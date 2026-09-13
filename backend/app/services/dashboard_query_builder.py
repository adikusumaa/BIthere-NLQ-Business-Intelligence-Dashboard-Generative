"""
Interactive single-page fraud dashboard - dynamic config test.

User NLQ scenario simulated here:
    "Buat dashboard fraud dengan tren bulanan, top states, cities,
     chip usage, age group, dan MCC. Saya ingin bisa klik salah satu
     brand kartu dan semua chart menyesuaikan."

Interaction model:
    - Click a bar on the Card Brand chart.
    - Its click behavior sets the brand_filter dashboard parameter.
    - All other charts re-query using [[AND {{brand_filter}}]].

Note: only the test data is static. The rendering layer is fully dynamic.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.tools.render_dashboard import render_dashboard_dynamic


FILTERS = [
    {
        "name": "Card Brand",
        "slug": "brand",
        "section": "category",
        "target_tag": "brand_filter",
        "dimension": ("cards", "card_brand"),
    },
    {
        "name": "Merchant State",
        "slug": "state",
        "section": "category",
        "target_tag": "state_filter",
        "dimension": ("transactions", "merchant_state"),
    },
    {
        "name": "Merchant City",
        "slug": "city",
        "section": "category",
        "target_tag": "city_filter",
        "dimension": ("transactions", "merchant_city"),
    },
    {
        "name": "Date Range",
        "slug": "date",
        "section": "date",
        "target_tag": "date_filter",
        "dimension": ("transactions", "date"),
    },
]


def sql_kpi(metric_expr: str) -> str:
    return (
        f"SELECT {metric_expr} "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]]"
    )


CHART_TOTAL_COUNT = {
    "title": "Total Fraud Count",
    "sql": sql_kpi("COUNT(*) AS total"),
    "display": "scalar",
    "layout": (0, 0, 6, 4),
    "metric": "total",
}

CHART_TOTAL_AMOUNT = {
    "title": "Total Fraud Amount",
    "sql": sql_kpi("ROUND(SUM(t.amount)::numeric, 2) AS total_amount"),
    "display": "scalar",
    "layout": (0, 6, 6, 4),
    "metric": "total_amount",
}

CHART_FRAUD_RATE = {
    "title": "Fraud Rate",
    "sql": (
        "SELECT ROUND(100.0 * SUM(CASE WHEN f.fraud_label = 'Yes' "
        "THEN 1 ELSE 0 END) / COUNT(*), 3) AS fraud_rate_pct "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE 1=1 "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]]"
    ),
    "display": "gauge",
    "layout": (0, 12, 6, 4),
    "metric": "fraud_rate_pct",
    "visualization_settings": {
        "gauge.segments": [
            {"min": 0, "max": 1, "color": "#8ecae6", "label": "Low"},
            {"min": 1, "max": 5, "color": "#ffb703", "label": "Medium"},
            {"min": 5, "max": 100, "color": "#e63946", "label": "High"},
        ]
    },
}

CHART_AVG_AMOUNT = {
    "title": "Average Fraud Amount",
    "sql": sql_kpi("ROUND(AVG(t.amount)::numeric, 2) AS avg_amount"),
    "display": "scalar",
    "layout": (0, 18, 6, 4),
    "metric": "avg_amount",
}

CHART_BY_BRAND = {
    "title": "Fraud by Card Brand",
    "sql": (
        "SELECT c.card_brand, COUNT(*) AS fraud_count "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY c.card_brand "
        "ORDER BY fraud_count DESC"
    ),
    "display": "bar",
    "layout": (4, 0, 24, 8),
    "dimension": "card_brand",
    "metric": "fraud_count",
    "crossfilter": {
        "source_tag": "brand_filter",
        "source_column": "card_brand",
    },
}

CHART_MONTHLY_TREND = {
    "title": "Monthly Fraud Trend",
    "sql": (
        "SELECT DATE_TRUNC('month', t.date) AS month, "
        "COUNT(*) AS fraud_count "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY month ORDER BY month"
    ),
    "display": "line",
    "layout": (12, 0, 24, 8),
    "dimension": "month",
    "metric": "fraud_count",
}

CHART_TOP_STATES = {
    "title": "Top 10 States by Fraud Count",
    "sql": (
        "SELECT t.merchant_state, COUNT(*) AS fraud_count "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY t.merchant_state "
        "ORDER BY fraud_count DESC LIMIT 10"
    ),
    "display": "row",
    "layout": (20, 0, 12, 8),
    "dimension": "merchant_state",
    "metric": "fraud_count",
    "crossfilter": {
        "source_tag": "state_filter",
        "source_column": "merchant_state",
    },
}

CHART_CHIP_USAGE = {
    "title": "Fraud by Chip Usage",
    "sql": (
        "SELECT t.use_chip, COUNT(*) AS fraud_count "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY t.use_chip"
    ),
    "display": "donut",
    "layout": (20, 12, 12, 8),
    "dimension": "use_chip",
    "metric": "fraud_count",
}

CHART_AGE_GROUP = {
    "title": "Fraud by Age Group",
    "sql": (
        "SELECT CASE "
        "WHEN u.current_age < 25 THEN 'Under 25' "
        "WHEN u.current_age < 35 THEN '25-34' "
        "WHEN u.current_age < 45 THEN '35-44' "
        "WHEN u.current_age < 55 THEN '45-54' "
        "WHEN u.current_age < 65 THEN '55-64' "
        "ELSE '65+' END AS age_group, "
        "COUNT(*) AS fraud_count "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY age_group ORDER BY age_group"
    ),
    "display": "bar",
    "layout": (28, 0, 12, 8),
    "dimension": "age_group",
    "metric": "fraud_count",
}

CHART_TOP_CITIES = {
    "title": "Top 10 Cities by Fraud Count",
    "sql": (
        "SELECT t.merchant_city, COUNT(*) AS fraud_count "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY t.merchant_city "
        "ORDER BY fraud_count DESC LIMIT 10"
    ),
    "display": "row",
    "layout": (28, 12, 12, 8),
    "dimension": "merchant_city",
    "metric": "fraud_count",
    "crossfilter": {
        "source_tag": "city_filter",
        "source_column": "merchant_city",
    },
}

CHART_MCC = {
    "title": "Fraud Amount by MCC Category",
    "sql": (
        "SELECT m.description AS category, "
        "ROUND(SUM(t.amount)::numeric, 2) AS total_amount "
        "FROM transactions t "
        "JOIN cards c ON t.card_id = c.id "
        "JOIN users u ON t.client_id = u.id "
        "JOIN fraud_labels f ON t.id = f.id "
        "JOIN mcc_codes m ON t.mcc = m.mcc_code "
        "WHERE f.fraud_label = 'Yes' "
        "[[AND {{brand_filter}}]] "
        "[[AND {{state_filter}}]] "
        "[[AND {{city_filter}}]] "
        "[[AND {{date_filter}}]] "
        "GROUP BY m.description "
        "ORDER BY total_amount DESC LIMIT 15"
    ),
    "display": "bar",
    "layout": (36, 0, 24, 8),
    "dimension": "category",
    "metric": "total_amount",
}


DASHBOARD_CONFIG = {
    "title": "Fraud Analytics Dashboard",
    "description": (
        "Interactive fraud analytics. Click a bar on the Card Brand or "
        "Merchant State chart to filter every other chart on the dashboard."
    ),
    "filters": FILTERS,
    "charts": [
        CHART_TOTAL_COUNT,
        CHART_TOTAL_AMOUNT,
        CHART_FRAUD_RATE,
        CHART_AVG_AMOUNT,
        CHART_BY_BRAND,
        CHART_MONTHLY_TREND,
        CHART_TOP_STATES,
        CHART_CHIP_USAGE,
        CHART_AGE_GROUP,
        CHART_TOP_CITIES,
        CHART_MCC,
    ],
}


async def main():
    print("=" * 76)
    print(f"  {DASHBOARD_CONFIG['title']}")
    print("=" * 76)
    print(f"  Charts  : {len(DASHBOARD_CONFIG['charts'])}")
    print(f"  Filters : {len(DASHBOARD_CONFIG['filters'])}")
    print("  Clickable charts:")
    print("    - Fraud by Card Brand -> brand_filter")
    print("    - Top 10 States       -> state_filter")
    print("    - Top 10 Cities       -> city_filter")
    print("=" * 76)

    result = await render_dashboard_dynamic(DASHBOARD_CONFIG)

    print()
    if result["success"]:
        print("[SUCCESS] Dashboard created")
        print(f"  Dashboard ID : {result.get('dashboard_id')}")
        print(f"  Filters      : {', '.join(result.get('filters', []))}")
        print(f"  Card IDs     : {result.get('card_ids', [])}")
        print(f"  Embed URL    : {result.get('embed_url')}")
        print()
        print("=" * 76)
        print("  Open in browser:")
        print(f"  {result.get('embed_url')}")
        print()
        print("  Interaction: click a bar on Card Brand / State / City.")
        print("  All other charts re-query to show only that segment.")
        print("  Reset: click the X on the filter widget at the top.")
        print("=" * 76)
    else:
        print("[FAILED]")
        print(f"  Error : {result.get('error')}")
        print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())