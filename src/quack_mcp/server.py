"""Main MCP server implementation for Quack MCP."""

import asyncio
from typing import Any

import duckdb
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)
from pydantic import ValidationError

from .exceptions import QuackMCPError, QueryError
from .models import (
    AnalyzeCSVArgs,
    DescribeTableArgs,
    DetectAnomaliesArgs,
    DiscoverCSVFilesArgs,
    DiscoverExcelFilesArgs,
    LoadCSVArgs,
    LoadExcelArgs,
    LoadMultipleCSVsArgs,
    LoadMultipleExcelsArgs,
    OptimizeExpensesArgs,
    QueryCSVArgs,
)
from .tools.analysis import AnalysisTools
from .tools.data_loading import DataLoadingTools
from .tools.specialized import SpecializedTools
from .utils import format_sample_data, get_column_type_icon


class QuackMCPServer:
    """Main MCP server for CSV and Excel analysis using DuckDB."""

    def __init__(self) -> None:
        """Initialize the QuackMCP server."""
        self.server = Server("quack-mcp")
        self.db: duckdb.DuckDBPyConnection | None = None
        self.loaded_tables: dict[str, str] = {}

        # Initialize tool handlers
        self.data_tools = DataLoadingTools(self)
        self.analysis_tools = AnalysisTools(self)
        self.specialized_tools = SpecializedTools(self)

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="load_csv",
                    description="Load a CSV file into DuckDB for analysis",
                    inputSchema=LoadCSVArgs.model_json_schema(),
                ),
                Tool(
                    name="load_multiple_csvs",
                    description="Load multiple CSV files using glob patterns or file lists into DuckDB for analysis",
                    inputSchema=LoadMultipleCSVsArgs.model_json_schema(),
                ),
                Tool(
                    name="load_excel",
                    description="Load an Excel (.xlsx) file into DuckDB for analysis",
                    inputSchema=LoadExcelArgs.model_json_schema(),
                ),
                Tool(
                    name="load_multiple_excels",
                    description="Load multiple Excel files using glob patterns or file lists into DuckDB for analysis",
                    inputSchema=LoadMultipleExcelsArgs.model_json_schema(),
                ),
                Tool(
                    name="query_csv",
                    description="Execute SQL query on loaded CSV data",
                    inputSchema=QueryCSVArgs.model_json_schema(),
                ),
                Tool(
                    name="describe_table",
                    description="Get schema information for a loaded table",
                    inputSchema=DescribeTableArgs.model_json_schema(),
                ),
                Tool(
                    name="list_tables",
                    description="List all loaded tables",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="analyze_csv",
                    description="Perform basic statistical analysis on CSV data",
                    inputSchema=AnalyzeCSVArgs.model_json_schema(),
                ),
                Tool(
                    name="discover_csv_files",
                    description="Discover CSV files matching a glob pattern",
                    inputSchema=DiscoverCSVFilesArgs.model_json_schema(),
                ),
                Tool(
                    name="discover_excel_files",
                    description="Discover Excel files matching a glob pattern",
                    inputSchema=DiscoverExcelFilesArgs.model_json_schema(),
                ),
                Tool(
                    name="optimize_expenses",
                    description="Analyze credit card spending data to identify expense optimization opportunities with actionable recommendations and savings estimates",
                    inputSchema=OptimizeExpensesArgs.model_json_schema(),
                ),
                Tool(
                    name="detect_anomalies",
                    description="Detect anomalies and irregularities in dataset using statistical analysis and business logic rules",
                    inputSchema=DetectAnomaliesArgs.model_json_schema(),
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                return await self._dispatch_tool(name, arguments)
            except ValidationError as e:
                raise QuackMCPError(f"Invalid arguments for {name}: {e}") from e
            except Exception as e:
                if isinstance(e, QuackMCPError):
                    raise
                raise QuackMCPError(f"Tool {name} failed: {e!s}") from e

    async def _dispatch_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Dispatch tool call to appropriate handler."""
        # Route to appropriate tool handler
        if name == "load_csv":
            args = LoadCSVArgs.model_validate(arguments)
            return await self.data_tools.load_csv(args)
        elif name == "load_multiple_csvs":
            args = LoadMultipleCSVsArgs.model_validate(arguments)
            return await self.data_tools.load_multiple_csvs(args)
        elif name == "load_excel":
            args = LoadExcelArgs.model_validate(arguments)
            return await self.data_tools.load_excel(args)
        elif name == "load_multiple_excels":
            args = LoadMultipleExcelsArgs.model_validate(arguments)
            return await self.data_tools.load_multiple_excels(args)
        elif name == "query_csv":
            args = QueryCSVArgs.model_validate(arguments)
            return await self.analysis_tools.query_csv(args)
        elif name == "describe_table":
            args = DescribeTableArgs.model_validate(arguments)
            return await self.analysis_tools.describe_table(args)
        elif name == "list_tables":
            return await self.analysis_tools.list_tables()
        elif name == "analyze_csv":
            args = AnalyzeCSVArgs.model_validate(arguments)
            return await self.analysis_tools.analyze_csv(args)
        elif name == "discover_csv_files":
            args = DiscoverCSVFilesArgs.model_validate(arguments)
            return await self.data_tools.discover_csv_files(args)
        elif name == "discover_excel_files":
            args = DiscoverExcelFilesArgs.model_validate(arguments)
            return await self.data_tools.discover_excel_files(args)
        elif name == "optimize_expenses":
            args = OptimizeExpensesArgs.model_validate(arguments)
            return await self.specialized_tools.optimize_expenses(args)
        elif name == "detect_anomalies":
            args = DetectAnomaliesArgs.model_validate(arguments)
            return await self.specialized_tools.detect_anomalies(args)
        else:
            raise QuackMCPError(f"Unknown tool: {name}")

    def get_db_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self.db is None:
            self.db = duckdb.connect(":memory:")
            # Install and load required extensions
            try:
                self.db.execute("INSTALL excel")
                self.db.execute("LOAD excel")
            except Exception:
                # Extensions might already be loaded or unavailable
                pass
        return self.db

    async def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute SQL query and return results."""
        try:
            conn = self.get_db_connection()
            result = conn.execute(query).fetchall()
            columns = [desc[0] for desc in conn.description] if conn.description else []

            # Convert to list of dictionaries
            return [dict(zip(columns, row, strict=False)) for row in result]

        except Exception as e:
            raise QueryError(f"Query execution failed: {e!s}", query) from e

    async def inspect_table_schema(self, table_name: str) -> str:
        """Inspect table schema and return formatted information."""
        try:
            # Get schema information
            schema = await self.execute_query(f"DESCRIBE {table_name}")

            # Get row count
            count_result = await self.execute_query(
                f"SELECT COUNT(*) as row_count FROM {table_name}"
            )
            row_count = count_result[0]["row_count"] if count_result else 0

            # Get sample data (first 3 rows)
            sample_data = await self.execute_query(
                f"SELECT * FROM {table_name} LIMIT 3"
            )

            # Format the inspection result

            inspection = f'📊 TABLE INSPECTION: "{table_name}"\n'
            inspection += "━" * 50 + "\n"
            inspection += f"📈 Total Rows: {row_count:,}\n\n"

            inspection += "🏗️ SCHEMA:\n"
            for i, col in enumerate(schema, 1):
                icon = get_column_type_icon(col["column_type"])
                nullable = " - nullable" if col.get("null", "YES") == "YES" else ""
                inspection += f"  {i}. {icon} {col['column_name']} ({col['column_type']}){nullable}\n"

            if sample_data:
                inspection += f"\n👀 SAMPLE DATA (first {len(sample_data)} rows):\n"
                inspection += format_sample_data(sample_data, schema)

            inspection += (
                "\n💡 Ready for analysis! Use query_csv to explore the data with SQL."
            )

        except Exception as e:
            return f"Schema inspection failed: {e!s}"
        else:
            return inspection

    def add_loaded_table(self, table_name: str, source_path: str) -> None:
        """Add table to loaded tables registry."""
        self.loaded_tables[table_name] = source_path

    def get_loaded_tables(self) -> dict[str, str]:
        """Get dictionary of loaded tables."""
        return self.loaded_tables.copy()

    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


def main() -> None:
    """Main entry point."""
    server = QuackMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
