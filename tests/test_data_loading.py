"""Tests for data loading tools."""

from pathlib import Path

import pytest

from quack_mcp.exceptions import CSVLoadError
from quack_mcp.models import (
    DiscoverCSVFilesArgs,
    LoadCSVArgs,
    LoadMultipleCSVsArgs,
)
from quack_mcp.tools.data_loading import DataLoadingTools


@pytest.mark.unit
class TestDataLoadingTools:
    """Test data loading tools functionality."""

    @pytest.mark.asyncio
    async def test_load_csv_success(self, server, create_csv_file):
        """Test successful CSV loading."""
        csv_file = create_csv_file("test_employees", "employees")
        tools = DataLoadingTools(server)

        args = LoadCSVArgs(file_path=str(csv_file))
        result = await tools.load_csv(args)

        assert len(result) == 1
        assert "Successfully loaded CSV" in result[0].text
        assert "test_employees" in result[0].text
        assert "test_employees" in server.get_loaded_tables()

    @pytest.mark.asyncio
    async def test_load_csv_file_not_found(self, server):
        """Test CSV loading with non-existent file."""
        tools = DataLoadingTools(server)

        args = LoadCSVArgs(file_path="/non/existent/file.csv")

        with pytest.raises(CSVLoadError) as exc_info:
            await tools.load_csv(args)

        assert "File not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_csv_empty_file(self, server, create_csv_file):
        """Test CSV loading with empty file."""
        csv_file = create_csv_file("empty_test", "empty")
        tools = DataLoadingTools(server)

        args = LoadCSVArgs(file_path=str(csv_file))

        with pytest.raises(CSVLoadError) as exc_info:
            await tools.load_csv(args)

        assert "empty or contains no valid data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_csv_with_custom_parameters(self, server, temp_dir):
        """Test CSV loading with custom delimiter and table name."""
        # Create a CSV with semicolon delimiter
        csv_content = "name;age;department\nJohn;30;Engineering\nJane;25;Marketing"
        csv_file = temp_dir / "semicolon.csv"
        csv_file.write_text(csv_content)

        tools = DataLoadingTools(server)

        args = LoadCSVArgs(
            file_path=str(csv_file),
            table_name="custom_table",
            delimiter=";",
            header=True,
        )
        result = await tools.load_csv(args)

        assert len(result) == 1
        assert "custom_table" in result[0].text
        assert "custom_table" in server.get_loaded_tables()

    @pytest.mark.asyncio
    async def test_load_csv_glob_pattern(self, server, create_csv_file):
        """Test CSV loading with glob pattern."""
        tools = DataLoadingTools(server)

        # Create multiple files with same schema for glob pattern testing
        create_csv_file("employees1", "employees")
        create_csv_file("employees2", "employees")
        create_csv_file("employees3", "employees")

        # Use glob pattern to load multiple files
        pattern = str(create_csv_file("dummy", "employees").parent / "employees*.csv")
        args = LoadCSVArgs(file_path=pattern)

        result = await tools.load_csv(args)

        assert len(result) == 1
        assert "Successfully loaded" in result[0].text
        assert "files" in result[0].text

    @pytest.mark.asyncio
    async def test_load_multiple_csvs_with_file_list(
        self, server, create_multiple_csv_files
    ):
        """Test loading multiple CSVs with explicit file list and different schemas."""
        tools = DataLoadingTools(server)

        file_list = [str(path) for path in list(create_multiple_csv_files.values())[:3]]

        args = LoadMultipleCSVsArgs(
            pattern_or_files=file_list,
            table_name="multi_table",
            union_by_name=True,  # Required for different schemas
            include_filename=True,
        )
        result = await tools.load_multiple_csvs(args)

        assert len(result) == 1
        assert "multi_table" in result[0].text
        assert "multi_table" in server.get_loaded_tables()

    @pytest.mark.asyncio
    async def test_load_multiple_csvs_with_pattern(
        self, server, create_multiple_csv_files
    ):
        """Test loading multiple CSVs with glob pattern."""
        tools = DataLoadingTools(server)

        pattern = str(
            Path(next(iter(create_multiple_csv_files.values()))).parent / "*.csv"
        )

        args = LoadMultipleCSVsArgs(
            pattern_or_files=pattern, union_by_name=True, include_filename=True
        )
        result = await tools.load_multiple_csvs(args)

        assert len(result) == 1
        assert "Successfully loaded" in result[0].text

    @pytest.mark.asyncio
    async def test_load_multiple_csvs_file_not_found(self, server):
        """Test loading multiple CSVs with non-existent files."""
        tools = DataLoadingTools(server)

        args = LoadMultipleCSVsArgs(
            pattern_or_files=["/non/existent1.csv", "/non/existent2.csv"]
        )

        with pytest.raises(CSVLoadError) as exc_info:
            await tools.load_multiple_csvs(args)

        assert "File not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_discover_csv_files_success(self, server, create_multiple_csv_files):
        """Test successful CSV file discovery."""
        tools = DataLoadingTools(server)

        pattern = str(
            Path(next(iter(create_multiple_csv_files.values()))).parent / "*.csv"
        )
        args = DiscoverCSVFilesArgs(pattern=pattern)

        result = await tools.discover_csv_files(args)

        assert len(result) == 1
        assert "Found" in result[0].text
        assert "files matching pattern" in result[0].text
        assert ".csv" in result[0].text

    @pytest.mark.asyncio
    async def test_discover_csv_files_no_matches(self, server, temp_dir):
        """Test CSV file discovery with no matches."""
        tools = DataLoadingTools(server)

        pattern = str(temp_dir / "nonexistent*.csv")
        args = DiscoverCSVFilesArgs(pattern=pattern)

        result = await tools.discover_csv_files(args)

        assert len(result) == 1
        assert "Found 0 files" in result[0].text


