"""
Test for MCP tool: fetch_data
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.tools.fetch_data import fetch_data


async def main():
    print("=" * 60)
    print("[TEST 1] Valid query")
    print("=" * 60)
    result = await fetch_data("SELECT COUNT(*) AS total FROM users")
    print(f"Success   : {result['success']}")
    print(f"Row count : {result['row_count']}")
    print(f"Data      : {result['data']}")
    print(f"Error     : {result['error']}")

    print("\n" + "=" * 60)
    print("[TEST 2] Empty query")
    print("=" * 60)
    result = await fetch_data("")
    print(f"Success   : {result['success']}")
    print(f"Error     : {result['error']}")

    print("\n" + "=" * 60)
    print("[TEST 3] Invalid query (should fail gracefully)")
    print("=" * 60)
    result = await fetch_data("SELECT * FROM nonexistent_table")
    print(f"Success   : {result['success']}")
    print(f"Error     : {result['error']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())