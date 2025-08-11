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

### Local Installation

```bash
npm install
npm run build
```

### Docker Installation

#### Prerequisites
- Docker and Docker Compose installed
- Access to CSV files on your host system

#### Building and Running

```bash
# Build the Docker image
docker build -t quack-mcp .

# Or use docker-compose for easier management
docker-compose up quack-mcp
```

#### Development Mode

```bash
# Run with hot reload for development
docker-compose up quack-mcp-dev
```

## Usage

### Local Usage

The server runs via stdin/stdout transport for MCP protocol:

```bash
node src/index.ts
```

### Docker Usage

```bash
# Run with docker-compose (recommended)
docker-compose up quack-mcp

# Or run directly with Docker
docker run -it --rm \
  -v $(pwd)/data:/app/data:ro \
  -v /path/to/your/csv/files:/app/csv-data:ro \
  quack-mcp
```

**Note**: Mount your CSV files as volumes so the container can access them.

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

### Multi-File CSV Tools

#### `load_multiple_csvs`
Load multiple CSV files using glob patterns or file lists into DuckDB for analysis.

**Parameters:**
- `pattern_or_files` (required): Glob pattern (e.g., "data/*.csv", "reports/**/*.csv") or array of specific file paths
- `table_name` (optional): Name for the combined table (defaults to "multi_csv_data")
- `union_by_name` (optional): Combine files by column name instead of position (default: false)
- `include_filename` (optional): Include a filename column to track source file for each row (default: false)
- `delimiter` (optional): CSV delimiter (default: ",")
- `header` (optional): Whether CSV files have header rows (default: true)

**Examples:**
- Load all CSV files in a directory: `"data/*.csv"`
- Load files recursively: `"reports/**/*.csv"`
- Load specific files: `["sales_q1.csv", "sales_q2.csv"]`
- Mix patterns: `["data/sales_*.csv", "archive/legacy_*.csv"]`

#### `discover_csv_files`
Discover CSV files matching a glob pattern without loading them.

**Parameters:**
- `pattern` (required): Glob pattern to search for CSV files

**Returns:** List of matching files with metadata (size, modification date, existence status)

**Note:** The existing `load_csv` tool now also supports glob patterns for backward compatibility.

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
- Either Node.js installed (for local) OR Docker installed (for containerized)

### Local Configuration

For local installation, add the following to your Claude Code MCP configuration file (usually `~/.config/claude-code/mcp_servers.json`):

```json
{
  "mcpServers": {
    "quack-csv": {
      "command": "node",
      "args": ["/absolute/path/to/quack-mcp/src/index.ts"],
      "env": {}
    }
  }
}
```

### Docker Configuration

For Docker deployment, configure Claude Code to use the containerized server:

```json
{
  "mcpServers": {
    "quack-csv": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/absolute/path/to/your/csv/files:/app/csv-data:ro",
        "-v", "/absolute/path/to/quack-mcp/data:/app/data:ro",
        "quack-mcp"
      ],
      "env": {}
    }
  }
}
```

Or with docker-compose:

```json
{
  "mcpServers": {
    "quack-csv": {
      "command": "docker-compose",
      "args": [
        "-f", "/absolute/path/to/quack-mcp/docker-compose.yml",
        "run", "--rm", "quack-mcp"
      ],
      "env": {},
      "cwd": "/absolute/path/to/quack-mcp"
    }
  }
}
```

**Important:** 
- Replace paths with actual full paths to your directories
- Ensure CSV files are accessible via volume mounts for Docker setup
- For Docker setup, build the image first: `docker build -t quack-mcp .`

### Usage Examples

#### Basic CSV Analysis

**Local:**
```
Load the CSV file at /path/to/your/data.csv
```

**Docker:**
```
Load the CSV file at /app/csv-data/data.csv
```
*(Mount your CSV directory to `/app/csv-data` in Docker configuration)*

#### Expense Analysis

**Local:**
```
I have credit card data at /Users/me/transactions.csv. Load it and run an expense optimization analysis.
```

**Docker:**
```
I have credit card data at /app/csv-data/transactions.csv. Load it and run an expense optimization analysis.
```

#### Complex Data Analysis

**Local:**
```
I have sales data at /Users/me/sales_2024.csv. Load it and then:
1. Show me monthly sales trends
2. Find the top 10 customers by revenue
3. Calculate average order value by product category
```

**Docker:**
```
I have sales data at /app/csv-data/sales_2024.csv. Load it and then:
1. Show me monthly sales trends
2. Find the top 10 customers by revenue
3. Calculate average order value by product category
```

#### Data Quality Assessment

**Local:**
```
Load /path/to/customer_data.csv and help me understand:
- How many missing values are in each column
- What's the distribution of customer ages  
- Are there any duplicate customer IDs
```

**Docker:**
```
Load /app/csv-data/customer_data.csv and help me understand:
- How many missing values are in each column
- What's the distribution of customer ages
- Are there any duplicate customer IDs
```

#### Multi-CSV Analysis

**Local:**
```
Load all CSV files matching the pattern /path/to/sales_*.csv and combine them into a single table
```

```
Load multiple quarterly sales files: ["sales_q1.csv", "sales_q2.csv", "sales_q3.csv", "sales_q4.csv"] with filename tracking
```

```
Discover what CSV files are available in /path/to/data/ directory matching the pattern *.csv
```