@pytest.mark.integration
class TestDataLoadingIntegration:
    """Integration tests for data loading."""

    @pytest.mark.asyncio
    async def test_load_and_query_csv(self, server, create_csv_file):
        """Test loading CSV and then querying it."""
        csv_file = create_csv_file("integration_test", "employees")
        tools = DataLoadingTools(server)

        # Load the CSV
        args = LoadCSVArgs(file_path=str(csv_file))
        load_result = await tools.load_csv(args)

        assert len(load_result) == 1
        assert "integration_test" in server.get_loaded_tables()

        # Query the loaded data
        query_result = await server.execute_query(
            "SELECT COUNT(*) as count FROM integration_test"
        )
        assert len(query_result) == 1
        assert query_result[0]["count"] > 0

    @pytest.mark.asyncio
    async def test_load_multiple_files_different_schemas(self, server, temp_dir):
        """Test loading multiple files with different schemas using union_by_name."""
        # Create files with different column orders
        file1_content = "name,age,department\nJohn,30,Engineering"
        file2_content = "department,name,age,salary\nSales,Jane,25,50000"

        file1 = temp_dir / "file1.csv"
        file2 = temp_dir / "file2.csv"
        file1.write_text(file1_content)
        file2.write_text(file2_content)

        tools = DataLoadingTools(server)

        args = LoadMultipleCSVsArgs(
            pattern_or_files=[str(file1), str(file2)],
            table_name="union_test",
            union_by_name=True,
        )
        result = await tools.load_multiple_csvs(args)

        assert len(result) == 1
        assert "union_test" in server.get_loaded_tables()

        # Verify the data was combined correctly
        query_result = await server.execute_query(
            "SELECT COUNT(*) as count FROM union_test"
        )
        assert query_result[0]["count"] == 2

    @pytest.mark.asyncio
    async def test_nested_directory_discovery(self, server, create_nested_csv_files):
        """Test discovering CSV files in nested directories."""
        tools = DataLoadingTools(server)

        root_dir = Path(next(iter(create_nested_csv_files.values()))).parent
        pattern = str(root_dir / "**/*.csv")

        args = DiscoverCSVFilesArgs(pattern=pattern)
        result = await tools.discover_csv_files(args)

        assert len(result) == 1
        response_text = result[0].text
        assert "Found" in response_text
        assert "files matching pattern" in response_text

        # Should find files in subdirectories
        file_count = len(create_nested_csv_files)
        assert str(file_count) in response_text
