# Quack MCP Development Guidelines

This document outlines the development guidelines, coding conventions, and best practices for the Quack MCP server project.

## Project Overview

Quack MCP is a Model Context Protocol (MCP) server that provides CSV and Excel analysis capabilities using DuckDB. The project emphasizes type safety, performance, and maintainability through strict Python typing, modern Python patterns, and comprehensive testing.

## Python Configuration

### Environment Requirements

The project requires Python 3.12+ and uses modern Python features:

- **Python 3.12+** with modern type hints (`list[T]`, `dict[K,V]`, `str | None`)
- **uv** package manager for fast dependency resolution
- **pyproject.toml** for project configuration
- **No requirements.txt** - uv handles all dependencies

### Code Quality Tools

```toml
# pyproject.toml configuration
[tool.ruff]
target-version = "py312"
line-length = 88
fix = true

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG001", "SIM", "TCH", "TID", "Q", "PTH", "ERA", "PL", "TRY", "RUF"]

[tool.pyright]
include = ["src"]
typeCheckingMode = "strict"
pythonVersion = "3.12"
```

**Key Rules:**
- **All type annotations must be explicit** - Use modern Python 3.12 type hints
- **Strict type checking** - pyright enforces complete type safety
- **No unused variables or imports** - Clean, minimal code only
- **Consistent file naming** - Use snake_case for files and functions

## Architecture Guidelines

### Class Structure

All classes follow a consistent structure:

```python
class QuackMCPServer:
    """Main MCP server for CSV and Excel analysis using DuckDB."""

    def __init__(self) -> None:
        """Initialize the QuackMCP server."""
        # 1. Initialize core properties
        self.server = Server("quack-mcp")
        self.db: duckdb.DuckDBPyConnection | None = None
        self.loaded_tables: dict[str, str] = {}
        
        # 2. Initialize tool handlers
        self.data_tools = DataLoadingTools(self)
        self.analysis_tools = AnalysisTools(self)
        self.specialized_tools = SpecializedTools(self)
        
        # 3. Setup handlers
        self._setup_handlers()

    # 4. Private setup methods
    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""
        # Configuration logic

    # 5. Public async methods (tool handlers)
    async def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute SQL query and return results."""
        # Implementation

    # 6. Utility methods
    def get_db_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        # Implementation
```

### Method Naming Conventions

- **Tool handlers**: Use snake_case matching the tool name (`load_csv`, `query_csv`)
- **Private methods**: Use snake_case with leading underscore (`_setup_handlers`, `_validate_input`)
- **Async methods**: Always mark as `async` and return proper type hints
- **Properties**: Use descriptive names and type hints

### Error Handling

All errors must be handled consistently using custom exceptions:

```python
try:
    # Operation
    result = await self.execute_query(query)
except Exception as e:
    raise QueryError(f"Query execution failed: {e!s}", query) from e
```

**Rules:**
- Always catch and wrap errors in appropriate custom exceptions
- Provide descriptive error messages with context
- Use `from e` to preserve exception chains
- Never let raw exceptions propagate to MCP clients

## Import Standards

### Import Organization

Imports must be organized in this order:

```python
# 1. Standard library imports
import asyncio
from pathlib import Path
from typing import Any, Optional

# 2. Third-party libraries
import duckdb
from mcp.server import Server
from pydantic import BaseModel, Field, field_validator

# 3. Internal modules
from .exceptions import QuackMCPError, QueryError
from .models import LoadCSVArgs, QueryCSVArgs
from .tools.data_loading import DataLoadingTools
```

### Type Hints

Use modern Python 3.12 type hints:

```python
# Modern Python 3.12 style
def process_data(items: list[dict[str, Any]]) -> dict[str, int | None]:
    """Process data with modern type hints."""
    result: dict[str, int | None] = {}
    for item in items:
        result[item["key"]] = item.get("value")
    return result
```

**Avoid deprecated typing:**
- ❌ `List[str]`, `Dict[str, int]`, `Optional[str]`
- ✅ `list[str]`, `dict[str, int]`, `str | None`

## Pydantic Models

### Model Definition

All tool arguments use Pydantic v2 models:

```python
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
```