**Docker:**
```
Load all CSV files in /app/csv-data/reports/ recursively using the pattern /app/csv-data/reports/**/*.csv
```

```
Load monthly data files with different schemas using union by name: /app/csv-data/monthly_*.csv
```

**Advanced Multi-CSV Examples:**
```
I have sales data split across multiple files in /path/to/sales/ directory:
1. Load all files matching sales_2024_*.csv
2. Include filename column to track data sources
3. Use union_by_name since some files have extra columns
4. Analyze total revenue by quarter and source file
```

```
Load transaction data from multiple sources:
- All files in transactions/ directory
- Include legacy data from archive/2023/
- Combine using pattern ["transactions/*.csv", "archive/2023/*.csv"]
- Generate monthly spending report
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

#### `load_multiple_csvs`
- **Usage**: "Load all CSV files matching data/*.csv pattern"
- **Features**: Glob patterns, file lists, schema unification, filename tracking

#### `discover_csv_files`
- **Usage**: "What CSV files are available in the reports/ directory?"
- **Features**: File discovery, metadata, size and modification info

## Glob Pattern Reference

Multi-CSV tools support glob patterns for flexible file matching:

| Pattern | Description | Example |
|---------|-------------|---------|
| `*` | Matches any characters | `sales_*.csv` matches `sales_q1.csv`, `sales_2024.csv` |
| `**` | Matches directories recursively | `data/**/*.csv` finds CSVs at any depth in `data/` |
| `?` | Matches single character | `report_?.csv` matches `report_1.csv`, `report_A.csv` |
| `[abc]` | Matches any character in brackets | `sales_[123].csv` matches `sales_1.csv`, `sales_2.csv`, `sales_3.csv` |
| `[a-z]` | Matches character range | `file_[a-c].csv` matches `file_a.csv`, `file_b.csv`, `file_c.csv` |

**Example Patterns:**
- `*.csv` - All CSV files in current directory
- `data/*.csv` - All CSV files in data directory
- `reports/**/*.csv` - All CSV files in reports directory and subdirectories
- `sales_2024_*.csv` - All sales files for 2024
- `**/monthly_[0-9][0-9].csv` - Monthly files with 2-digit numbers, anywhere in directory tree

**Note:** The `?` wildcard is not supported for S3/remote file reads due to URL encoding issues.

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

### 5. Multi-CSV Best Practices
When working with multiple CSV files:
- **Use `union_by_name=true`** when files have different column orders or missing columns
- **Enable `filename=true`** to track which file each row came from
- **Use `discover_csv_files`** first to see what files match your pattern
- **Start with a small pattern** to test schema compatibility before loading all files
- **Use descriptive table names** when loading multiple datasets

**Examples:**
- ✅ "Load all sales files with union_by_name and filename tracking"
- ✅ "First discover what CSV files are in /data/reports/ then load them"
- ✅ "Load quarterly files and analyze by source file"

## Troubleshooting

### Server Not Found
If Claude Code can't find the MCP server:

**Local Installation:**
1. Check that the path in your configuration is absolute and correct
2. Verify Node.js is installed and accessible
3. Restart Claude Code after configuration changes

**Docker Installation:**
1. Ensure Docker image is built: `docker build -t quack-mcp .`
2. Check Docker is running and accessible
3. Verify volume mount paths are correct and absolute
4. Restart Claude Code after configuration changes

### Permission Errors

**Local Installation:**
1. Ensure the CSV file path is correct and accessible
2. Check file permissions
3. Use absolute paths for CSV files

**Docker Installation:**
1. Ensure CSV files are mounted as volumes in Docker configuration
2. Check volume mount paths are correct: `-v /host/path:/app/csv-data:ro`
3. Verify Docker has permission to access the mounted directories
4. Use paths relative to container mount points (e.g., `/app/csv-data/file.csv`)

### Container Issues

**Docker-specific problems:**
1. **Container won't start**: Check Docker logs with `docker logs <container-id>`
2. **File not found**: Ensure CSV files are properly mounted as volumes
3. **Permission denied**: Check file permissions on host system
4. **Memory issues**: DuckDB requires sufficient container memory for large CSV files

### SQL Errors
If queries fail:
1. Check the table name (use `list_tables` to verify)
2. Verify column names with `describe_table`
3. Remember DuckDB uses standard SQL syntax

### Performance Issues
For large CSV files:

**Both Local and Docker:**
1. DuckDB is optimized for analytics but very large files may take time to load
2. Consider using `LIMIT` clauses for initial exploration
3. The server loads data into memory - ensure sufficient RAM

**Docker-specific:**
1. Increase container memory limits if needed
2. Consider mounting CSV files read-only for better performance

## MCP Client Configuration

### Local Installation
For other MCP clients, add to your configuration:

```json
{
  "mcpServers": {
    "quack-mcp": {
      "command": "node",
      "args": ["/path/to/quack-mcp/src/index.ts"]
    }
  }
}
```

### Docker Installation
For containerized deployment with other MCP clients:

```json
{
  "mcpServers": {
    "quack-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/csv/files:/app/csv-data:ro",
        "quack-mcp"
      ]
    }
  }
}
```

Or with docker-compose:

```json
{
  "mcpServers": {
    "quack-mcp": {
      "command": "docker-compose",
      "args": [
        "-f", "/path/to/quack-mcp/docker-compose.yml",
        "run", "--rm", "quack-mcp"
      ],
      "cwd": "/path/to/quack-mcp"
    }
  }
}
```
