# Using Quack MCP with Claude Code

This guide shows how to configure and use the Quack MCP server with Claude Code for powerful CSV analysis.

## Prerequisites

- Claude Code installed and configured
- Node.js installed on your system
- Quack MCP server built (`npm install && npm run build`)

## Configuration

### 1. Add to Claude Code MCP Configuration

Add the following to your Claude Code MCP configuration file (usually `~/.config/claude-code/mcp_servers.json` or similar):

```json
{
  "mcpServers": {
    "quack-csv": {
      "command": "node",
      "args": ["/absolute/path/to/quack-mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

**Important:** Replace `/absolute/path/to/quack-mcp` with the actual full path to your Quack MCP directory.

### 2. Restart Claude Code

After adding the configuration, restart Claude Code to load the new MCP server.

### 3. Verify Connection

You can verify the server is connected by asking Claude Code: "What MCP tools are available?" You should see the Quack CSV tools listed.

## Usage Examples

### Basic CSV Analysis Workflow

1. **Load a CSV file**:
```
Load the CSV file at /path/to/your/data.csv
```

Claude Code will use the `load_csv` tool and automatically show you:
- Total number of rows
- Complete schema with column types
- Sample data preview
- Visual type indicators

2. **Explore the data structure**:
```
Show me all the tables that are currently loaded
```

3. **Query your data**:
```
Find all records where salary > 60000 and age < 30
```

4. **Perform statistical analysis**:
```
Analyze the salary and age columns in the dataset
```

### Advanced Usage Examples

#### Complex Data Analysis
```
I have sales data at /Users/me/sales_2024.csv. Load it and then:
1. Show me monthly sales trends
2. Find the top 10 customers by revenue
3. Calculate average order value by product category
```

#### Data Quality Assessment
```
Load /path/to/customer_data.csv and help me understand:
- How many missing values are in each column
- What's the distribution of customer ages
- Are there any duplicate customer IDs
```

#### Multi-step Analysis
```
Load the inventory data at /data/inventory.csv and:
1. Find products with low stock levels (< 10 units)
2. Calculate total inventory value by category
3. Show me which suppliers have the most products
```

## Available Tools

### `load_csv`
- **Purpose**: Load CSV files into DuckDB with automatic schema inspection
- **Usage**: "Load the CSV at /path/to/file.csv"
- **Features**: 
  - Automatic delimiter detection
  - Schema analysis with type inference
  - Sample data preview
  - Row count summary

### `query_csv`
- **Purpose**: Execute SQL queries on loaded data
- **Usage**: "Query the data to find all records where column > value"
- **Features**: Full SQL support including JOINs, aggregations, window functions

### `describe_table`
- **Purpose**: Get detailed schema information
- **Usage**: "Describe the structure of table_name"

### `list_tables`
- **Purpose**: Show all loaded tables
- **Usage**: "What tables are currently loaded?"

### `analyze_csv`
- **Purpose**: Perform statistical analysis
- **Usage**: "Analyze the numerical columns in my data"
- **Features**: Count, unique values, min/max, averages

## Tips for Best Results

### 1. Use Clear, Natural Language
Instead of technical commands, use natural descriptions:
- ❌ "Execute load_csv with file_path=/data/sales.csv"
- ✅ "Load the sales data from /data/sales.csv"

### 2. Leverage Claude's SQL Knowledge
Ask for complex analysis in plain English:
- "Show me the correlation between price and sales volume"
- "Find seasonal patterns in the data"
- "Identify outliers in the revenue column"

### 3. Iterative Analysis
Build on previous queries:
- "Now filter that result to only include 2024 data"
- "Add a column showing the percentage change from last month"

### 4. Data Visualization Requests
Ask for formatted output:
- "Create a summary table of sales by region"
- "Show the top 10 results formatted nicely"

## Troubleshooting

### Server Not Found
If Claude Code can't find the MCP server:
1. Check that the path in your configuration is absolute and correct
2. Verify `npm run build` completed successfully
3. Restart Claude Code after configuration changes

### Permission Errors
If you get file access errors:
1. Ensure the CSV file path is correct and accessible
2. Check file permissions
3. Use absolute paths for CSV files

### SQL Errors
If queries fail:
1. Check the table name (use `list_tables` to verify)
2. Verify column names with `describe_table`
3. Remember DuckDB uses standard SQL syntax

### Performance Issues
For large CSV files:
1. DuckDB is optimized for analytics but very large files may take time to load
2. Consider using `LIMIT` clauses for initial exploration
3. The server loads data into memory - ensure sufficient RAM

## Example Session

Here's a complete example of analyzing sales data:

```
User: Load the sales data from /Users/me/Documents/sales_2024.csv

Claude: I'll load your sales data using the Quack MCP server.

[Server loads file and shows schema inspection with 15,432 rows, columns like date, product, quantity, revenue, etc.]

User: What are the top 5 products by total revenue?

Claude: I'll query the data to find the top 5 products by revenue.

[Shows SQL results with product names and total revenue]

User: Now show me monthly sales trends for those top products

Claude: I'll analyze the monthly trends for those top-performing products.

[Shows time-series analysis with monthly breakdown]
```

This MCP server transforms CSV analysis in Claude Code from a manual, multi-step process into a conversational, intelligent workflow where you can focus on insights rather than data manipulation mechanics.