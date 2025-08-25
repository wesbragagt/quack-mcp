"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from quack_mcp.models import (
    LoadCSVArgs,
    LoadMultipleCSVsArgs,
    LoadExcelArgs,
    QueryCSVArgs,
    DescribeTableArgs,
    AnalyzeCSVArgs,
    OptimizeExpensesArgs,
    DetectAnomaliesArgs,
    DiscoverCSVFilesArgs,
    MCPTextContent,
    MCPToolResponse,
)


@pytest.mark.unit
class TestLoadCSVArgs:
    """Test LoadCSVArgs model validation."""

    def test_valid_args(self):
        """Test valid CSV loading arguments."""
        args = LoadCSVArgs(
            file_path="/path/to/file.csv",
            table_name="test_table",
            delimiter=",",
            header=True
        )
        
        assert args.file_path == "/path/to/file.csv"
        assert args.table_name == "test_table"
        assert args.delimiter == ","
        assert args.header is True

    def test_required_field_missing(self):
        """Test validation error when required field is missing."""
        with pytest.raises(ValidationError):
            LoadCSVArgs()

    def test_empty_file_path(self):
        """Test validation error for empty file path."""
        with pytest.raises(ValidationError) as exc_info:
            LoadCSVArgs(file_path="")
        
        assert "file_path cannot be empty" in str(exc_info.value)

    def test_defaults(self):
        """Test default values."""
        args = LoadCSVArgs(file_path="/path/to/file.csv")
        
        assert args.table_name is None
        assert args.delimiter == ","
        assert args.header is True


@pytest.mark.unit
class TestLoadExcelArgs:
    """Test LoadExcelArgs model validation."""

    def test_valid_excel_file(self):
        """Test valid Excel file arguments."""
        args = LoadExcelArgs(
            file_path="/path/to/file.xlsx",
            sheet="Sheet1",
            range="A1:C10"
        )
        
        assert args.file_path == "/path/to/file.xlsx"
        assert args.sheet == "Sheet1"
        assert args.range == "A1:C10"

    def test_invalid_extension(self):
        """Test validation error for non-xlsx files."""
        with pytest.raises(ValidationError) as exc_info:
            LoadExcelArgs(file_path="/path/to/file.xls")
        
        assert "Only .xlsx files are supported" in str(exc_info.value)

    def test_empty_file_path(self):
        """Test validation error for empty file path."""
        with pytest.raises(ValidationError) as exc_info:
            LoadExcelArgs(file_path="")
        
        assert "file_path cannot be empty" in str(exc_info.value)


@pytest.mark.unit
class TestLoadMultipleCSVsArgs:
    """Test LoadMultipleCSVsArgs model validation."""

    def test_string_pattern(self):
        """Test string glob pattern."""
        args = LoadMultipleCSVsArgs(pattern_or_files="data/*.csv")
        
        assert args.pattern_or_files == "data/*.csv"
        assert args.table_name == "multi_csv_data"
        assert args.union_by_name is False
        assert args.include_filename is False

    def test_file_list(self):
        """Test file list."""
        files = ["file1.csv", "file2.csv", "file3.csv"]
        args = LoadMultipleCSVsArgs(pattern_or_files=files)
        
        assert args.pattern_or_files == files

    def test_custom_table_name(self):
        """Test custom table name."""
        args = LoadMultipleCSVsArgs(
            pattern_or_files="*.csv",
            table_name="custom_table",
            union_by_name=True,
            include_filename=True
        )
        
        assert args.table_name == "custom_table"
        assert args.union_by_name is True
        assert args.include_filename is True


@pytest.mark.unit
class TestQueryCSVArgs:
    """Test QueryCSVArgs model validation."""

    def test_valid_query(self):
        """Test valid SQL query."""
        args = QueryCSVArgs(query="SELECT * FROM table")
        assert args.query == "SELECT * FROM table"

    def test_empty_query(self):
        """Test validation error for empty query."""
        with pytest.raises(ValidationError) as exc_info:
            QueryCSVArgs(query="")
        
        assert "query cannot be empty" in str(exc_info.value)

    def test_whitespace_query(self):
        """Test validation error for whitespace-only query."""
        with pytest.raises(ValidationError) as exc_info:
            QueryCSVArgs(query="   ")
        
        assert "query cannot be empty" in str(exc_info.value)


