#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ErrorCode, ListToolsRequestSchema, McpError, } from '@modelcontextprotocol/sdk/types.js';
import Database from 'duckdb';
import fs from 'fs/promises';
import path from 'path';
class QuackMCPServer {
    server;
    db;
    loadedTables = new Map();
    constructor() {
        this.server = new Server({
            name: 'quack-mcp',
            version: '1.0.0',
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.db = new Database.Database(':memory:');
        this.setupToolHandlers();
    }
    setupToolHandlers() {
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                {
                    name: 'load_csv',
                    description: 'Load a CSV file into DuckDB for analysis',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            file_path: {
                                type: 'string',
                                description: 'Path to the CSV file to load',
                            },
                            table_name: {
                                type: 'string',
                                description: 'Name for the table (optional, defaults to filename)',
                            },
                            delimiter: {
                                type: 'string',
                                description: 'CSV delimiter (default: ",")',
                                default: ',',
                            },
                            header: {
                                type: 'boolean',
                                description: 'Whether CSV has header row (default: true)',
                                default: true,
                            },
                        },
                        required: ['file_path'],
                    },
                },
                {
                    name: 'query_csv',
                    description: 'Execute SQL query on loaded CSV data',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            query: {
                                type: 'string',
                                description: 'SQL query to execute',
                            },
                        },
                        required: ['query'],
                    },
                },
                {
                    name: 'describe_table',
                    description: 'Get schema information for a loaded table',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            table_name: {
                                type: 'string',
                                description: 'Name of the table to describe',
                            },
                        },
                        required: ['table_name'],
                    },
                },
                {
                    name: 'list_tables',
                    description: 'List all loaded tables',
                    inputSchema: {
                        type: 'object',
                        properties: {},
                    },
                },
                {
                    name: 'analyze_csv',
                    description: 'Perform basic statistical analysis on CSV data',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            table_name: {
                                type: 'string',
                                description: 'Name of the table to analyze',
                            },
                            columns: {
                                type: 'array',
                                items: { type: 'string' },
                                description: 'Specific columns to analyze (optional)',
                            },
                        },
                        required: ['table_name'],
                    },
                },
                {
                    name: 'optimize_expenses',
                    description: 'Analyze credit card spending data to identify expense optimization opportunities with actionable recommendations and savings estimates',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            table_name: {
                                type: 'string',
                                description: 'Name of the table containing transaction data',
                            },
                            amount_column: {
                                type: 'string',
                                description: 'Name of the column containing transaction amounts',
                                default: 'Amount',
                            },
                            name_column: {
                                type: 'string',
                                description: 'Name of the column containing merchant/transaction names',
                                default: 'Name',
                            },
                            date_column: {
                                type: 'string',
                                description: 'Name of the column containing transaction dates',
                                default: 'Date',
                            },
                        },
                        required: ['table_name'],
                    },
                },
            ],
        }));
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            switch (request.params.name) {
                case 'load_csv':
                    return await this.loadCSV(request.params.arguments);
                case 'query_csv':
                    return await this.queryCSV(request.params.arguments);
                case 'describe_table':
                    return await this.describeTable(request.params.arguments);
                case 'list_tables':
                    return await this.listTables();
                case 'analyze_csv':
                    return await this.analyzeCSV(request.params.arguments);
                case 'optimize_expenses':
                    return await this.optimizeExpenses(request.params.arguments);
                default:
                    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
            }
        });
    }
    async loadCSV(args) {
        try {
            const { file_path, table_name, delimiter = ',', header = true } = args;
            // Check if file exists
            await fs.access(file_path);
            const tableName = table_name || path.basename(file_path, path.extname(file_path)).replace(/[^a-zA-Z0-9_]/g, '_');
            // Try simple CSV loading with properly escaped path
            const escapedPath = file_path.replace(/'/g, "''");
            const query = `
        CREATE OR REPLACE TABLE "${tableName}" AS 
        SELECT * FROM read_csv('${escapedPath}', 
          header=${header}
        )
      `;
            console.error('Executing query:', query);
            await this.executeQuery(query);
            this.loadedTables.set(tableName, file_path);
            // Automatically inspect the schema and data
            const schemaInfo = await this.inspectTableSchema(tableName);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Successfully loaded CSV file "${file_path}" as table "${tableName}"\n\n${schemaInfo}`,
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Failed to load CSV: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    async queryCSV(args) {
        try {
            const { query } = args;
            const result = await this.executeQuery(query);
            return {
                content: [
                    {
                        type: 'text',
                        text: this.safeStringify(result, null, 2),
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Query failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    async describeTable(args) {
        try {
            const { table_name } = args;
            const result = await this.executeQuery(`DESCRIBE ${table_name}`);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Schema for table "${table_name}":\n${this.safeStringify(result, null, 2)}`,
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Failed to describe table: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    async listTables() {
        try {
            const tables = Array.from(this.loadedTables.entries()).map(([name, path]) => ({
                table_name: name,
                file_path: path,
            }));
            return {
                content: [
                    {
                        type: 'text',
                        text: `Loaded tables:\n${this.safeStringify(tables, null, 2)}`,
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Failed to list tables: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    async analyzeCSV(args) {
        try {
            const { table_name, columns } = args;
            let query;
            if (columns && columns.length > 0) {
                const columnStats = columns
                    .map((col) => `
            COUNT(${col}) as ${col}_count,
            COUNT(DISTINCT ${col}) as ${col}_unique,
            MIN(${col}) as ${col}_min,
            MAX(${col}) as ${col}_max,
            AVG(TRY_CAST(${col} AS DOUBLE)) as ${col}_avg
          `)
                    .join(',');
                query = `SELECT ${columnStats} FROM ${table_name}`;
            }
            else {
                query = `
          SELECT 
            COUNT(*) as total_rows,
            COUNT(*) - COUNT(*) as missing_values
          FROM ${table_name}
        `;
            }
            const result = await this.executeQuery(query);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Analysis for table "${table_name}":\n${this.safeStringify(result, null, 2)}`,
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Analysis failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    async optimizeExpenses(args) {
        try {
            const { table_name, amount_column = 'Amount', name_column = 'Name', date_column = 'Date' } = args;
            const report = await this.generateExpenseOptimizationReport(table_name, amount_column, name_column, date_column);
            return {
                content: [
                    {
                        type: 'text',
                        text: report,
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Expense optimization failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    async inspectTableSchema(tableName) {
        try {
            // Get schema information
            const schema = await this.executeQuery(`DESCRIBE ${tableName}`);
            // Get row count
            const countResult = await this.executeQuery(`SELECT COUNT(*) as row_count FROM ${tableName}`);
            const rowCount = countResult[0]?.row_count || 0;
            // Get sample data (first 3 rows)
            const sampleData = await this.executeQuery(`SELECT * FROM ${tableName} LIMIT 3`);
            // Format the inspection result
            let inspection = `📊 TABLE INSPECTION: "${tableName}"\n`;
            inspection += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
            inspection += `📈 Total Rows: ${rowCount.toLocaleString()}\n\n`;
            inspection += `🏗️ SCHEMA:\n`;
            schema.forEach((col, index) => {
                const icon = this.getColumnTypeIcon(col.column_type);
                inspection += `  ${index + 1}. ${icon} ${col.column_name} (${col.column_type})${col.null ? ' - nullable' : ''}\n`;
            });
            if (sampleData.length > 0) {
                inspection += `\n👀 SAMPLE DATA (first ${sampleData.length} rows):\n`;
                inspection += this.formatSampleData(sampleData, schema);
            }
            inspection += `\n💡 Ready for analysis! Use query_csv to explore the data with SQL.`;
            return inspection;
        }
        catch (error) {
            return `Schema inspection failed: ${error instanceof Error ? error.message : String(error)}`;
        }
    }
    getColumnTypeIcon(type) {
        const lowerType = type.toLowerCase();
        if (lowerType.includes('int') || lowerType.includes('bigint') || lowerType.includes('double') || lowerType.includes('decimal'))
            return '🔢';
        if (lowerType.includes('varchar') || lowerType.includes('text') || lowerType.includes('string'))
            return '📝';
        if (lowerType.includes('date') || lowerType.includes('timestamp'))
            return '📅';
        if (lowerType.includes('bool'))
            return '✅';
        return '📊';
    }
    formatSampleData(data, schema) {
        if (data.length === 0)
            return '  No data available\n';
        let result = '';
        const columnNames = schema.map(col => col.column_name);
        // Create header
        result += '  ' + columnNames.map(name => name.padEnd(15)).join(' | ') + '\n';
        result += '  ' + columnNames.map(() => '─'.repeat(15)).join('─┼─') + '\n';
        // Add data rows
        data.forEach((row) => {
            const values = columnNames.map(name => {
                const value = row[name];
                const strValue = value === null || value === undefined ? 'NULL' : String(value);
                return strValue.length > 15 ? strValue.substring(0, 12) + '...' : strValue.padEnd(15);
            });
            result += '  ' + values.join(' | ') + '\n';
        });
        return result;
    }
    executeQuery(query) {
        return new Promise((resolve, reject) => {
            this.db.all(query, (err, rows) => {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(rows);
                }
            });
        });
    }
    safeStringify(obj, replacer, space) {
        return JSON.stringify(obj, (key, value) => {
            if (typeof value === 'bigint') {
                // Convert BigInt to number if it fits in safe integer range
                if (value <= Number.MAX_SAFE_INTEGER && value >= Number.MIN_SAFE_INTEGER) {
                    return Number(value);
                }
                // Otherwise convert to string with suffix to indicate it was a BigInt
                return value.toString() + 'n';
            }
            return replacer ? replacer(key, value) : value;
        }, space);
    }
    async generateExpenseOptimizationReport(tableName, amountCol, nameCol, dateCol) {
        // 1. Monthly expense summary
        const monthlyQuery = `
      SELECT 
        strftime('%Y-%m', ${dateCol}) as month,
        COUNT(*) as transaction_count,
        ROUND(SUM(CASE WHEN ${amountCol} < 0 THEN ABS(${amountCol}) ELSE 0 END), 2) as total_expenses,
        ROUND(MAX(CASE WHEN ${amountCol} < 0 THEN ABS(${amountCol}) ELSE 0 END), 2) as largest_expense
      FROM ${tableName} 
      GROUP BY strftime('%Y-%m', ${dateCol})
      ORDER BY month
    `;
        // 2. Subscription analysis (recurring charges)
        const subscriptionQuery = `
      SELECT 
        ${nameCol} as name,
        ROUND(ABS(${amountCol}), 2) as amount,
        COUNT(*) as frequency,
        ROUND(SUM(ABS(${amountCol})), 2) as total_spent,
        MIN(${dateCol}) as first_charge,
        MAX(${dateCol}) as last_charge
      FROM ${tableName} 
      WHERE ${amountCol} < 0 
      GROUP BY ${nameCol}, ROUND(ABS(${amountCol}), 2)
      HAVING COUNT(*) >= 2 AND ABS(${amountCol}) < 100
      ORDER BY frequency DESC, total_spent DESC
      LIMIT 10
    `;
        // 3. Small frequent purchases analysis
        const smallPurchasesQuery = `
      SELECT 
        CASE 
          WHEN ${nameCol} LIKE '%COFFEE%' OR ${nameCol} LIKE '%STARBUCKS%' OR ${nameCol} LIKE '%DUNKIN%' THEN 'Coffee Shops'
          WHEN ${nameCol} LIKE '%CUSTARD%' OR ${nameCol} LIKE '%ICE CREAM%' THEN 'Ice Cream/Desserts'
          WHEN ${nameCol} LIKE '%RESTAURANT%' OR ${nameCol} LIKE '%GRILL%' OR ${nameCol} LIKE '%PIZZA%' OR ${nameCol} LIKE '%TACO%' OR ${nameCol} LIKE '%CULVERS%' THEN 'Restaurants'
          WHEN ${nameCol} LIKE '%GAS%' OR ${nameCol} LIKE '%FUEL%' OR ${nameCol} LIKE '%SHELL%' THEN 'Gas Stations'
          WHEN ABS(${amountCol}) < 10 THEN 'Small Purchases (<$10)'
          WHEN ABS(${amountCol}) BETWEEN 10 AND 25 THEN 'Medium Purchases ($10-25)'
          ELSE 'Other'
        END as category,
        COUNT(*) as transaction_count,
        ROUND(SUM(ABS(${amountCol})), 2) as total_spent,
        ROUND(AVG(ABS(${amountCol})), 2) as avg_amount
      FROM ${tableName} 
      WHERE ${amountCol} < 0 AND ABS(${amountCol}) < 50
      GROUP BY category
      HAVING transaction_count >= 3
      ORDER BY total_spent DESC
    `;
        // 4. Grocery spending analysis
        const groceryQuery = `
      SELECT 
        strftime('%Y-%m', ${dateCol}) as month,
        COUNT(*) as grocery_trips,
        ROUND(SUM(ABS(${amountCol})), 2) as total_grocery_spend,
        ROUND(AVG(ABS(${amountCol})), 2) as avg_per_trip,
        ROUND(MIN(ABS(${amountCol})), 2) as min_spend,
        ROUND(MAX(ABS(${amountCol})), 2) as max_spend
      FROM ${tableName} 
      WHERE ${amountCol} < 0 AND (${nameCol} LIKE '%KROGER%' OR ${nameCol} LIKE '%TARGET%')
      GROUP BY strftime('%Y-%m', ${dateCol})
      ORDER BY month
    `;
        // Execute all queries
        const [monthlyData, subscriptions, smallPurchases, groceryData] = await Promise.all([
            this.executeQuery(monthlyQuery),
            this.executeQuery(subscriptionQuery),
            this.executeQuery(smallPurchasesQuery),
            this.executeQuery(groceryQuery)
        ]);
        // Generate the formatted report
        return this.formatOptimizationReport(monthlyData, subscriptions, smallPurchases, groceryData);
    }
    formatOptimizationReport(monthlyData, subscriptions, smallPurchases, groceryData) {
        let report = '## 💰 Expense Optimization Report\n\n';
        // Monthly summary
        report += '### 📊 Monthly Spending Overview\n';
        report += '| Month | Total Expenses | Largest Purchase | Transactions |\n';
        report += '|-------|---------------|------------------|-------------|\n';
        monthlyData.forEach(month => {
            report += `| ${month.month} | $${month.total_expenses?.toLocaleString() || '0'} | $${month.largest_expense?.toLocaleString() || '0'} | ${month.transaction_count || 0} |\n`;
        });
        report += '\n';
        // High-impact optimization opportunities
        report += '### 🎯 HIGH-IMPACT Opportunities (Save $100+ monthly)\n\n';
        // Subscription analysis
        if (subscriptions.length > 0) {
            const subscriptionTotal = subscriptions.reduce((sum, sub) => sum + (sub.total_spent || 0), 0);
            const monthlySubTotal = subscriptionTotal / 3; // Assuming 3-month period
            report += `**1. Subscription Audit** - Potential savings: $${Math.round(monthlySubTotal * 0.3)}/month\n`;
            report += '```\n';
            subscriptions.slice(0, 5).forEach(sub => {
                report += `• ${sub.name}: $${sub.amount} × ${sub.frequency} times = $${sub.total_spent}\n`;
            });
            report += '```\n';
            report += '**Actions**: Cancel unused services, switch to annual plans for discounts\n\n';
        }
        // Small purchases analysis
        const coffeeData = smallPurchases.find(cat => cat.category === 'Coffee Shops');
        const treatData = smallPurchases.find(cat => cat.category === 'Ice Cream/Desserts');
        const restaurantData = smallPurchases.find(cat => cat.category === 'Restaurants');
        if (coffeeData || treatData) {
            const coffeeMonthly = (coffeeData?.total_spent || 0) / 3;
            const treatMonthly = (treatData?.total_spent || 0) / 3;
            const totalSavings = Math.round((coffeeMonthly + treatMonthly) * 0.7);
            report += `**2. Coffee & Treats** - Potential savings: $${totalSavings}/month\n`;
            if (coffeeData)
                report += `• Coffee shops: ${coffeeData.transaction_count} visits = $${Math.round(coffeeMonthly)}/month\n`;
            if (treatData)
                report += `• Treats/desserts: ${treatData.transaction_count} visits = $${Math.round(treatMonthly)}/month\n`;
            report += '**Actions**: Make coffee at home, limit treats to weekends\n\n';
        }
        if (restaurantData) {
            const restaurantMonthly = restaurantData.total_spent / 3;
            const restaurantSavings = Math.round(restaurantMonthly * 0.4);
            report += `**3. Dining Out** - Potential savings: $${restaurantSavings}/month\n`;
            report += `• ${restaurantData.transaction_count} restaurant visits = $${Math.round(restaurantMonthly)}/month\n`;
            report += '**Actions**: Limit to 1-2 restaurant visits per week, meal prep\n\n';
        }
        // Medium-impact opportunities
        report += '### 🔍 MEDIUM-IMPACT Opportunities (Save $25-100 monthly)\n\n';
        // Grocery optimization
        if (groceryData.length > 0) {
            const avgGrocerySpend = groceryData.reduce((sum, month) => sum + (month.total_grocery_spend || 0), 0) / groceryData.length;
            const potentialSavings = Math.round(avgGrocerySpend * 0.15);
            report += `**4. Grocery Optimization** - Potential savings: $${potentialSavings}/month\n`;
            report += '```\n';
            groceryData.forEach(month => {
                report += `${month.month}: ${month.grocery_trips} trips, $${Math.round(month.avg_per_trip || 0)} avg/trip\n`;
            });
            report += '```\n';
            report += '**Actions**: Plan weekly meals, set $75 budget per trip, use store apps for coupons\n\n';
        }
        // Small purchases breakdown
        const smallPurchasesTotal = smallPurchases.reduce((sum, cat) => sum + (cat.total_spent || 0), 0);
        if (smallPurchasesTotal > 0) {
            report += `**5. Small Purchase Optimization** - Potential savings: $${Math.round(smallPurchasesTotal * 0.2 / 3)}/month\n`;
            report += '```\n';
            smallPurchases.slice(0, 4).forEach(cat => {
                report += `• ${cat.category}: ${cat.transaction_count} purchases = $${cat.total_spent}\n`;
            });
            report += '```\n';
            report += '**Actions**: Use 24-hour rule for non-essentials, batch small purchases\n\n';
        }
        // Summary
        const totalPotentialSavings = Math.round((subscriptions.reduce((sum, sub) => sum + sub.total_spent, 0) * 0.3 / 3) +
            ((coffeeData?.total_spent || 0) + (treatData?.total_spent || 0)) * 0.7 / 3 +
            ((restaurantData?.total_spent || 0) * 0.4 / 3) +
            (smallPurchasesTotal * 0.2 / 3));
        report += `### 📈 **Total Monthly Savings Potential: $${totalPotentialSavings}+**\n\n`;
        report += '**Implementation Priority**:\n';
        report += '1. **Subscription audit** (easiest, immediate impact)\n';
        report += '2. **Coffee routine change** (highest ROI)\n';
        report += '3. **Meal planning** (reduces grocery + restaurant costs)\n';
        report += '4. **Small purchase discipline** (builds long-term habits)\n\n';
        report += '💡 **Tip**: Start with one category per month to build sustainable habits.';
        return report;
    }
    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('Quack MCP Server running on stdio');
    }
}
// Export the class for testing
export { QuackMCPServer };
const server = new QuackMCPServer();
if (process.argv[1] === import.meta.url.replace('file://', '')) {
    server.run().catch(console.error);
}
