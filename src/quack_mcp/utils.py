"""Utility functions for Quack MCP server."""

import json
import re
from pathlib import Path
from typing import Any


def safe_json_dumps(obj: Any, indent: int | None = 2) -> str:
    """Safely serialize object to JSON, handling Python-specific types."""

    def json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for Python types."""
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(obj, default=json_serializer, indent=indent)


def sanitize_table_name(name: str) -> str:
    """Sanitize table name for DuckDB."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def escape_sql_string(value: str) -> str:
    """Escape single quotes in SQL strings."""
    return value.replace("'", "''")


def get_column_type_icon(column_type: str) -> str:
    """Get emoji icon for column type."""
    lower_type = column_type.lower()
    if any(t in lower_type for t in ["int", "bigint", "double", "decimal", "numeric"]):
        return "🔢"
    if any(t in lower_type for t in ["varchar", "text", "string", "char"]):
        return "📝"
    if any(t in lower_type for t in ["date", "timestamp", "time"]):
        return "📅"
    if "bool" in lower_type:
        return "✅"
    return "📊"


def format_sample_data(data: list[dict[str, Any]], schema: list[dict[str, Any]]) -> str:
    """Format sample data for display."""
    if not data:
        return "  No data available\n"

    result = ""
    column_names = [col["column_name"] for col in schema]

    # Create header
    result += "  " + " | ".join(name.ljust(15) for name in column_names) + "\n"
    result += "  " + "─┼─".join("─" * 15 for _ in column_names) + "\n"

    # Add data rows
    for row in data:
        values = []
        for name in column_names:
            value = row.get(name)
            str_value = "NULL" if value is None else str(value)
            truncated = str_value[:12] + "..." if len(str_value) > 15 else str_value
            values.append(truncated.ljust(15))
        result += "  " + " | ".join(values) + "\n"

    return result


def validate_file_exists(file_path: str) -> Path:
    """Validate that file exists and return Path object."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path


def is_glob_pattern(pattern: str) -> bool:
    """Check if string contains glob pattern characters."""
    return any(char in pattern for char in ["*", "?", "[", "]"])