**Schema Rules:**
- All parameters must have Field descriptions
- Use appropriate type hints (`str`, `bool`, `list[str]`, etc.)
- Include `@field_validator` for custom validation
- Always use `@classmethod` with field validators
- Specify default values in Field, not in type hints

### Tool Handler Implementation

```python
async def load_csv(self, args: LoadCSVArgs) -> list[TextContent]:
    """Load CSV file into DuckDB."""
    try:
        # 1. Validate and extract arguments
        file_path = Path(args.file_path)
        table_name = args.table_name or sanitize_table_name(file_path.stem)
        
        # 2. Business logic
        result = await self._load_csv_file(file_path, table_name, args)
        
        # 3. Return MCP response format
        return [
            TextContent(
                type="text",
                text=f"Successfully loaded CSV: {result}"
            )
        ]
    except Exception as e:
        if isinstance(e, (CSVLoadError, QueryError)):
            raise
        raise CSVLoadError(f"CSV loading failed: {e!s}") from e
```

## Database Operations

### Query Execution Pattern

```python
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
```

### SQL Query Construction

- **Use f-strings** for query building with proper escaping
- **Always escape user input** using helper functions
- **Use parameterized queries** when possible
- **Add query logging** for debugging

```python
def escape_sql_string(value: str) -> str:
    """Escape SQL string value."""
    return value.replace("'", "''")

# Usage
escaped_path = escape_sql_string(args.file_path)
query = f"""
    CREATE OR REPLACE TABLE "{table_name}" AS 
    SELECT * FROM read_csv('{escaped_path}', 
        header={str(args.header).lower()},
        delim='{args.delimiter}'
    )
"""
```

### Table Management

- **Validate table names**: Use sanitization functions
- **Check for empty results**: Drop tables with zero rows
- **Track loaded tables**: Use `self.loaded_tables` dictionary

```python
def sanitize_table_name(name: str) -> str:
    """Sanitize table name for DuckDB."""
    import re
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)

# Check if the table has any rows
count_result = await self.execute_query(f'SELECT COUNT(*) as row_count FROM "{table_name}"')
row_count = count_result[0]["row_count"] if count_result else 0

if row_count == 0:
    await self.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
    raise CSVLoadError("No data was loaded from the CSV file")

self.loaded_tables[table_name] = str(file_path)
```

## Testing Standards

### Test File Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_analysis.py         # Analysis tools tests
├── test_data_loading.py     # Data loading tests
├── test_models.py           # Pydantic model validation tests
└── test_server.py           # Server integration tests
```

### Test Structure

```python
import pytest
from pathlib import Path
from quack_mcp.models import LoadCSVArgs
from quack_mcp.tools.data_loading import DataLoadingTools

@pytest.mark.unit
class TestDataLoadingTools:
    """Test data loading functionality."""

    @pytest.mark.asyncio
    async def test_load_csv_success(self, server, create_csv_file):
        """Test successful CSV loading."""
        # Arrange
        csv_file = create_csv_file("test_data", "employees")
        tools = DataLoadingTools(server)
        args = LoadCSVArgs(file_path=str(csv_file))
        
        # Act
        result = await tools.load_csv(args)
        
        # Assert
        assert len(result) == 1
        assert "Successfully loaded CSV" in result[0].text
        assert "test_data" in server.get_loaded_tables()
```

### Fixtures and Test Data

Use pytest fixtures for reusable test components:

```python
@pytest.fixture
def sample_csv_data() -> dict[str, str]:
    """Sample CSV data for testing."""
    return {
        "employees": """name,age,department,salary
John Doe,30,Engineering,75000
Jane Smith,25,Marketing,65000""",
        
        "sales": """date,product,quantity,price
2024-01-01,Widget A,10,25.50
2024-01-02,Widget B,5,45.00""",
    }

@pytest.fixture
def create_csv_file(temp_dir: Path, sample_csv_data: dict[str, str]):
    """Factory fixture to create CSV files in temp directory."""
    def _create_csv_file(name: str, data_key: str = None) -> Path:
        if data_key is None:
            data_key = name
        
        csv_path = temp_dir / f"{name}.csv"
        csv_path.write_text(sample_csv_data.get(data_key, sample_csv_data["employees"]))
        return csv_path
    
    return _create_csv_file
