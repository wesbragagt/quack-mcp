"""Data loading tools implementation."""

from pathlib import Path
from typing import TYPE_CHECKING

from mcp.types import TextContent

from ..exceptions import CSVLoadError, ExcelLoadError, FileDiscoveryError
from ..models import (
    DiscoverCSVFilesArgs,
    DiscoverExcelFilesArgs,
    LoadCSVArgs,
    LoadExcelArgs,
    LoadMultipleCSVsArgs,
    LoadMultipleExcelsArgs,
)
from ..utils import escape_sql_string, is_glob_pattern, sanitize_table_name

if TYPE_CHECKING:
    from ..server import QuackMCPServer


class DataLoadingTools:
    """Handles data loading operations for CSV and Excel files."""

    def __init__(self, server: "QuackMCPServer") -> None:
        """Initialize data loading tools."""
        self.server = server

    async def load_csv(self, args: LoadCSVArgs) -> list[TextContent]:
        """Load a CSV file into DuckDB."""
        try:
            file_path = Path(args.file_path)

            # Handle glob patterns
            if is_glob_pattern(args.file_path):
                return await self._load_csv_glob(args)

            # Single file loading
            if not file_path.exists():
                raise CSVLoadError(f"File not found: {args.file_path}")

            # Generate table name
            table_name = args.table_name or sanitize_table_name(file_path.stem)

            # Build query
            escaped_path = escape_sql_string(str(file_path))
            query_parts = [
                f'CREATE OR REPLACE TABLE "{table_name}" AS',
                f"SELECT * FROM read_csv('{escaped_path}',",
                f"  header={str(args.header).lower()},",
            ]

            if args.delimiter != ",":
                query_parts.append(f"  delim='{args.delimiter}',")

            # Remove trailing comma and close
            query_parts[-1] = query_parts[-1].rstrip(",")
            query_parts.append(")")

            query = "\n".join(query_parts)

            # Execute query
            await self.server.execute_query(query)

            # Verify data was loaded
            count_result = await self.server.execute_query(
                f'SELECT COUNT(*) as row_count FROM "{table_name}"'
            )
            row_count = count_result[0]["row_count"] if count_result else 0

            if row_count == 0:
                await self.server.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
                raise CSVLoadError("CSV file is empty or contains no valid data")

            # Register table
            self.server.add_loaded_table(table_name, str(file_path))

            # Get schema information
            schema_info = await self.server.inspect_table_schema(table_name)

            return [
                TextContent(
                    type="text",
                    text=f'Successfully loaded CSV file "{args.file_path}" as table "{table_name}"\n\n{schema_info}'
                )
            ]

        except Exception as e:
            if isinstance(e, CSVLoadError):
                raise
            raise CSVLoadError(str(e), args.file_path)

    async def _load_csv_glob(self, args: LoadCSVArgs) -> list[TextContent]:
        """Load CSV files using glob pattern."""
        try:
            # Discover files using glob pattern
            glob_result = await self.server.execute_query(
                f"SELECT file FROM glob('{escape_sql_string(args.file_path)}')"
            )
            discovered_files = [row["file"] for row in glob_result]

            if not discovered_files:
                raise CSVLoadError(f"No CSV files found matching pattern: {args.file_path}")

            # Generate table name
            table_name = args.table_name or sanitize_table_name(f"csv_{args.file_path}")

            # Build query for multiple files
            escaped_path = escape_sql_string(args.file_path)
            query_parts = [
                f'CREATE OR REPLACE TABLE "{table_name}" AS',
                f"SELECT * FROM read_csv('{escaped_path}',",
                f"  header={str(args.header).lower()},",
            ]

            if args.delimiter != ",":
                query_parts.append(f"  delim='{args.delimiter}',")

            # Remove trailing comma and close
            query_parts[-1] = query_parts[-1].rstrip(",")
            query_parts.append(")")

            query = "\n".join(query_parts)

            # Execute query
            await self.server.execute_query(query)

            # Verify data was loaded
            count_result = await self.server.execute_query(
                f'SELECT COUNT(*) as row_count FROM "{table_name}"'
            )
            row_count = count_result[0]["row_count"] if count_result else 0

            if row_count == 0:
                await self.server.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
                raise CSVLoadError("No data was loaded from the CSV files")

            # Register table
            self.server.add_loaded_table(table_name, args.file_path)

            # Get schema information
            schema_info = await self.server.inspect_table_schema(table_name)

            file_list = ", ".join(discovered_files[:5])
            if len(discovered_files) > 5:
                file_list += "..."

            return [
                TextContent(
                    type="text",
                    text=f'Successfully loaded {len(discovered_files)} CSV files matching "{args.file_path}" as table "{table_name}"\n\nFiles: {file_list}\n\n{schema_info}'
                )
            ]

        except Exception as e:
            if isinstance(e, CSVLoadError):
                raise
            raise CSVLoadError(str(e), args.file_path)

    async def load_multiple_csvs(self, args: LoadMultipleCSVsArgs) -> list[TextContent]:
        """Load multiple CSV files."""
        try:
            table_name = sanitize_table_name(args.table_name)
            discovered_files: list[str] = []

            if isinstance(args.pattern_or_files, str):
                # Handle glob pattern
                if is_glob_pattern(args.pattern_or_files):
                    glob_result = await self.server.execute_query(
                        f"SELECT file FROM glob('{escape_sql_string(args.pattern_or_files)}')"
                    )
                    discovered_files = [row["file"] for row in glob_result]

                    if not discovered_files:
                        raise CSVLoadError(f"No CSV files found matching pattern: {args.pattern_or_files}")
                else:
                    # Single file path
                    if not Path(args.pattern_or_files).exists():
                        raise CSVLoadError(f"File not found: {args.pattern_or_files}")
                    discovered_files = [args.pattern_or_files]
            else:
                # List of files
                discovered_files = args.pattern_or_files
                for file_path in discovered_files:
                    if not Path(file_path).exists():
                        raise CSVLoadError(f"File not found: {file_path}")

            # Build query
            if isinstance(args.pattern_or_files, str) and is_glob_pattern(args.pattern_or_files):
                # Use glob pattern directly
                escaped_pattern = escape_sql_string(args.pattern_or_files)
                read_csv_args = [
                    f"'{escaped_pattern}'",
                    f"header={str(args.header).lower()}",
                    f"delim='{args.delimiter}'",
                    f"union_by_name={str(args.union_by_name).lower()}",
                    f"filename={str(args.include_filename).lower()}",
                ]
            else:
                # Use file list
                file_list = ", ".join(f"'{escape_sql_string(f)}'" for f in discovered_files)
                read_csv_args = [
                    f"[{file_list}]",
                    f"header={str(args.header).lower()}",
                    f"delim='{args.delimiter}'",
                    f"union_by_name={str(args.union_by_name).lower()}",
                    f"filename={str(args.include_filename).lower()}",
                ]

            query = f"""
                CREATE OR REPLACE TABLE "{table_name}" AS 
                SELECT * FROM read_csv({', '.join(read_csv_args)})
            """

            # Execute query
            await self.server.execute_query(query)

            # Verify data was loaded
            count_result = await self.server.execute_query(
                f'SELECT COUNT(*) as row_count FROM "{table_name}"'
            )
            row_count = count_result[0]["row_count"] if count_result else 0

            if row_count == 0:
                await self.server.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
                raise CSVLoadError("No data was loaded from the CSV files")

            # Register table
            source_description = (
                args.pattern_or_files
                if isinstance(args.pattern_or_files, str)
                else ", ".join(args.pattern_or_files)
            )
            self.server.add_loaded_table(table_name, source_description)

            # Get schema information
            schema_info = await self.server.inspect_table_schema(table_name)

            file_count = len(discovered_files) if discovered_files else "multiple"
            files_text = (
                ", ".join(discovered_files[:10]) + ("..." if len(discovered_files) > 10 else "")
                if discovered_files
                else "matched by pattern"
            )

            return [
                TextContent(
                    type="text",
                    text=f'Successfully loaded {file_count} files as table "{table_name}"\n\nFiles processed: {files_text}\n\n{schema_info}'
                )
            ]

        except Exception as e:
            if isinstance(e, CSVLoadError):
                raise
            raise CSVLoadError(f"Multi-CSV loading failed: {e!s}")

    async def load_excel(self, args: LoadExcelArgs) -> list[TextContent]:
        """Load an Excel file into DuckDB."""
        try:
            file_path = Path(args.file_path)

            if not file_path.exists():
                raise ExcelLoadError(f"File not found: {args.file_path}")

            # Ensure Excel extension is loaded
            await self._ensure_excel_extension()

            # Generate table name
            table_name = args.table_name or sanitize_table_name(file_path.stem)

            # Build query parameters
            escaped_path = escape_sql_string(str(file_path))
            query_params = [f"'{escaped_path}'"]

            # Add optional parameters
            options = []
            if args.sheet:
                options.append(f"sheet='{escape_sql_string(args.sheet)}'")
            if args.range:
                options.append(f"range='{escape_sql_string(args.range)}'")
            options.append(f"header={str(args.header).lower()}")
            if args.all_varchar:
                options.append(f"all_varchar={str(args.all_varchar).lower()}")

            if options:
                query_params.append(", ".join(options))

            query = f"""
                CREATE OR REPLACE TABLE "{table_name}" AS 
                SELECT * FROM read_xlsx({', '.join(query_params)})
            """

            # Execute query
            await self.server.execute_query(query)

            # Verify data was loaded
            count_result = await self.server.execute_query(
                f'SELECT COUNT(*) as row_count FROM "{table_name}"'
            )
            row_count = count_result[0]["row_count"] if count_result else 0

            if row_count == 0:
                await self.server.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
                raise ExcelLoadError("Excel file is empty or contains no valid data in the specified sheet/range")

            # Register table
            self.server.add_loaded_table(table_name, str(file_path))

            # Get schema information
            schema_info = await self.server.inspect_table_schema(table_name)

            sheet_info = f" (sheet: {args.sheet})" if args.sheet else ""
            range_info = f" (range: {args.range})" if args.range else ""

            return [
                TextContent(
                    type="text",
                    text=f'Successfully loaded Excel file "{args.file_path}"{sheet_info}{range_info} as table "{table_name}"\n\n{schema_info}'
                )
            ]

        except Exception as e:
            if isinstance(e, ExcelLoadError):
                raise
            raise ExcelLoadError(str(e), args.file_path)

    async def load_multiple_excels(self, args: LoadMultipleExcelsArgs) -> list[TextContent]:
        """Load multiple Excel files."""
        try:
            table_name = sanitize_table_name(args.table_name)
            discovered_files: list[str] = []

            if isinstance(args.pattern_or_files, str):
                # Handle glob pattern
                if is_glob_pattern(args.pattern_or_files):
                    glob_result = await self.server.execute_query(
                        f"SELECT file FROM glob('{escape_sql_string(args.pattern_or_files)}')"
                    )
                    discovered_files = [row["file"] for row in glob_result]

                    if not discovered_files:
                        raise ExcelLoadError(f"No Excel files found matching pattern: {args.pattern_or_files}")
                else:
                    # Single file path
                    if not Path(args.pattern_or_files).exists():
                        raise ExcelLoadError(f"File not found: {args.pattern_or_files}")
                    discovered_files = [args.pattern_or_files]
            else:
                # List of files
                discovered_files = args.pattern_or_files
                for file_path in discovered_files:
                    if not Path(file_path).exists():
                        raise ExcelLoadError(f"File not found: {file_path}")

            # Validate Excel files
            non_xlsx_files = [f for f in discovered_files if not f.lower().endswith(".xlsx")]
            if non_xlsx_files:
                raise ExcelLoadError(f"Found non-xlsx files: {', '.join(non_xlsx_files)}. Only .xlsx files are supported.")

            # Ensure Excel extension is loaded
            await self._ensure_excel_extension()

            # Build query
            if isinstance(args.pattern_or_files, str) and is_glob_pattern(args.pattern_or_files):
                # Use glob pattern directly
                escaped_pattern = escape_sql_string(args.pattern_or_files)
                read_excel_source = f"'{escaped_pattern}'"
            else:
                # Use file list
                file_list = ", ".join(f"'{escape_sql_string(f)}'" for f in discovered_files)
                read_excel_source = f"[{file_list}]"

            # Build options
            options = []
            if args.sheet:
                options.append(f"sheet='{escape_sql_string(args.sheet)}'")
            options.extend([
                f"header={str(args.header).lower()}",
                f"union_by_name={str(args.union_by_name).lower()}",
                f"filename={str(args.include_filename).lower()}",
            ])
            if args.all_varchar:
                options.append(f"all_varchar={str(args.all_varchar).lower()}")

            query = f"""
                CREATE OR REPLACE TABLE "{table_name}" AS 
                SELECT * FROM read_xlsx({read_excel_source}, {', '.join(options)})
            """

            # Execute query
            await self.server.execute_query(query)

            # Verify data was loaded
            count_result = await self.server.execute_query(
                f'SELECT COUNT(*) as row_count FROM "{table_name}"'
            )
            row_count = count_result[0]["row_count"] if count_result else 0

            if row_count == 0:
                await self.server.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
                raise ExcelLoadError("No data was loaded from the Excel files")

            # Register table
            source_description = (
                args.pattern_or_files
                if isinstance(args.pattern_or_files, str)
                else ", ".join(args.pattern_or_files)
            )
            self.server.add_loaded_table(table_name, source_description)

            # Get schema information
            schema_info = await self.server.inspect_table_schema(table_name)

            file_count = len(discovered_files) if discovered_files else "multiple"
            files_text = (
                ", ".join(discovered_files[:10]) + ("..." if len(discovered_files) > 10 else "")
                if discovered_files
                else "matched by pattern"
            )
            sheet_info = f" (sheet: {args.sheet})" if args.sheet else ""

            return [
                TextContent(
                    type="text",
                    text=f'Successfully loaded {file_count} Excel files{sheet_info} as table "{table_name}"\n\nFiles processed: {files_text}\n\n{schema_info}'
                )
            ]

        except Exception as e:
            if isinstance(e, ExcelLoadError):
                raise
            raise ExcelLoadError(f"Multi-Excel loading failed: {e!s}")

    async def discover_csv_files(self, args: DiscoverCSVFilesArgs) -> list[TextContent]:
        """Discover CSV files matching a glob pattern."""
        try:
            # Use DuckDB's glob function
            result = await self.server.execute_query(
                f"SELECT file FROM glob('{escape_sql_string(args.pattern)}') ORDER BY file"
            )

            files = [row["file"] for row in result]

            # Get file info
            file_info = []
            total_size = 0
            existing_count = 0

            for file_path in files:
                try:
                    path = Path(file_path)
                    stats = path.stat()
                    file_info.append({
                        "path": file_path,
                        "size": stats.st_size,
                        "modified": stats.st_mtime,
                        "exists": True,
                    })
                    total_size += stats.st_size
                    existing_count += 1
                except Exception:
                    file_info.append({
                        "path": file_path,
                        "size": 0,
                        "modified": None,
                        "exists": False,
                        "error": "File not accessible",
                    })

            # Format response
            response = f'Found {len(files)} files matching pattern "{args.pattern}"\n\n'
            response += f"Existing files: {existing_count}\n"
            response += f"Total size: {total_size / 1024 / 1024:.2f} MB\n\n"
            response += "File Details:\n"

            for info in file_info:
                if info["exists"]:
                    size_kb = info["size"] / 1024
                    import datetime
                    modified_time = datetime.datetime.fromtimestamp(info["modified"]).isoformat()
                    response += f"- {info['path']} ({size_kb:.1f} KB, modified: {modified_time})\n"
                else:
                    response += f"- {info['path']} (NOT FOUND)\n"

            return [TextContent(type="text", text=response)]

        except Exception as e:
            raise FileDiscoveryError(str(e), args.pattern)

    async def discover_excel_files(self, args: DiscoverExcelFilesArgs) -> list[TextContent]:
        """Discover Excel files matching a glob pattern."""
        try:
            # Use DuckDB's glob function
            result = await self.server.execute_query(
                f"SELECT file FROM glob('{escape_sql_string(args.pattern)}') ORDER BY file"
            )

            files = [row["file"] for row in result]

            # Filter Excel files
            excel_files = [f for f in files if f.lower().endswith(".xlsx")]
            non_excel_files = [f for f in files if not f.lower().endswith(".xlsx")]

            # Get file info for Excel files
            file_info = []
            total_size = 0
            existing_count = 0

            for file_path in excel_files:
                try:
                    path = Path(file_path)
                    stats = path.stat()
                    file_info.append({
                        "path": file_path,
                        "size": stats.st_size,
                        "modified": stats.st_mtime,
                        "exists": True,
                    })
                    total_size += stats.st_size
                    existing_count += 1
                except Exception:
                    file_info.append({
                        "path": file_path,
                        "size": 0,
                        "modified": None,
                        "exists": False,
                        "error": "File not accessible",
                    })

            # Format response
            response = f'Found {len(files)} files matching pattern "{args.pattern}"\n\n'
            response += f"Excel files (.xlsx): {len(excel_files)}\n"
            response += f"Other files: {len(non_excel_files)}\n"

            if excel_files:
                response += f"Existing Excel files: {existing_count}\n"
                response += f"Total Excel file size: {total_size / 1024 / 1024:.2f} MB\n\n"

            if non_excel_files:
                response += "\n⚠️  Non-Excel files found (will be ignored by Excel tools):\n"
                for file in non_excel_files[:5]:
                    response += f"- {file}\n"
                if len(non_excel_files) > 5:
                    response += f"... and {len(non_excel_files) - 5} more\n"

            if excel_files:
                response += "\n📊 Excel File Details:\n"
                for info in file_info:
                    if info["exists"]:
                        size_kb = info["size"] / 1024
                        import datetime
                        modified_time = datetime.datetime.fromtimestamp(info["modified"]).isoformat()
                        response += f"- {info['path']} ({size_kb:.1f} KB, modified: {modified_time})\n"
                    else:
                        response += f"- {info['path']} (NOT FOUND)\n"
            else:
                response += "\nNo Excel (.xlsx) files found matching the pattern."

            return [TextContent(type="text", text=response)]

        except Exception as e:
            raise FileDiscoveryError(str(e), args.pattern)

    async def _ensure_excel_extension(self) -> None:
        """Ensure Excel extension is loaded."""
        try:
            conn = self.server.get_db_connection()
            conn.execute("INSTALL excel")
            conn.execute("LOAD excel")
        except Exception:
            # Extensions might already be loaded
            pass
