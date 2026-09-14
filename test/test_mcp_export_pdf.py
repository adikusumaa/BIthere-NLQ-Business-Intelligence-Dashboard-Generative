"""
Test for MCP tool: export_pdf

Requires a valid public Metabase dashboard URL for the screenshot test.
Replace DASHBOARD_URL below with one from a previous test run.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.tools.export_pdf import export_pdf


DASHBOARD_URL = "http://localhost:3000/public/dashboard/c0172672-1f01-4580-b031-39538c15dc81"


SAMPLE_INSIGHT = (
    "Executive Summary:\n"
    "In January 2010, a total of 15 transactions were flagged as fraudulent. "
    "The total amount involved reached 1,234.56 USD, indicating moderate "
    "financial exposure for the period.\n"
    "The fraud rate stands at 0.15%, which is within acceptable thresholds "
    "but warrants continued monitoring.\n"
    "\n"
    "Key Findings:\n"
    "The largest concentration of fraud occurred in Italy, accounting for "
    "over 60% of the total fraudulent amount. This is followed by Ohio and "
    "California, which together represent another 15% of the exposure.\n"
    "Card brand analysis shows that Mastercard and Visa are the most "
    "affected brands, consistent with their higher transaction volumes.\n"
    "\n"
    "Recommendations:\n"
    "First, conduct a root-cause analysis on the Italian transactions to "
    "identify common merchant or product patterns. Second, strengthen the "
    "detection rules around high-value transactions exceeding 200 USD. "
    "Third, expand the fraud monitoring to cover chip-related anomalies "
    "that bypassed the physical chip verification."
)

SAMPLE_KPIS = [
    {"label": "Total Fraud Transactions", "value": "1,505"},
    {"label": "Total Fraud Amount (USD)", "value": "166,016.90"},
    {"label": "Average Fraud Amount (USD)", "value": "110.31"},
    {"label": "Fraud Rate", "value": "0.15%"},
    {"label": "Top Affected State", "value": "Italy"},
]


async def main():
    print("=" * 60)
    print("[TEST 1] Export PDF with KPIs and dashboard screenshot")
    print("=" * 60)

    result = await export_pdf(
        title="Fraud Analysis - January 2010",
        insight=SAMPLE_INSIGHT,
        dashboard_url=DASHBOARD_URL,
        kpis=SAMPLE_KPIS,
        capture_screenshot=True,
    )
    print(f"Success         : {result['success']}")
    print(f"Engine          : {result.get('engine')}")
    print(f"Filename        : {result['filename']}")
    print(f"Path            : {result['pdf_path']}")
    print(f"Screenshot      : {result.get('screenshot_path')}")
    print(f"Error           : {result['error']}")

    print("\n" + "=" * 60)
    print("[TEST 2] Empty title (should fail)")
    print("=" * 60)
    result = await export_pdf(title="", insight="Some content")
    print(f"Success : {result['success']}")
    print(f"Error   : {result['error']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())