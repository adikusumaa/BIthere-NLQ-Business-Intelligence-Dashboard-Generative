"""
Full dashboard test — creates 5 charts in one Metabase dashboard.

Charts:
1. Scalar  - Total fraud count
2. Bar     - Top 10 merchant cities by fraud count
3. Line    - Monthly fraud trend
4. Pie     - Fraud distribution by card brand
5. Table   - Top 5 states by total fraud amount
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.tools.render_dashboard import render_dashboard_multi


CHARTS = [
    {
        "title": "Total Fraud Transactions",
        "sql": (
            "SELECT COUNT(*) AS total_fraud "
            "FROM fraud_labels WHERE fraud_label = 'Yes'"
        ),
        "display": "scalar",
    },
    {
        "title": "Top 10 Cities by Fraud Count",
        "sql": (
            "SELECT t.merchant_city, COUNT(*) AS fraud_count "
            "FROM transactions t "
            "JOIN fraud_labels f ON t.id = f.id "
            "WHERE f.fraud_label = 'Yes' "
            "GROUP BY t.merchant_city "
            "ORDER BY fraud_count DESC "
            "LIMIT 10"
        ),
        "display": "bar",
    },
    {
        "title": "Monthly Fraud Trend",
        "sql": (
            "SELECT DATE_TRUNC('month', t.date) AS month, COUNT(*) AS fraud_count "
            "FROM transactions t "
            "JOIN fraud_labels f ON t.id = f.id "
            "WHERE f.fraud_label = 'Yes' "
            "GROUP BY month ORDER BY month"
        ),
        "display": "line",
    },
    {
        "title": "Fraud Distribution by Card Brand",
        "sql": (
            "SELECT c.card_brand, COUNT(*) AS fraud_count "
            "FROM transactions t "
            "JOIN cards c ON t.card_id = c.id "
            "JOIN fraud_labels f ON t.id = f.id "
            "WHERE f.fraud_label = 'Yes' "
            "GROUP BY c.card_brand"
        ),
        "display": "pie",
    },
    {
        "title": "Top 5 States by Fraud Amount",
        "sql": (
            "SELECT t.merchant_state, "
            "ROUND(SUM(t.amount)::numeric, 2) AS total_fraud_amount "
            "FROM transactions t "
            "JOIN fraud_labels f ON t.id = f.id "
            "WHERE f.fraud_label = 'Yes' "
            "GROUP BY t.merchant_state "
            "ORDER BY total_fraud_amount DESC "
            "LIMIT 5"
        ),
        "display": "table",
    },
]


async def main():
    print("=" * 60)
    print(f"[TEST] Building dashboard with {len(CHARTS)} charts")
    print("=" * 60)

    result = await render_dashboard_multi(
        title="BIthere — Fraud Analytics Dashboard",
        charts=CHARTS,
    )

    print(f"\nSuccess      : {result['success']}")
    print(f"Dashboard ID : {result['dashboard_id']}")
    print(f"Card IDs     : {result['card_ids']}")
    print(f"Embed URL    : {result['embed_url']}")
    print(f"Error        : {result['error']}")
    print("\n" + "=" * 60)
    if result["embed_url"]:
        print("Open in browser:")
        print(f"  {result['embed_url']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())