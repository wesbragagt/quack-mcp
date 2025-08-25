"""Specialized analytics tools implementation."""

from typing import TYPE_CHECKING, Any

from mcp.types import TextContent

from ..exceptions import QueryError, TableNotFoundError
from ..models import DetectAnomaliesArgs, OptimizeExpensesArgs

if TYPE_CHECKING:
    from ..server import QuackMCPServer


class SpecializedTools:
    """Handles specialized analytics operations."""

    def __init__(self, server: "QuackMCPServer") -> None:
        """Initialize specialized tools."""
        self.server = server

    async def optimize_expenses(self, args: OptimizeExpensesArgs) -> list[TextContent]:
        """Analyze credit card spending data for optimization opportunities."""
        try:
            # Check if table exists
            loaded_tables = self.server.get_loaded_tables()
            if args.table_name not in loaded_tables:
                raise TableNotFoundError(args.table_name)

            report = await self._generate_expense_optimization_report(
                args.table_name, args.amount_column, args.name_column, args.date_column
            )

            return [TextContent(type="text", text=report)]

        except TableNotFoundError:
            raise
        except Exception as e:
            raise QueryError(f"Expense optimization failed: {e!s}")

    async def detect_anomalies(self, args: DetectAnomaliesArgs) -> list[TextContent]:
        """Detect anomalies and irregularities in dataset."""
        try:
            # Check if table exists
            loaded_tables = self.server.get_loaded_tables()
            if args.table_name not in loaded_tables:
                raise TableNotFoundError(args.table_name)

            report = await self._generate_anomaly_report(
                args.table_name,
                args.severity_threshold,
                args.focus_columns or [],
                args.anomaly_types,
            )

            return [TextContent(type="text", text=report)]

        except TableNotFoundError:
            raise
        except Exception as e:
            raise QueryError(f"Anomaly detection failed: {e!s}")

    async def _generate_expense_optimization_report(
        self, table_name: str, amount_col: str, name_col: str, date_col: str
    ) -> str:
        """Generate expense optimization report."""

        # 1. Monthly expense summary
        monthly_query = f"""
            SELECT 
                strftime('%Y-%m', {date_col}) as month,
                COUNT(*) as transaction_count,
                ROUND(SUM(CASE WHEN {amount_col} < 0 THEN ABS({amount_col}) ELSE 0 END), 2) as total_expenses,
                ROUND(MAX(CASE WHEN {amount_col} < 0 THEN ABS({amount_col}) ELSE 0 END), 2) as largest_expense
            FROM {table_name} 
            GROUP BY strftime('%Y-%m', {date_col})
            ORDER BY month
        """

        # 2. Subscription analysis (recurring charges)
        subscription_query = f"""
            SELECT 
                {name_col} as name,
                ROUND(ABS({amount_col}), 2) as amount,
                COUNT(*) as frequency,
                ROUND(SUM(ABS({amount_col})), 2) as total_spent,
                MIN({date_col}) as first_charge,
                MAX({date_col}) as last_charge
            FROM {table_name} 
            WHERE {amount_col} < 0 
            GROUP BY {name_col}, ROUND(ABS({amount_col}), 2)
            HAVING COUNT(*) >= 2 AND ABS({amount_col}) < 100
            ORDER BY frequency DESC, total_spent DESC
            LIMIT 10
        """

        # 3. Small frequent purchases analysis
        small_purchases_query = f"""
            SELECT 
                CASE 
                    WHEN {name_col} LIKE '%COFFEE%' OR {name_col} LIKE '%STARBUCKS%' OR {name_col} LIKE '%DUNKIN%' THEN 'Coffee Shops'
                    WHEN {name_col} LIKE '%CUSTARD%' OR {name_col} LIKE '%ICE CREAM%' THEN 'Ice Cream/Desserts'
                    WHEN {name_col} LIKE '%RESTAURANT%' OR {name_col} LIKE '%GRILL%' OR {name_col} LIKE '%PIZZA%' OR {name_col} LIKE '%TACO%' OR {name_col} LIKE '%CULVERS%' THEN 'Restaurants'
                    WHEN {name_col} LIKE '%GAS%' OR {name_col} LIKE '%FUEL%' OR {name_col} LIKE '%SHELL%' THEN 'Gas Stations'
                    WHEN ABS({amount_col}) < 10 THEN 'Small Purchases (<$10)'
                    WHEN ABS({amount_col}) BETWEEN 10 AND 25 THEN 'Medium Purchases ($10-25)'
                    ELSE 'Other'
                END as category,
                COUNT(*) as transaction_count,
                ROUND(SUM(ABS({amount_col})), 2) as total_spent,
                ROUND(AVG(ABS({amount_col})), 2) as avg_amount
            FROM {table_name} 
            WHERE {amount_col} < 0 AND ABS({amount_col}) < 50
            GROUP BY category
            HAVING transaction_count >= 3
            ORDER BY total_spent DESC
        """

        # 4. Grocery spending analysis
        grocery_query = f"""
            SELECT 
                strftime('%Y-%m', {date_col}) as month,
                COUNT(*) as grocery_trips,
                ROUND(SUM(ABS({amount_col})), 2) as total_grocery_spend,
                ROUND(AVG(ABS({amount_col})), 2) as avg_per_trip,
                ROUND(MIN(ABS({amount_col})), 2) as min_spend,
                ROUND(MAX(ABS({amount_col})), 2) as max_spend
            FROM {table_name} 
            WHERE {amount_col} < 0 AND ({name_col} LIKE '%KROGER%' OR {name_col} LIKE '%TARGET%')
            GROUP BY strftime('%Y-%m', {date_col})
            ORDER BY month
        """

        # Execute all queries
        monthly_data, subscriptions, small_purchases, grocery_data = await asyncio.gather(
            self.server.execute_query(monthly_query),
            self.server.execute_query(subscription_query),
            self.server.execute_query(small_purchases_query),
            self.server.execute_query(grocery_query),
        )

        return self._format_optimization_report(monthly_data, subscriptions, small_purchases, grocery_data)

    def _format_optimization_report(
        self,
        monthly_data: list[dict[str, Any]],
        subscriptions: list[dict[str, Any]],
        small_purchases: list[dict[str, Any]],
        grocery_data: list[dict[str, Any]],
    ) -> str:
        """Format the expense optimization report."""
        report = "## 💰 Expense Optimization Report\n\n"

        # Monthly summary
        report += "### 📊 Monthly Spending Overview\n"
        report += "| Month | Total Expenses | Largest Purchase | Transactions |\n"
        report += "|-------|---------------|------------------|-------------|\n"
        for month in monthly_data:
            total_expenses = month.get("total_expenses", 0) or 0
            largest_expense = month.get("largest_expense", 0) or 0
            transaction_count = month.get("transaction_count", 0) or 0
            report += f"| {month['month']} | ${total_expenses:,.2f} | ${largest_expense:,.2f} | {transaction_count} |\n"
        report += "\n"

        # High-impact optimization opportunities
        report += "### 🎯 HIGH-IMPACT Opportunities (Save $100+ monthly)\n\n"

        # Subscription analysis
        if subscriptions:
            subscription_total = sum(sub.get("total_spent", 0) or 0 for sub in subscriptions)
            monthly_sub_total = subscription_total / 3  # Assuming 3-month period

            report += f"**1. Subscription Audit** - Potential savings: ${monthly_sub_total * 0.3:.0f}/month\n"
            report += "```\n"
            for sub in subscriptions[:5]:
                name = sub.get("name", "Unknown")
                amount = sub.get("amount", 0) or 0
                frequency = sub.get("frequency", 0) or 0
                total_spent = sub.get("total_spent", 0) or 0
                report += f"• {name}: ${amount:.2f} × {frequency} times = ${total_spent:.2f}\n"
            report += "```\n"
            report += "**Actions**: Cancel unused services, switch to annual plans for discounts\n\n"

        # Small purchases analysis
        coffee_data = next((cat for cat in small_purchases if cat.get("category") == "Coffee Shops"), None)
        treat_data = next((cat for cat in small_purchases if cat.get("category") == "Ice Cream/Desserts"), None)
        restaurant_data = next((cat for cat in small_purchases if cat.get("category") == "Restaurants"), None)

        if coffee_data or treat_data:
            coffee_monthly = (coffee_data.get("total_spent", 0) or 0) / 3 if coffee_data else 0
            treat_monthly = (treat_data.get("total_spent", 0) or 0) / 3 if treat_data else 0
            total_savings = (coffee_monthly + treat_monthly) * 0.7

            report += f"**2. Coffee & Treats** - Potential savings: ${total_savings:.0f}/month\n"
            if coffee_data:
                transaction_count = coffee_data.get("transaction_count", 0) or 0
                report += f"• Coffee shops: {transaction_count} visits = ${coffee_monthly:.0f}/month\n"
            if treat_data:
                transaction_count = treat_data.get("transaction_count", 0) or 0
                report += f"• Treats/desserts: {transaction_count} visits = ${treat_monthly:.0f}/month\n"
            report += "**Actions**: Make coffee at home, limit treats to weekends\n\n"

        if restaurant_data:
            restaurant_monthly = (restaurant_data.get("total_spent", 0) or 0) / 3
            restaurant_savings = restaurant_monthly * 0.4
            transaction_count = restaurant_data.get("transaction_count", 0) or 0

            report += f"**3. Dining Out** - Potential savings: ${restaurant_savings:.0f}/month\n"
            report += f"• {transaction_count} restaurant visits = ${restaurant_monthly:.0f}/month\n"
            report += "**Actions**: Limit to 1-2 restaurant visits per week, meal prep\n\n"

        # Medium-impact opportunities
        report += "### 🔍 MEDIUM-IMPACT Opportunities (Save $25-100 monthly)\n\n"

        # Grocery optimization
        if grocery_data:
            avg_grocery_spend = sum(month.get("total_grocery_spend", 0) or 0 for month in grocery_data) / len(grocery_data)
            potential_savings = avg_grocery_spend * 0.15

            report += f"**4. Grocery Optimization** - Potential savings: ${potential_savings:.0f}/month\n"
            report += "```\n"
            for month in grocery_data:
                month_str = month.get("month", "Unknown")
                grocery_trips = month.get("grocery_trips", 0) or 0
                avg_per_trip = month.get("avg_per_trip", 0) or 0
                report += f"{month_str}: {grocery_trips} trips, ${avg_per_trip:.0f} avg/trip\n"
            report += "```\n"
            report += "**Actions**: Plan weekly meals, set $75 budget per trip, use store apps for coupons\n\n"

        # Small purchases breakdown
        small_purchases_total = sum(cat.get("total_spent", 0) or 0 for cat in small_purchases)
        if small_purchases_total > 0:
            potential_savings = small_purchases_total * 0.2 / 3
            report += f"**5. Small Purchase Optimization** - Potential savings: ${potential_savings:.0f}/month\n"
            report += "```\n"
            for cat in small_purchases[:4]:
                category = cat.get("category", "Unknown")
                transaction_count = cat.get("transaction_count", 0) or 0
                total_spent = cat.get("total_spent", 0) or 0
                report += f"• {category}: {transaction_count} purchases = ${total_spent:.2f}\n"
            report += "```\n"
            report += "**Actions**: Use 24-hour rule for non-essentials, batch small purchases\n\n"

        # Summary
        subscription_savings = (sum(sub.get("total_spent", 0) or 0 for sub in subscriptions) * 0.3 / 3) if subscriptions else 0
        coffee_treat_savings = ((coffee_data.get("total_spent", 0) or 0) + (treat_data.get("total_spent", 0) or 0)) * 0.7 / 3 if (coffee_data or treat_data) else 0
        restaurant_savings_calc = (restaurant_data.get("total_spent", 0) or 0) * 0.4 / 3 if restaurant_data else 0
        small_purchases_savings = small_purchases_total * 0.2 / 3

        total_potential_savings = subscription_savings + coffee_treat_savings + restaurant_savings_calc + small_purchases_savings

        report += f"### 📈 **Total Monthly Savings Potential: ${total_potential_savings:.0f}+**\n\n"
        report += "**Implementation Priority**:\n"
        report += "1. **Subscription audit** (easiest, immediate impact)\n"
        report += "2. **Coffee routine change** (highest ROI)\n"
        report += "3. **Meal planning** (reduces grocery + restaurant costs)\n"
        report += "4. **Small purchase discipline** (builds long-term habits)\n\n"
        report += "💡 **Tip**: Start with one category per month to build sustainable habits."

        return report

    async def _generate_anomaly_report(
        self,
        table_name: str,
        severity_threshold: str,
        focus_columns: list[str],
        anomaly_types: list[str],
    ) -> str:
        """Generate comprehensive anomaly detection report."""
        anomalies: list[dict[str, Any]] = []
        severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        min_severity = severity_order.get(severity_threshold, 2)

        # Get table schema for analysis
        schema = await self.server.execute_query(f"DESCRIBE {table_name}")
        total_rows_result = await self.server.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        total_rows = total_rows_result[0]["count"] if total_rows_result else 0

        report = f"# 🔍 Anomaly Detection Report\n**Table:** {table_name} ({total_rows:,} rows)\n**Severity Threshold:** {severity_threshold}\n\n"

        # 1. DUPLICATE DETECTION
        if "duplicates" in anomaly_types:
            duplicate_anomalies = await self._check_duplicates(table_name, schema, focus_columns)
            for dup in duplicate_anomalies:
                if severity_order.get(dup["severity"], 0) >= min_severity:
                    anomalies.append(dup)

        # 2. NULL VALUE ANALYSIS
        if "nulls" in anomaly_types:
            null_anomalies = await self._check_null_values(table_name, schema, total_rows, focus_columns)
            for null_anomaly in null_anomalies:
                if severity_order.get(null_anomaly["severity"], 0) >= min_severity:
                    anomalies.append(null_anomaly)

        # 3. STATISTICAL OUTLIERS
        if "statistical" in anomaly_types or "outliers" in anomaly_types:
            outlier_anomalies = await self._check_statistical_outliers(table_name, schema, focus_columns)
            for outlier in outlier_anomalies:
                if severity_order.get(outlier["severity"], 0) >= min_severity:
                    anomalies.append(outlier)

        # 4. PATTERN ANALYSIS
        if "patterns" in anomaly_types:
            pattern_anomalies = await self._check_pattern_anomalies(table_name, schema, focus_columns)
            for pattern in pattern_anomalies:
                if severity_order.get(pattern["severity"], 0) >= min_severity:
                    anomalies.append(pattern)

        # 5. BUSINESS LOGIC RULES
        if "business_logic" in anomaly_types:
            business_anomalies = await self._check_business_logic_anomalies(table_name, schema)
            for business in business_anomalies:
                if severity_order.get(business["severity"], 0) >= min_severity:
                    anomalies.append(business)

        # Sort anomalies by severity
        anomalies.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)

        # Format report
        if not anomalies:
            report += f"✅ **No anomalies detected** above {severity_threshold} severity threshold.\n"
        else:
            critical_count = len([a for a in anomalies if a["severity"] == "critical"])
            high_count = len([a for a in anomalies if a["severity"] == "high"])
            medium_count = len([a for a in anomalies if a["severity"] == "medium"])
            low_count = len([a for a in anomalies if a["severity"] == "low"])

            report += "## 📊 Summary\n"
            if critical_count > 0:
                report += f"🚨 **Critical:** {critical_count} anomalies\n"
            if high_count > 0:
                report += f"⚠️ **High:** {high_count} anomalies\n"
            if medium_count > 0:
                report += f"🔶 **Medium:** {medium_count} anomalies\n"
            if low_count > 0:
                report += f"🔵 **Low:** {low_count} anomalies\n"

            report += "\n## 🔍 Detailed Findings\n\n"

            for anomaly in anomalies:
                icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "🔶",
                    "low": "🔵",
                }.get(anomaly["severity"], "🔍")

                report += f"### {icon} {anomaly['title']}\n"
                report += f"**Severity:** {anomaly['severity'].upper()}\n"
                report += f"**Impact:** {anomaly['impact']}\n"
                if anomaly.get("affected_records"):
                    report += f"**Affected Records:** {anomaly['affected_records']:,}\n"
                if anomaly.get("percentage"):
                    report += f"**Percentage:** {anomaly['percentage']}%\n"
                report += f"**Details:** {anomaly['description']}\n"
                if anomaly.get("examples"):
                    report += f"**Examples:**\n```\n{anomaly['examples']}\n```\n"
                if anomaly.get("recommendation"):
                    report += f"**Recommendation:** {anomaly['recommendation']}\n"
                report += "\n---\n\n"

        return report

    async def _check_duplicates(
        self, table_name: str, schema: list[dict[str, Any]], focus_columns: list[str]
    ) -> list[dict[str, Any]]:
        """Check for duplicate values in columns."""
        anomalies = []
        columns_to_check = focus_columns if focus_columns else [col["column_name"] for col in schema]

        for column in columns_to_check[:8]:  # Limit to prevent excessive queries
            try:
                duplicate_query = f"""
                    SELECT {column}, COUNT(*) as duplicate_count
                    FROM {table_name} 
                    WHERE {column} IS NOT NULL
                    GROUP BY {column}
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                    LIMIT 10
                """

                duplicates = await self.server.execute_query(duplicate_query)

                if duplicates:
                    total_duplicate_records = sum(dup.get("duplicate_count", 0) or 0 for dup in duplicates)
                    max_duplicates = max(dup.get("duplicate_count", 0) or 0 for dup in duplicates)

                    if max_duplicates > 50000:
                        severity = "critical"
                    elif max_duplicates > 1000:
                        severity = "high"
                    elif max_duplicates > 10:
                        severity = "medium"
                    else:
                        severity = "low"

                    examples = "\n".join(
                        f"{list(d.values())[0]}: {d.get('duplicate_count', 0)} occurrences"
                        for d in duplicates[:3]
                    )

                    anomalies.append({
                        "type": "duplicate",
                        "severity": severity,
                        "title": f"Duplicate Values in {column}",
                        "impact": "Data integrity, potential processing errors",
                        "affected_records": total_duplicate_records,
                        "description": f"Found {len(duplicates)} unique values with duplicates, max {max_duplicates} occurrences",
                        "examples": examples,
                        "recommendation": "URGENT: Investigate data corruption, tracking number system failure" if max_duplicates > 1000 else "Review business logic for duplicates",
                    })
            except Exception:
                # Skip columns that can't be analyzed
                continue

        return anomalies

    async def _check_null_values(
        self, table_name: str, schema: list[dict[str, Any]], total_rows: int, focus_columns: list[str]
    ) -> list[dict[str, Any]]:
        """Check for excessive null values."""
        anomalies = []
        columns_to_check = focus_columns if focus_columns else [col["column_name"] for col in schema]

        for column_info in schema:
            column = column_info["column_name"]
            if column not in columns_to_check:
                continue

            try:
                null_query = f"""
                    SELECT 
                        COUNT(*) - COUNT({column}) as null_count,
                        ROUND((COUNT(*) - COUNT({column})) * 100.0 / COUNT(*), 2) as null_percentage
                    FROM {table_name}
                """

                result = await self.server.execute_query(null_query)
                if not result:
                    continue

                null_count = result[0].get("null_count", 0) or 0
                null_percentage = result[0].get("null_percentage", 0) or 0

                if null_count > 0:
                    if null_percentage > 50:
                        severity = "critical"
                    elif null_percentage > 25:
                        severity = "high"
                    elif null_percentage > 10:
                        severity = "medium"
                    else:
                        severity = "low"

                    if severity != "low" or null_count > 100:
                        anomalies.append({
                            "type": "null_values",
                            "severity": severity,
                            "title": f"High Null Rate in {column}",
                            "impact": "Data completeness, analysis accuracy",
                            "affected_records": null_count,
                            "percentage": null_percentage,
                            "description": f"{null_count} null values ({null_percentage}% of total)",
                            "recommendation": "Investigate data source, implement validation" if null_percentage > 25 else "Consider default values or imputation",
                        })
            except Exception:
                # Skip columns that can't be analyzed
                continue

        return anomalies

    async def _check_statistical_outliers(
        self, table_name: str, schema: list[dict[str, Any]], focus_columns: list[str]
    ) -> list[dict[str, Any]]:
        """Check for statistical outliers in numeric columns."""
        anomalies = []
        numeric_columns = [
            col for col in schema
            if any(t in col["column_type"].upper() for t in ["DOUBLE", "BIGINT", "INTEGER", "DECIMAL", "NUMERIC"])
        ]

        columns_to_check = (
            [col for col in numeric_columns if col["column_name"] in focus_columns]
            if focus_columns
            else numeric_columns[:5]
        )

        for column_info in columns_to_check:
            column = column_info["column_name"]

            try:
                stats_query = f"""
                    SELECT 
                        AVG({column}) as mean,
                        MIN({column}) as min_val,
                        MAX({column}) as max_val,
                        STDDEV({column}) as stddev,
                        COUNT(*) as total_count
                    FROM {table_name} 
                    WHERE {column} IS NOT NULL
                """

                stats_result = await self.server.execute_query(stats_query)
                if not stats_result:
                    continue

                stats = stats_result[0]
                mean = stats.get("mean", 0) or 0
                min_val = stats.get("min_val", 0) or 0
                max_val = stats.get("max_val", 0) or 0
                stddev = stats.get("stddev", 0) or 0
                total_count = stats.get("total_count", 0) or 0

                if stddev and stddev > 0:
                    # Use 3-sigma method
                    outlier_query = f"""
                        SELECT COUNT(*) as outlier_count
                        FROM {table_name}
                        WHERE {column} IS NOT NULL 
                          AND ({column} > {mean + 3 * stddev} OR {column} < {mean - 3 * stddev})
                    """

                    outlier_result = await self.server.execute_query(outlier_query)
                    if not outlier_result:
                        continue

                    outlier_count = outlier_result[0].get("outlier_count", 0) or 0
                    outlier_percentage = (outlier_count / total_count) * 100 if total_count > 0 else 0

                    if outlier_count > 0:
                        if outlier_percentage > 5:
                            severity = "high"
                        elif outlier_percentage > 1:
                            severity = "medium"
                        else:
                            severity = "low"

                        # Get examples of outliers
                        example_query = f"""
                            SELECT {column}
                            FROM {table_name}
                            WHERE {column} IS NOT NULL 
                              AND ({column} > {mean + 3 * stddev} OR {column} < {mean - 3 * stddev})
                            ORDER BY ABS({column} - {mean}) DESC
                            LIMIT 5
                        """

                        try:
                            examples_result = await self.server.execute_query(example_query)
                            example_values = [str(e[column]) for e in examples_result]
                            example_text = ", ".join(example_values)
                        except Exception:
                            example_text = "Unable to retrieve examples"

                        method = f"3σ (mean: {mean:.2f}, σ: {stddev:.2f})"
                        examples = f"Range: {min_val} to {max_val}\nOutlier examples: {example_text}"

                        anomalies.append({
                            "type": "statistical_outlier",
                            "severity": severity,
                            "title": f"Statistical Outliers in {column}",
                            "impact": "Potential data quality issues, skewed analysis",
                            "affected_records": outlier_count,
                            "percentage": round(outlier_percentage, 2),
                            "description": f"{outlier_count} values identified using {method}",
                            "examples": examples,
                            "recommendation": "Investigate extreme values, consider data validation rules",
                        })
            except Exception:
                # Skip columns that can't be analyzed
                continue

        return anomalies

    async def _check_pattern_anomalies(
        self, table_name: str, schema: list[dict[str, Any]], focus_columns: list[str]
    ) -> list[dict[str, Any]]:
        """Check for unusual patterns in string columns."""
        anomalies = []

        string_columns = [
            col for col in schema
            if any(t in col["column_type"].upper() for t in ["VARCHAR", "TEXT", "CHAR"])
        ]

        columns_to_check = (
            [col for col in string_columns if col["column_name"] in focus_columns]
            if focus_columns
            else string_columns[:3]
        )

        for column_info in columns_to_check:
            column = column_info["column_name"]

            try:
                # Check for unusual length patterns
                length_query = f"""
                    SELECT 
                        LENGTH({column}) as str_length,
                        COUNT(*) as count
                    FROM {table_name}
                    WHERE {column} IS NOT NULL
                    GROUP BY LENGTH({column})
                    ORDER BY count DESC
                    LIMIT 20
                """

                length_results = await self.server.execute_query(length_query)

                # Look for extremely short or long values
                extreme_lengths = [
                    r for r in length_results
                    if (r.get("str_length", 0) or 0) > 200 or (r.get("str_length", 0) or 0) < 1
                ]

                if extreme_lengths:
                    affected_count = sum(r.get("count", 0) or 0 for r in extreme_lengths)
                    severity = "medium" if affected_count > 100 else "low"

                    examples = "\n".join(
                        f"Length {r.get('str_length', 0)}: {r.get('count', 0)} records"
                        for r in extreme_lengths
                    )

                    anomalies.append({
                        "type": "length_pattern",
                        "severity": severity,
                        "title": f"Unusual Length Patterns in {column}",
                        "impact": "Potential data truncation or corruption",
                        "affected_records": affected_count,
                        "description": "Found values with extreme lengths",
                        "examples": examples,
                        "recommendation": "Review data input validation and field constraints",
                    })
            except Exception:
                # Skip columns that can't be analyzed
                continue

        return anomalies

    async def _check_business_logic_anomalies(
        self, table_name: str, schema: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Check for business logic violations."""
        anomalies = []

        try:
            # Check for zero/negative values in amount columns
            amount_columns = [
                col for col in schema
                if any(term in col["column_name"].lower() for term in ["amount", "charge", "price"])
            ]

            for column_info in amount_columns:
                column = column_info["column_name"]

                try:
                    zero_query = f"""
                        SELECT COUNT(*) as zero_count  
                        FROM {table_name}
                        WHERE {column} = 0
                    """

                    zero_result = await self.server.execute_query(zero_query)
                    zero_count = zero_result[0].get("zero_count", 0) or 0 if zero_result else 0

                    if zero_count > 50:
                        severity = "high" if zero_count > 500 else "medium"
                        anomalies.append({
                            "type": "business_logic",
                            "severity": severity,
                            "title": f"Excessive Zero Values in {column}",
                            "impact": "Revenue loss, processing errors",
                            "affected_records": zero_count,
                            "description": f"{zero_count} records with zero charges - potential pricing or billing errors",
                            "recommendation": "Review billing logic and pricing rules",
                        })
                except Exception:
                    continue

            # Check for date consistency
            date_columns = [
                col for col in schema
                if any(t in col["column_type"].upper() for t in ["DATE", "TIMESTAMP"])
            ]

            if len(date_columns) >= 2:
                try:
                    date_col1 = date_columns[0]["column_name"]
                    date_col2 = date_columns[1]["column_name"]

                    date_order_query = f"""
                        SELECT COUNT(*) as invalid_order_count
                        FROM {table_name}
                        WHERE {date_col1} IS NOT NULL AND {date_col2} IS NOT NULL
                          AND {date_col1} > {date_col2}
                    """

                    invalid_order_result = await self.server.execute_query(date_order_query)
                    invalid_order_count = invalid_order_result[0].get("invalid_order_count", 0) or 0 if invalid_order_result else 0

                    if invalid_order_count > 0:
                        severity = "high" if invalid_order_count > 100 else "medium"
                        anomalies.append({
                            "type": "business_logic",
                            "severity": severity,
                            "title": "Invalid Date Sequence",
                            "impact": "Data integrity, timeline analysis errors",
                            "affected_records": invalid_order_count,
                            "description": f"{invalid_order_count} records where {date_col1} > {date_col2}",
                            "recommendation": "Review data entry process and add validation constraints",
                        })
                except Exception:
                    pass

        except Exception:
            # Skip business logic checks if they fail
            pass

        return anomalies


# Import asyncio for concurrent execution
import asyncio
