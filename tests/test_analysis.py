"""Tests for analysis tools."""

import json

import pytest

from quack_mcp.exceptions import QueryError, TableNotFoundError
from quack_mcp.models import (
    AnalyzeCSVArgs,
    DescribeTableArgs,
    LoadCSVArgs,
    QueryCSVArgs,
)
from quack_mcp.tools.analysis import AnalysisTools
from quack_mcp.tools.data_loading import DataLoadingTools


@pytest.mark.unit
class TestAnalysisTools:
    """Test analysis tools functionality."""

    @pytest.mark.asyncio
    async def test_query_csv_success(self, server, loaded_test_table):
        """Test successful SQL query execution."""
        tools = AnalysisTools(server)

        args = QueryCSVArgs(query=f"SELECT COUNT(*) as count FROM {loaded_test_table}")
        result = await tools.query_csv(args)

        assert len(result) == 1
        result_text = result[0].text
        assert "count" in result_text
        # Should contain valid JSON with the count
        data = json.loads(result_text)
        assert isinstance(data, list)
        assert len(data) == 1
        assert "count" in data[0]

    @pytest.mark.asyncio
    async def test_query_csv_syntax_error(self, server):
        """Test query execution with syntax error."""
        tools = AnalysisTools(server)

        args = QueryCSVArgs(query="INVALID SQL SYNTAX")

        with pytest.raises(QueryError) as exc_info:
            await tools.query_csv(args)

        assert "Query execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_describe_table_success(self, server, loaded_test_table):
        """Test successful table description."""
        tools = AnalysisTools(server)

        args = DescribeTableArgs(table_name=loaded_test_table)
        result = await tools.describe_table(args)

        assert len(result) == 1
        result_text = result[0].text
        assert f'Schema for table "{loaded_test_table}"' in result_text
        assert "column_name" in result_text
        assert "column_type" in result_text

    @pytest.mark.asyncio
    async def test_describe_table_not_found(self, server):
        """Test describing non-existent table."""
        tools = AnalysisTools(server)

        args = DescribeTableArgs(table_name="non_existent_table")

        with pytest.raises(TableNotFoundError) as exc_info:
            await tools.describe_table(args)

        assert "non_existent_table" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_tables_empty(self, server):
        """Test listing tables when no tables are loaded."""
        tools = AnalysisTools(server)

        result = await tools.list_tables()

        assert len(result) == 1
        result_text = result[0].text
        assert "Loaded tables:" in result_text
        # Should contain empty list
        data_start = result_text.find("[")
        data_json = result_text[data_start:]
        data = json.loads(data_json)
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_tables_with_data(self, server, loaded_test_table):
        """Test listing tables when tables are loaded."""
        tools = AnalysisTools(server)

        result = await tools.list_tables()

        assert len(result) == 1
        result_text = result[0].text
        assert "Loaded tables:" in result_text
        assert loaded_test_table in result_text

    @pytest.mark.asyncio
    async def test_analyze_csv_general(self, server, loaded_test_table):
        """Test general CSV analysis without specific columns."""
        tools = AnalysisTools(server)

        args = AnalyzeCSVArgs(table_name=loaded_test_table)
        result = await tools.analyze_csv(args)

        assert len(result) == 1
        result_text = result[0].text
        assert f'Analysis for table "{loaded_test_table}"' in result_text
        assert "total_rows" in result_text

    @pytest.mark.asyncio
    async def test_analyze_csv_specific_columns(self, server, loaded_test_table):
        """Test CSV analysis with specific columns."""
        tools = AnalysisTools(server)

        # First, find out what columns are available
        schema_result = await server.execute_query(f"DESCRIBE {loaded_test_table}")
        available_columns = [col["column_name"] for col in schema_result]

        # Use the first two columns for testing
        test_columns = available_columns[:2]

        args = AnalyzeCSVArgs(table_name=loaded_test_table, columns=test_columns)
        result = await tools.analyze_csv(args)

        assert len(result) == 1
        result_text = result[0].text
        assert f'Analysis for table "{loaded_test_table}"' in result_text

        # Should contain analysis for the specific columns
        for col in test_columns:
            assert f"{col}_count" in result_text

    @pytest.mark.asyncio
    async def test_analyze_csv_table_not_found(self, server):
        """Test analyzing non-existent table."""
        tools = AnalysisTools(server)

        args = AnalyzeCSVArgs(table_name="non_existent_table")

        with pytest.raises(TableNotFoundError) as exc_info:
            await tools.analyze_csv(args)

        assert "non_existent_table" in str(exc_info.value)


@pytest.mark.integration
class TestAnalysisIntegration:
    """Integration tests for analysis tools."""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, server, create_csv_file):
        """Test complete analysis workflow: load, describe, query, analyze."""

        # Step 1: Load CSV
        csv_file = create_csv_file("workflow_test", "employees")
        data_tools = DataLoadingTools(server)
        analysis_tools = AnalysisTools(server)

        load_args = LoadCSVArgs(file_path=str(csv_file))
        load_result = await data_tools.load_csv(load_args)
        assert "Successfully loaded" in load_result[0].text

        table_name = "workflow_test"

        # Step 2: Describe table
        describe_args = DescribeTableArgs(table_name=table_name)
        describe_result = await analysis_tools.describe_table(describe_args)
        assert f'Schema for table "{table_name}"' in describe_result[0].text

        # Step 3: Query data
        query_args = QueryCSVArgs(query=f"SELECT * FROM {table_name} LIMIT 3")
        query_result = await analysis_tools.query_csv(query_args)
        query_data = json.loads(query_result[0].text)
        assert len(query_data) <= 3

        # Step 4: Analyze data
        analyze_args = AnalyzeCSVArgs(table_name=table_name)
        analyze_result = await analysis_tools.analyze_csv(analyze_args)
        assert "total_rows" in analyze_result[0].text

    @pytest.mark.asyncio
    async def test_complex_query_operations(self, server, loaded_test_table):
        """Test complex SQL operations on loaded data."""
        tools = AnalysisTools(server)

        # Test aggregation query
        agg_args = QueryCSVArgs(
            query=f"SELECT COUNT(*) as total, AVG(age) as avg_age FROM {loaded_test_table}"
        )
        agg_result = await tools.query_csv(agg_args)

        agg_data = json.loads(agg_result[0].text)
        assert len(agg_data) == 1
        assert "total" in agg_data[0]
        assert "avg_age" in agg_data[0]

        # Test grouping query
        group_args = QueryCSVArgs(
            query=f"SELECT department, COUNT(*) as count FROM {loaded_test_table} GROUP BY department"
        )
        group_result = await tools.query_csv(group_args)

        group_data = json.loads(group_result[0].text)
        assert len(group_data) >= 1
        for row in group_data:
            assert "department" in row
            assert "count" in row

    @pytest.mark.asyncio
    async def test_analyze_numeric_columns(self, server):
        """Test analysis of tables with numeric data."""
        # Create a table with numeric data for testing
        await server.execute_query("""
            CREATE TABLE numeric_test AS
            SELECT
                generate_series as id,
                random() * 1000 as value,
                (random() * 50 + 18)::int as age
            FROM generate_series(1, 100)
        """)

        server.add_loaded_table("numeric_test", "generated_data")

        tools = AnalysisTools(server)

        args = AnalyzeCSVArgs(table_name="numeric_test", columns=["value", "age"])
        result = await tools.analyze_csv(args)

        assert len(result) == 1
        result_text = result[0].text

        # Should contain statistical analysis for numeric columns
        assert "value_count" in result_text
        assert "age_count" in result_text
        assert "value_min" in result_text
        assert "value_max" in result_text
