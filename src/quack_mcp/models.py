"""Pydantic models for Quack MCP tool schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LoadCSVArgs(BaseModel):
    """Arguments for load_csv tool."""

    file_path: str = Field(..., description="Path to the CSV file to load")
    table_name: str | None = Field(
        None, description="Name for the table (optional, defaults to filename)"
    )
    delimiter: str = Field(",", description="CSV delimiter (default: ',')")
    header: bool = Field(True, description="Whether CSV has header row (default: true)")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("file_path cannot be empty")
        return v


class LoadMultipleCSVsArgs(BaseModel):
    """Arguments for load_multiple_csvs tool."""

    pattern_or_files: str | list[str] = Field(
        ...,
        description="Glob pattern or array of file paths to load"
    )
    table_name: str = Field(
        "multi_csv_data",
        description="Name for the combined table (optional, defaults to 'multi_csv_data')"
    )
    union_by_name: bool = Field(
        False,
        description="Combine files by column name instead of position (default: false)"
    )
    include_filename: bool = Field(
        False,
        description="Include a filename column to track source file for each row (default: false)"
    )
    delimiter: str = Field(",", description="CSV delimiter (default: ',')")
    header: bool = Field(True, description="Whether CSV files have header rows (default: true)")


class LoadExcelArgs(BaseModel):
    """Arguments for load_excel tool."""

    file_path: str = Field(..., description="Path to the Excel file to load")
    table_name: str | None = Field(
        None, description="Name for the table (optional, defaults to filename)"
    )
    sheet: str | None = Field(
        None,
        description="Name or index of the sheet to load (optional, defaults to first sheet)"
    )
    range: str | None = Field(
        None,
        description="Cell range to load (e.g., 'A1:C10') (optional, loads all data by default)"
    )
    header: bool = Field(True, description="Whether Excel file has header row (default: true)")
    all_varchar: bool = Field(
        False, description="Force all columns to be treated as text (default: false)"
    )

    @field_validator("file_path")
    @classmethod
    def validate_excel_file(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("file_path cannot be empty")
        if not v.lower().endswith(".xlsx"):
            raise ValueError("Only .xlsx files are supported")
        return v


class LoadMultipleExcelsArgs(BaseModel):
    """Arguments for load_multiple_excels tool."""

    pattern_or_files: str | list[str] = Field(
        ...,
        description="Glob pattern or array of file paths to load"
    )
    table_name: str = Field(
        "multi_excel_data",
        description="Name for the combined table (optional, defaults to 'multi_excel_data')"
    )
    union_by_name: bool = Field(
        False,
        description="Combine files by column name instead of position (default: false)"
    )
    include_filename: bool = Field(
        False,
        description="Include a filename column to track source file for each row (default: false)"
    )
    sheet: str | None = Field(
        None,
        description="Name or index of the sheet to load from all files (optional, defaults to first sheet)"
    )
    header: bool = Field(True, description="Whether Excel files have header rows (default: true)")
    all_varchar: bool = Field(
        False, description="Force all columns to be treated as text (default: false)"
    )


class QueryCSVArgs(BaseModel):
    """Arguments for query_csv tool."""

    query: str = Field(..., description="SQL query to execute")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query cannot be empty")
        return v


class DescribeTableArgs(BaseModel):
    """Arguments for describe_table tool."""

    table_name: str = Field(..., description="Name of the table to describe")

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("table_name cannot be empty")
        return v


class AnalyzeCSVArgs(BaseModel):
    """Arguments for analyze_csv tool."""

    table_name: str = Field(..., description="Name of the table to analyze")
    columns: list[str] | None = Field(
        None, description="Specific columns to analyze (optional)"
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("table_name cannot be empty")
        return v


class DiscoverCSVFilesArgs(BaseModel):
    """Arguments for discover_csv_files tool."""

    pattern: str = Field(
        ...,
        description="Glob pattern to search for CSV files (e.g., '*.csv', 'data/**/*.csv')"
    )

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("pattern cannot be empty")
        return v


class DiscoverExcelFilesArgs(BaseModel):
    """Arguments for discover_excel_files tool."""

    pattern: str = Field(
        ...,
        description="Glob pattern to search for Excel files (e.g., '*.xlsx', 'data/**/*.xlsx')"
    )

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("pattern cannot be empty")
        return v


class OptimizeExpensesArgs(BaseModel):
    """Arguments for optimize_expenses tool."""

    table_name: str = Field(..., description="Name of the table containing transaction data")
    amount_column: str = Field("Amount", description="Name of the column containing transaction amounts")
    name_column: str = Field("Name", description="Name of the column containing merchant/transaction names")
    date_column: str = Field("Date", description="Name of the column containing transaction dates")

    @field_validator("table_name", "amount_column", "name_column", "date_column")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field cannot be empty")
        return v


AnomalyType = Literal["statistical", "duplicates", "nulls", "outliers", "patterns", "business_logic"]
SeverityLevel = Literal["low", "medium", "high", "critical"]


class DetectAnomaliesArgs(BaseModel):
    """Arguments for detect_anomalies tool."""

    table_name: str = Field(..., description="Name of the table to analyze for anomalies")
    severity_threshold: SeverityLevel = Field(
        "medium",
        description="Minimum severity level to report (low, medium, high, critical)"
    )
    focus_columns: list[str] | None = Field(
        None, description="Specific columns to focus anomaly detection on (optional)"
    )
    anomaly_types: list[AnomalyType] = Field(
        ["statistical", "duplicates", "nulls", "outliers", "patterns"],
        description="Types of anomalies to detect: statistical, duplicates, nulls, outliers, patterns, business_logic"
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("table_name cannot be empty")
        return v


# Response models for better type safety
class MCPTextContent(BaseModel):
    """MCP text content response."""

    type: Literal["text"] = "text"
    text: str


class MCPToolResponse(BaseModel):
    """MCP tool response wrapper."""

    content: list[MCPTextContent]
