"""Custom exceptions for Quack MCP server."""


class QuackMCPError(Exception):
    """Base exception for Quack MCP server errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class CSVLoadError(QuackMCPError):
    """Raised when CSV loading fails."""

    def __init__(self, message: str, file_path: str | None = None):
        if file_path:
            message = f"Failed to load CSV '{file_path}': {message}"
        super().__init__(message)


class ExcelLoadError(QuackMCPError):
    """Raised when Excel loading fails."""

    def __init__(self, message: str, file_path: str | None = None):
        if file_path:
            message = f"Failed to load Excel '{file_path}': {message}"
        super().__init__(message)


class QueryError(QuackMCPError):
    """Raised when SQL query execution fails."""

    def __init__(self, message: str, query: str | None = None):
        if query:
            message = f"Query failed: {message}\nQuery: {query}"
        super().__init__(message)


class TableNotFoundError(QuackMCPError):
    """Raised when a referenced table is not found."""

    def __init__(self, table_name: str):
        super().__init__(f"Table '{table_name}' not found")


class FileDiscoveryError(QuackMCPError):
    """Raised when file discovery fails."""

    def __init__(self, message: str, pattern: str | None = None):
        if pattern:
            message = f"File discovery failed for pattern '{pattern}': {message}"
        super().__init__(message)
