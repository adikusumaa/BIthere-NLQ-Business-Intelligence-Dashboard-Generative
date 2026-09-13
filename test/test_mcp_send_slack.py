"""
Test for MCP tool: send_slack
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.tools.send_slack import send_slack
from app.core.config import settings


async def main():
    print("=" * 60)
    print(f"SLACK_WEBHOOK_URL set: {bool(settings.SLACK_WEBHOOK_URL)}")
    print("=" * 60)

    print("\n[TEST 1] Send a normal message")
    print("-" * 60)
    result = await send_slack("Test message from BIthere MCP tool.")
    print(f"Success : {result['success']}")
    print(f"Channel : {result['channel']}")
    print(f"Error   : {result['error']}")

    print("\n[TEST 2] Empty message")
    print("-" * 60)
    result = await send_slack("")
    print(f"Success : {result['success']}")
    print(f"Error   : {result['error']}")

    print("\n[TEST 3] Message with dashboard URL")
    print("-" * 60)
    result = await send_slack(
        "Fraud report for January 2010 — 15 transactions flagged.",
        dashboard_url="http://localhost:3000/public/dashboard/example",
    )
    print(f"Success : {result['success']}")
    print(f"Error   : {result['error']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())