```

### Assertion Patterns

```python
# Test Pydantic validation
with pytest.raises(ValidationError) as exc_info:
    LoadCSVArgs(file_path="")
assert "file_path cannot be empty" in str(exc_info.value)

# Test async operations
result = await server.execute_query("SELECT COUNT(*) as count FROM test_table")
assert len(result) == 1
assert result[0]["count"] > 0

# Test MCP responses
assert isinstance(result, list)
assert len(result) > 0
assert isinstance(result[0], TextContent)
assert "expected text" in result[0].text
```

## File and Path Handling

### Path Operations

Use `pathlib.Path` for all file operations:

```python
from pathlib import Path

def process_file(file_path: str) -> dict[str, Any]:
    """Process file using pathlib."""
    path = Path(file_path)
    
    # Check existence
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Get metadata
    return {
        "name": path.name,
        "stem": path.stem,
        "suffix": path.suffix,
        "size": path.stat().st_size,
        "absolute": path.resolve(),
    }
```

### Glob Pattern Support

Support standard glob patterns for file discovery:

```python
def discover_files(pattern: str) -> list[Path]:
    """Discover files using glob pattern."""
    # Use DuckDB's glob function for consistency
    query = f"SELECT file FROM glob('{escape_sql_string(pattern)}')"
    result = await self.execute_query(query)
    return [Path(row["file"]) for row in result]
```

## Performance Guidelines

### Efficient Patterns

- **Leverage DuckDB's parallel processing** - Let DuckDB handle multiple files
- **Use appropriate data types** - Avoid forcing all columns to VARCHAR
- **Stream large results** - Use LIMIT for exploration
- **Batch operations** - Combine multiple queries when possible

### Memory Management

```python
# Use DuckDB's memory management
self.db = duckdb.connect(":memory:")  # In-memory database

# Clean up empty tables
if row_count == 0:
    await self.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
    
# Close connections properly
def cleanup(self) -> None:
    """Clean up database resources."""
    if self.db:
        self.db.close()
        self.db = None
```

## Documentation Standards

### Code Documentation

Use clear docstrings for all public methods:

```python
async def load_csv(self, args: LoadCSVArgs) -> list[TextContent]:
    """Load a CSV file into DuckDB for analysis.
    
    Args:
        args: CSV loading arguments including file path, table name, delimiter, etc.
        
    Returns:
        List containing a TextContent response with loading results and table schema.
        
    Raises:
        CSVLoadError: If file cannot be loaded or is empty.
        QueryError: If DuckDB query execution fails.
    """
```

### Tool Documentation

Each tool requires comprehensive documentation in README.md:

- Clear description of purpose
- Parameter documentation with types and defaults
- Example usage patterns
- Error conditions and troubleshooting

## Security Guidelines

### Input Validation

```python
@field_validator("file_path")
@classmethod
def validate_file_path(cls, v: str) -> str:
    """Validate file path for security."""
    if not v.strip():
        raise ValueError("file_path cannot be empty")
    
    # Prevent directory traversal
    path = Path(v).resolve()
    if ".." in str(path):
        raise ValueError("Directory traversal not allowed")
    
    return str(path)
```

### SQL Injection Prevention

```python
def escape_sql_string(value: str) -> str:
    """Escape SQL string to prevent injection."""
    return value.replace("'", "''")

def sanitize_table_name(name: str) -> str:
    """Sanitize table name for safe SQL usage."""
    import re
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)
```

## Development Workflow

### Before Committing

1. **Run tests**: `uv run pytest`
2. **Run type checking**: `uv run pyright`
3. **Run linting**: `uv run ruff check --fix`
4. **Test functionality**: Manual testing with sample data

### Code Review Checklist

- [ ] All new features have comprehensive tests
- [ ] Error handling follows established patterns
- [ ] Type hints are complete and correct
- [ ] Documentation updated for public APIs
- [ ] Performance implications considered
- [ ] Security implications reviewed
- [ ] Pydantic models include proper validation

## Deployment Guidelines

### Local Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run server
uv run python -m quack_mcp.server
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
WORKDIR /app
COPY . .
RUN uv sync --frozen
CMD ["uv", "run", "python", "-m", "quack_mcp.server"]
```

This document serves as the authoritative guide for maintaining code quality and consistency across the Quack MCP Python project.