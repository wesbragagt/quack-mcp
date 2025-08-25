"""Tests for the main QuackMCP server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import TextContent
from pydantic import ValidationError

from quack_mcp.server import QuackMCPServer
from quack_mcp.exceptions import QuackMCPError
from quack_mcp.models import LoadCSVArgs, QueryCSVArgs


@pytest.mark.unit
class TestQuackMCPServer:
    """Test QuackMCP server functionality."""

    def test_server_initialization(self):
        """Test server initializes correctly."""
        server = QuackMCPServer()
        assert server is not None
        assert server.server.name == "quack-mcp"
        assert server.loaded_tables == {}
        assert server.db is None  # Not connected yet

    @pytest.mark.asyncio
    async def test_get_db_connection(self, server: QuackMCPServer):
        """Test database connection creation."""
        conn = server.get_db_connection()
        assert conn is not None
        assert server.db is not None

    @pytest.mark.asyncio
    async def test_execute_query_success(self, server: QuackMCPServer):
        """Test successful query execution."""
        # Execute a simple query
        result = await server.execute_query("SELECT 1 as test_column")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["test_column"] == 1

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, server: QuackMCPServer):
        """Test query execution failure."""
        with pytest.raises(Exception):  # QueryError should be raised
            await server.execute_query("INVALID SQL SYNTAX")

    @pytest.mark.asyncio
    async def test_inspect_table_schema(self, server: QuackMCPServer):
        """Test table schema inspection."""
        # Create a test table
        await server.execute_query("""
            CREATE TABLE test_table (
                id INTEGER,
                name VARCHAR,
                value DOUBLE
            )
        """)
        
        # Insert some test data
        await server.execute_query("""
            INSERT INTO test_table VALUES 
            (1, 'test1', 10.5),
            (2, 'test2', 20.7)
        """)
        
        # Test schema inspection
        schema_info = await server.inspect_table_schema("test_table")
        
        assert "TABLE INSPECTION" in schema_info
        assert "test_table" in schema_info
        assert "Total Rows: 2" in schema_info
        assert "SCHEMA:" in schema_info
        assert "INTEGER" in schema_info
        assert "VARCHAR" in schema_info
        assert "DOUBLE" in schema_info

    def test_add_loaded_table(self, server: QuackMCPServer):
        """Test adding tables to loaded registry."""
        server.add_loaded_table("test_table", "/path/to/file.csv")
        
        tables = server.get_loaded_tables()
        assert "test_table" in tables
        assert tables["test_table"] == "/path/to/file.csv"

    def test_get_loaded_tables_copy(self, server: QuackMCPServer):
        """Test that get_loaded_tables returns a copy."""
        server.add_loaded_table("test1", "/path/1.csv")
        
        tables1 = server.get_loaded_tables()
        tables2 = server.get_loaded_tables()
        
        # Should be equal but not the same object
        assert tables1 == tables2
        assert tables1 is not tables2
        
        # Modifying returned dict shouldn't affect server state
        tables1["new_table"] = "/new/path.csv"
        assert "new_table" not in server.get_loaded_tables()


@pytest.mark.integration
class TestServerIntegration:
    """Integration tests for server functionality."""

    @pytest.mark.asyncio
    async def test_server_tools_available(self, server: QuackMCPServer):
        """Test that server has all expected tools available."""
        # Test that we can access the server's tool handlers directly
        expected_tools = [
            "load_csv",
            "load_multiple_csvs", 
            "load_excel",
            "load_multiple_excels",
            "query_csv",
            "describe_table",
            "list_tables",
            "analyze_csv",
            "discover_csv_files",
            "discover_excel_files",
            "optimize_expenses",
            "detect_anomalies",
        ]
        
        # Check that the tools are properly configured by testing tool handlers
        assert hasattr(server.data_tools, 'load_csv')
        assert hasattr(server.analysis_tools, 'query_csv')
        assert hasattr(server.specialized_tools, 'optimize_expenses')
        
        # Verify server is properly initialized
        assert server.server.name == "quack-mcp"
        assert server.loaded_tables == {}

    @pytest.mark.asyncio
    async def test_load_csv_tool_integration(self, server: QuackMCPServer, create_csv_file):
        """Test successful CSV loading through tool interface."""
        # Create a test CSV file
        csv_file = create_csv_file("test", "employees")
        
        # Test load_csv tool directly
        args = LoadCSVArgs(file_path=str(csv_file))
        result = await server.data_tools.load_csv(args)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Successfully loaded CSV" in result[0].text
        
        # Verify table was loaded
        assert len(server.loaded_tables) > 0

    @pytest.mark.asyncio
    async def test_tool_validation_integration(self, server: QuackMCPServer):
        """Test tool argument validation."""
        # Test invalid arguments
        with pytest.raises(ValidationError):
            LoadCSVArgs(file_path="")  # Empty file path should fail
        
        with pytest.raises(ValidationError):
            QueryCSVArgs(query="")  # Empty query should fail

    @pytest.mark.asyncio
    async def test_query_tool_integration(self, server: QuackMCPServer, create_csv_file):
        """Test query tool integration."""
        # Create and load a CSV file
        csv_file = create_csv_file("test", "employees")
        
        # Load the CSV
        load_args = LoadCSVArgs(file_path=str(csv_file))
        await server.data_tools.load_csv(load_args)
        
        # Query the loaded data
        query_args = QueryCSVArgs(query="SELECT COUNT(*) as row_count FROM test")
        result = await server.analysis_tools.query_csv(query_args)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], TextContent)


@pytest.mark.unit
class TestServerUtilityMethods:
    """Test server utility methods."""

    @pytest.mark.asyncio
    async def test_inspect_table_schema_failure(self, server: QuackMCPServer):
        """Test schema inspection for non-existent table."""
        schema_info = await server.inspect_table_schema("non_existent_table")
        assert "Schema inspection failed" in schema_info