# Expense Optimization Tool

## Overview

The `optimize_expenses` tool analyzes credit card or bank transaction data to identify specific expense optimization opportunities with actionable recommendations and realistic savings estimates.

## Features

- 📊 **Monthly spending analysis** with trends and largest purchases
- 🔄 **Subscription detection** - automatically finds recurring charges
- ☕ **Small purchase categorization** - groups coffee, dining, treats, etc.
- 🛒 **Grocery spending optimization** - analyzes shopping patterns
- 💰 **Savings estimates** - calculates realistic monthly savings potential
- 📋 **Action prioritization** - orders recommendations by impact vs. effort

## Requirements

### Data Format
Your CSV data must contain these columns (column names are configurable):
- **Amount/Transaction Amount**: Numeric values (negative for expenses, positive for income)
- **Name/Merchant/Description**: Text description of the merchant or transaction
- **Date**: Date of the transaction (YYYY-MM-DD or similar format)

### Example Data Structure
```csv
Date,Name,Amount
2025-05-01,STARBUCKS COFFEE,"-4.95"
2025-05-01,KROGER GROCERY,"-125.67"
2025-05-02,NETFLIX.COM,"-15.99"
2025-05-03,TARGET.COM,"-89.42"
```

## Usage

### Basic Usage
```javascript
// First, load your transaction data
mcp__quack-mcp__load_csv({
  file_path: "./transactions.csv"
})

// Then run the expense optimization analysis
mcp__quack-mcp__optimize_expenses({
  table_name: "transactions"
})
```

### Advanced Usage with Custom Column Names
```javascript
mcp__quack-mcp__optimize_expenses({
  table_name: "my_transactions",
  amount_column: "transaction_amount",
  name_column: "merchant_name", 
  date_column: "transaction_date"
})
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `table_name` | string | ✅ Yes | - | Name of the loaded table containing transaction data |
| `amount_column` | string | ❌ No | `"Amount"` | Column containing transaction amounts |
| `name_column` | string | ❌ No | `"Name"` | Column containing merchant/transaction descriptions |
| `date_column` | string | ❌ No | `"Date"` | Column containing transaction dates |

## Output Format

The tool generates a comprehensive markdown report with these sections:

### 📊 Monthly Spending Overview
- Total expenses by month
- Largest purchases per month
- Transaction counts
- Spending trends

### 🎯 HIGH-IMPACT Opportunities (Save $100+ monthly)
- **Subscription Audit**: Recurring charges analysis
- **Coffee & Treats**: Small frequent purchases
- **Dining Out**: Restaurant spending patterns

### 🔍 MEDIUM-IMPACT Opportunities (Save $25-100 monthly)
- **Grocery Optimization**: Shopping frequency and amounts
- **Small Purchase Optimization**: Impulse buying patterns

### 📈 Summary
- Total monthly savings potential
- Implementation priority order
- Actionable next steps

## Analysis Logic

### Subscription Detection
Automatically identifies recurring charges by:
- Finding transactions with identical merchants and amounts
- Requiring 2+ occurrences for subscription classification
- Filtering amounts under $100 to focus on typical subscription costs

### Category Classification
Merchants are automatically categorized using pattern matching:
- **Coffee Shops**: Starbucks, Dunkin, local coffee shops
- **Restaurants**: Dining establishments, fast food
- **Groceries**: Major grocery chains (Kroger, Target, etc.)
- **Gas Stations**: Fuel purchases and convenience items
- **Entertainment**: Streaming services, apps, games

### Savings Calculations
Realistic savings percentages applied:
- **Subscriptions**: 30% (cancel unused, annual plans)
- **Coffee/Treats**: 70% (home brewing, weekend limits)
- **Dining Out**: 40% (meal planning, cooking more)
- **Groceries**: 15% (better planning, coupons)
- **Small Purchases**: 20% (impulse control, batching)

## Sample Report Output

```markdown
## 💰 Expense Optimization Report