@pytest.mark.unit
class TestAnalyzeCSVArgs:
    """Test AnalyzeCSVArgs model validation."""

    def test_valid_args_with_columns(self):
        """Test valid analyze arguments with specific columns."""
        args = AnalyzeCSVArgs(
            table_name="test_table",
            columns=["col1", "col2", "col3"]
        )
        
        assert args.table_name == "test_table"
        assert args.columns == ["col1", "col2", "col3"]

    def test_valid_args_without_columns(self):
        """Test valid analyze arguments without specific columns."""
        args = AnalyzeCSVArgs(table_name="test_table")
        
        assert args.table_name == "test_table"
        assert args.columns is None

    def test_empty_table_name(self):
        """Test validation error for empty table name."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeCSVArgs(table_name="")
        
        assert "table_name cannot be empty" in str(exc_info.value)


@pytest.mark.unit
class TestOptimizeExpensesArgs:
    """Test OptimizeExpensesArgs model validation."""

    def test_valid_args_with_defaults(self):
        """Test valid expense optimization arguments with defaults."""
        args = OptimizeExpensesArgs(table_name="expenses")
        
        assert args.table_name == "expenses"
        assert args.amount_column == "Amount"
        assert args.name_column == "Name"
        assert args.date_column == "Date"

    def test_valid_args_with_custom_columns(self):
        """Test valid arguments with custom column names."""
        args = OptimizeExpensesArgs(
            table_name="transactions",
            amount_column="transaction_amount",
            name_column="merchant_name",
            date_column="transaction_date"
        )
        
        assert args.table_name == "transactions"
        assert args.amount_column == "transaction_amount"
        assert args.name_column == "merchant_name"
        assert args.date_column == "transaction_date"

    def test_empty_fields_validation(self):
        """Test validation for empty field names."""
        with pytest.raises(ValidationError):
            OptimizeExpensesArgs(table_name="")
        
        with pytest.raises(ValidationError):
            OptimizeExpensesArgs(table_name="test", amount_column="")


@pytest.mark.unit
class TestDetectAnomaliesArgs:
    """Test DetectAnomaliesArgs model validation."""

    def test_valid_args_with_defaults(self):
        """Test valid anomaly detection arguments with defaults."""
        args = DetectAnomaliesArgs(table_name="test_table")
        
        assert args.table_name == "test_table"
        assert args.severity_threshold == "medium"
        assert args.focus_columns is None
        assert "statistical" in args.anomaly_types
        assert "duplicates" in args.anomaly_types

    def test_valid_args_with_custom_settings(self):
        """Test valid arguments with custom settings."""
        args = DetectAnomaliesArgs(
            table_name="data_table",
            severity_threshold="high",
            focus_columns=["col1", "col2"],
            anomaly_types=["statistical", "outliers"]
        )
        
        assert args.table_name == "data_table"
        assert args.severity_threshold == "high"
        assert args.focus_columns == ["col1", "col2"]
        assert args.anomaly_types == ["statistical", "outliers"]

    def test_invalid_severity_threshold(self):
        """Test validation error for invalid severity threshold."""
        with pytest.raises(ValidationError):
            DetectAnomaliesArgs(
                table_name="test",
                severity_threshold="invalid"
            )


@pytest.mark.unit
class TestDiscoverFilesArgs:
    """Test file discovery arguments."""

    def test_valid_csv_pattern(self):
        """Test valid CSV discovery pattern."""
        args = DiscoverCSVFilesArgs(pattern="*.csv")
        assert args.pattern == "*.csv"

    def test_empty_pattern(self):
        """Test validation error for empty pattern."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoverCSVFilesArgs(pattern="")
        
        assert "pattern cannot be empty" in str(exc_info.value)


@pytest.mark.unit
class TestResponseModels:
    """Test MCP response models."""

    def test_mcp_text_content(self):
        """Test MCP text content model."""
        content = MCPTextContent(text="Hello, world!")
        
        assert content.type == "text"
        assert content.text == "Hello, world!"

    def test_mcp_tool_response(self):
        """Test MCP tool response model."""
        content = MCPTextContent(text="Response text")
        response = MCPToolResponse(content=[content])
        
        assert len(response.content) == 1
        assert response.content[0].text == "Response text"
        assert response.content[0].type == "text"

    def test_mcp_tool_response_multiple_content(self):
        """Test MCP tool response with multiple content items."""
        contents = [
            MCPTextContent(text="First response"),
            MCPTextContent(text="Second response")
        ]
        response = MCPToolResponse(content=contents)
        
        assert len(response.content) == 2
        assert response.content[0].text == "First response"
        assert response.content[1].text == "Second response"