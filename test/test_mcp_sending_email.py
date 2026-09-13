"""
Test for MCP tool: send_email
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.tools.send_email import send_email
from app.services.email_templates import render_report_email, render_report_subject
from app.core.config import settings


TEST_RECIPIENT = "quelynshymko@gmail.com"


async def main():
    print("=" * 60)
    print(f"TEST_RECIPIENT : {TEST_RECIPIENT}")
    print("=" * 60)

    # --- TEST 1: Professional HTML report ---
    print("\n[TEST 1] Professional HTML report")
    print("-" * 60)

    insight_text = (
        "In January 2010, a total of 15 transactions were flagged as fraudulent, "
        "representing a non-trivial level of activity that warrants attention.\n"
        "The total amount involved in these transactions reached 1,234.56 USD, "
        "indicating a moderate financial exposure for the period.\n"
        "Recommendation: compare this month's fraud volume with adjacent months to "
        "identify seasonal patterns, and perform root-cause analysis on the flagged "
        "transactions to strengthen detection rules."
    )

    subject = render_report_subject("Fraud Analysis", "January 2010")
    html_body = render_report_email(
        title="Fraud Analysis - January 2010",
        insight=insight_text,
        dashboard_url="http://localhost:3000/public/dashboard/example",
    )

    result = await send_email(
        to_email=TEST_RECIPIENT,
        subject=subject,
        body=html_body,
        is_html=True,
    )
    print(f"Subject : {subject}")
    print(f"Success : {result['success']}")
    print(f"Error   : {result['error']}")

    # --- TEST 2: Invalid recipient ---
    print("\n[TEST 2] Invalid recipient (should fail)")
    print("-" * 60)
    result = await send_email(
        to_email="not-an-email",
        subject="Test",
        body="Body",
    )
    print(f"Success : {result['success']}")
    print(f"Error   : {result['error']}")

    # --- TEST 3: Empty subject ---
    print("\n[TEST 3] Empty subject (should fail)")
    print("-" * 60)
    result = await send_email(
        to_email=TEST_RECIPIENT,
        subject="",
        body="Body",
    )
    print(f"Success : {result['success']}")
    print(f"Error   : {result['error']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())