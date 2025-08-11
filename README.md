# Quack MCP

The best CSV analyst that pulls everything into DuckDB in order to provide LLM agents the ability to explore and analyze the data with accuracy and efficiency.

## Features

- **CSV Loading**: Load CSV files into DuckDB for fast analysis
- **SQL Querying**: Execute complex SQL queries on your CSV data
- **Data Analysis**: Built-in statistical analysis tools
- **Schema Inspection**: Examine table structures and metadata
- **Expense Optimization**: Analyze spending patterns and identify savings opportunities
- **Anomaly Detection**: Detect irregularities and outliers in datasets
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

### Core Analysis Tools

#### `load_csv`
Load a CSV file into DuckDB for analysis.

**Parameters:**
- `file_path` (required): Path to the CSV file
- `table_name` (optional): Name for the table (defaults to filename)
- `delimiter` (optional): CSV delimiter (default: ",")
- `header` (optional): Whether CSV has header row (default: true)

#### `query_csv`
Execute SQL queries on loaded CSV data.

**Parameters:**
- `query` (required): SQL query to execute

#### `describe_table`
Get schema information for a loaded table.

**Parameters:**
- `table_name` (required): Name of the table to describe

#### `list_tables`
List all currently loaded tables.

#### `analyze_csv`
Perform basic statistical analysis on CSV data.

**Parameters:**
- `table_name` (required): Name of the table to analyze
- `columns` (optional): Specific columns to analyze

### Specialized Analysis Tools

#### `optimize_expenses`
Analyze credit card or bank transaction data to identify expense optimization opportunities with actionable recommendations and realistic savings estimates.

**Parameters:**
- `table_name` (required): Name of the loaded table containing transaction data
- `amount_column` (optional, default: "Amount"): Column containing transaction amounts
- `name_column` (optional, default: "Name"): Column containing merchant/transaction descriptions
- `date_column` (optional, default: "Date"): Column containing transaction dates

**Required Data Format:**
- **Amount**: Numeric values (negative for expenses, positive for income)
- **Name**: Text description of the merchant or transaction
- **Date**: Date of the transaction (YYYY-MM-DD or similar format)

**Features:**
- 📊 Monthly spending analysis with trends and largest purchases
- 🔄 Subscription detection - automatically finds recurring charges
- ☕ Small purchase categorization - groups coffee, dining, treats, etc.
- 🛒 Grocery spending optimization - analyzes shopping patterns
- 💰 Savings estimates - calculates realistic monthly savings potential
- 📋 Action prioritization - orders recommendations by impact vs. effort

#### `detect_anomalies`
Detect anomalies and irregularities in dataset using statistical analysis and business logic rules.

**Parameters:**
- `table_name` (required): Name of the table to analyze for anomalies
- `anomaly_types` (optional): Types of anomalies to detect: statistical, duplicates, nulls, outliers, patterns, business_logic
- `focus_columns` (optional): Specific columns to focus anomaly detection on
- `severity_threshold` (optional, default: "medium"): Minimum severity level to report (low, medium, high, critical)

## Example Workflows

### Basic CSV Analysis
1. Load a CSV file: `load_csv` with your file path
2. Examine the structure: `describe_table` or `list_tables`
3. Query your data: `query_csv` with SQL queries
4. Analyze patterns: `analyze_csv` for statistical insights

### Expense Optimization Analysis
1. Load transaction data: `load_csv` with your credit card/bank data
2. Run optimization analysis: `optimize_expenses` with the table name
3. Review savings opportunities and implement recommendations

### Data Quality Assessment
1. Load your dataset: `load_csv` with your data file
2. Run anomaly detection: `detect_anomalies` to identify data issues
3. Clean data based on findings and re-analyze

## Using with Claude Code

### Prerequisites
- Claude Code installed and configured
- Node.js installed on your system
- Quack MCP server built (`npm install && npm run build`)

### Configuration

Add the following to your Claude Code MCP configuration file (usually `~/.config/claude-code/mcp_servers.json`):

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

### Usage Examples

#### Basic CSV Analysis
```
Load the CSV file at /path/to/your/data.csv
```

#### Expense Analysis
```
I have credit card data at /Users/me/transactions.csv. Load it and run an expense optimization analysis.
```

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

### Available Tools in Claude Code

#### `load_csv`
- **Usage**: "Load the CSV at /path/to/file.csv"
- **Features**: Automatic delimiter detection, schema analysis, sample preview

#### `query_csv`
- **Usage**: "Query the data to find all records where column > value"
- **Features**: Full SQL support including JOINs, aggregations, window functions

#### `describe_table`
- **Usage**: "Describe the structure of table_name"

#### `list_tables`
- **Usage**: "What tables are currently loaded?"

#### `analyze_csv`
- **Usage**: "Analyze the numerical columns in my data"
- **Features**: Count, unique values, min/max, averages

#### `optimize_expenses`
- **Usage**: "Analyze my spending for optimization opportunities"
- **Features**: Subscription detection, category analysis, savings calculations

#### `detect_anomalies`
- **Usage**: "Find anomalies in my dataset"
- **Features**: Statistical outliers, data quality issues, pattern detection

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

## MCP Client Configuration

For other MCP clients, add to your configuration:

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
