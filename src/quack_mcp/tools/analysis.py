"""Analysis tools implementation."""

from typing import TYPE_CHECKING

from mcp.types import TextContent

from quack_mcp.exceptions import QueryError, TableNotFoundError
from quack_mcp.models import AnalyzeCSVArgs, DescribeTableArgs, QueryCSVArgs
from quack_mcp.utils import safe_json_dumps

if TYPE_CHECKING:
    from quack_mcp.server import QuackMCPServer


class AnalysisTools:
    """Handles data analysis operations."""

    def __init__(self, server: "QuackMCPServer") -> None:
        """Initialize analysis tools."""
        self.server = server

    async def query_csv(self, args: QueryCSVArgs) -> list[TextContent]:
        """Execute SQL query on loaded CSV data."""
        try:
            result = await self.server.execute_query(args.query)
            return [TextContent(type="text", text=safe_json_dumps(result))]
        except Exception as e:
            raise QueryError(str(e), args.query) from e

    async def describe_table(self, args: DescribeTableArgs) -> list[TextContent]:
        """Get schema information for a loaded table."""
        try:
            # Check if table exists
            loaded_tables = self.server.get_loaded_tables()
            if args.table_name not in loaded_tables:
                raise TableNotFoundError(args.table_name)

            # Get schema
            result = await self.server.execute_query(f"DESCRIBE {args.table_name}")

            return [
                TextContent(
                    type="text",
                    text=f'Schema for table "{args.table_name}":\n{safe_json_dumps(result)}',
                )
            ]
        except TableNotFoundError:
            raise
        except Exception as e:
            raise QueryError(f"Failed to describe table: {e!s}") from e

    async def list_tables(self) -> list[TextContent]:
        """List all loaded tables."""
        try:
            loaded_tables = self.server.get_loaded_tables()
            tables = [
                {"table_name": name, "file_path": path}
                for name, path in loaded_tables.items()
            ]

            return [
                TextContent(
                    type="text", text=f"Loaded tables:\n{safe_json_dumps(tables)}"
                )
            ]
        except Exception as e:
            raise QueryError(f"Failed to list tables: {e!s}") from e

    async def analyze_csv(self, args: AnalyzeCSVArgs) -> list[TextContent]:
        """Perform basic statistical analysis on CSV data."""
        try:
            # Check if table exists
            loaded_tables = self.server.get_loaded_tables()
            if args.table_name not in loaded_tables:
                raise TableNotFoundError(args.table_name)

            if args.columns and len(args.columns) > 0:
                # Analyze specific columns
                column_stats = []
                for col in args.columns:
                    stat_parts = [
                        f"COUNT({col}) as {col}_count",
                        f"COUNT(DISTINCT {col}) as {col}_unique",
                        f"MIN({col}) as {col}_min",
                        f"MAX({col}) as {col}_max",
                        f"AVG(TRY_CAST({col} AS DOUBLE)) as {col}_avg",
                    ]
                    column_stats.extend(stat_parts)

                query = f"SELECT {', '.join(column_stats)} FROM {args.table_name}"
            else:
                # General analysis
                query = f"""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT(*) - COUNT(*) as missing_values
                    FROM {args.table_name}
                """

            result = await self.server.execute_query(query)

            return [
                TextContent(
                    type="text",
                    text=f'Analysis for table "{args.table_name}":\n{safe_json_dumps(result)}',
                )
            ]

        except TableNotFoundError:
            raise
        except Exception as e:
            raise QueryError(f"Analysis failed: {e!s}") from e
