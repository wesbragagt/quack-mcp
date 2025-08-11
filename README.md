# Quack MCP

The best CSV analyst that pulls everything into DuckDB in order to provide LLM agents the ability to explore and analyze the data with accuracy and efficiency.

## Features

- **CSV Loading**: Load CSV files into DuckDB for fast analysis
- **SQL Querying**: Execute complex SQL queries on your CSV data
- **Data Analysis**: Built-in statistical analysis tools
- **Schema Inspection**: Examine table structures and metadata
- **MCP Integration**: Works seamlessly with MCP clients like Claude Code

## Installation

```bash
npm install
npm run build
```

## Usage

The server runs via stdin/stdout transport for MCP protocol:

```bash
node dist/index.js
```

## Available Tools

### `load_csv`
Load a CSV file into DuckDB for analysis.

**Parameters:**
- `file_path` (required): Path to the CSV file
- `table_name` (optional): Name for the table (defaults to filename)
- `delimiter` (optional): CSV delimiter (default: ",")
- `header` (optional): Whether CSV has header row (default: true)

### `query_csv`
Execute SQL queries on loaded CSV data.

**Parameters:**
- `query` (required): SQL query to execute

### `describe_table`
Get schema information for a loaded table.

**Parameters:**
- `table_name` (required): Name of the table to describe

### `list_tables`
List all currently loaded tables.

### `analyze_csv`
Perform basic statistical analysis on CSV data.

**Parameters:**
- `table_name` (required): Name of the table to analyze
- `columns` (optional): Specific columns to analyze

## Example Workflow

1. Load a CSV file: `load_csv` with your file path
2. Examine the structure: `describe_table` or `list_tables`
3. Query your data: `query_csv` with SQL queries
4. Analyze patterns: `analyze_csv` for statistical insights

## MCP Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "quack-mcp": {
      "command": "node",
      "args": ["/path/to/quack-mcp/dist/index.js"]
    }
  }
}
```