### 📊 Monthly Spending Overview
| Month | Total Expenses | Largest Purchase | Transactions |
|-------|---------------|------------------|-------------|
| 2025-05 | $5,653.92 | $385.48 | 123 |
| 2025-06 | $5,804.50 | $256.00 | 106 |

### 🎯 HIGH-IMPACT Opportunities (Save $100+ monthly)

**1. Subscription Audit** - Potential savings: $45/month
• Netflix: $15.99 × 3 times = $47.97
• Spotify: $9.99 × 3 times = $29.97
**Actions**: Cancel unused services, switch to annual plans

### 📈 **Total Monthly Savings Potential: $243+**

**Implementation Priority**:
1. **Subscription audit** (easiest, immediate impact)
2. **Coffee routine change** (highest ROI)
3. **Meal planning** (reduces multiple categories)
```

## Best Practices

### Data Preparation
1. **Clean your data**: Remove duplicates and test transactions
2. **Consistent formatting**: Ensure dates are properly formatted
3. **Expense classification**: Make sure expenses are negative values
4. **Complete time period**: Include at least 2-3 months of data for patterns

### Using the Results
1. **Start with high-impact items**: Focus on subscriptions first
2. **Track implementation**: Monitor changes month-over-month
3. **Realistic expectations**: Aim for 60-70% of estimated savings
4. **Gradual changes**: Implement one category at a time

### Interpreting Savings Estimates
- **Conservative approach**: Estimates assume moderate behavior changes
- **Individual variation**: Your actual savings may vary based on commitment
- **Compound effects**: Some changes (meal planning) affect multiple categories
- **Timeline**: Full savings typically achieved over 2-3 months

## Common Use Cases

### Personal Finance Review
```javascript
// Monthly expense review
mcp__quack-mcp__optimize_expenses({
  table_name: "credit_card"
})
```

### Family Budget Analysis
```javascript
// Analyze household spending
mcp__quack-mcp__optimize_expenses({
  table_name: "family_expenses",
  amount_column: "amount",
  name_column: "description"
})
```

### Business Expense Audit
```javascript
// Review business spending patterns
mcp__quack-mcp__optimize_expenses({
  table_name: "business_expenses",
  amount_column: "expense_amount",
  name_column: "vendor_name",
  date_column: "expense_date"
})
```

## Troubleshooting

### Common Issues

**No subscriptions detected**
- Ensure you have 2+ months of data
- Check that recurring charges have identical amounts
- Verify merchant names are consistent

**Low savings estimates**
- May indicate already optimized spending
- Try analyzing longer time periods
- Consider data completeness

**Missing categories**
- Add custom merchant patterns in the code
- Check spelling variations in merchant names
- Verify expense amounts are negative

### Error Messages

**"Table not found"**
- Load your CSV data first using `load_csv`
- Check table name spelling

**"Column not found"**
- Verify column names match your data
- Use `describe_table` to see available columns

**"No expense data found"**
- Ensure expenses are negative values
- Check date format compatibility
- Verify data isn't filtered out

## Integration Examples

### With Claude Code
```bash
# Load data and analyze in one session
claude-code "Load ./expenses.csv and run expense optimization analysis"
```

### With Other MCP Tools
```javascript
// Combine with other analysis
mcp__quack-mcp__analyze_csv({ table_name: "expenses" })
mcp__quack-mcp__optimize_expenses({ table_name: "expenses" })
```

## Contributing

To extend the tool's capabilities:

1. **Add new categories**: Modify the categorization logic in `smallPurchasesQuery`
2. **Adjust savings rates**: Update percentages in `formatOptimizationReport`
3. **Custom analysis**: Add new queries to `generateExpenseOptimizationReport`

## Support

For issues or feature requests:
- Check data format requirements
- Verify all required columns exist
- Test with sample data first
- Review error messages for specific guidance