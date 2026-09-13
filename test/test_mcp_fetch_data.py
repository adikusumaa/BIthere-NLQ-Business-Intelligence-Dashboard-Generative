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
from app.connectors import get_connector


async def cleanup_connections():
    """Close all open connections and let SSL transports drain."""
    try:
        connector = get_connector()
        if getattr(connector, "pool", None):
            await connector.disconnect()
    except Exception:
        pass

    # Let pending SSL writes flush
    await asyncio.sleep(0.3)

    # Cancel any remaining pending tasks
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def main():
    try:
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
    finally:
        await cleanup_connections()
        print("[CLEANUP] All connections closed")


if __name__ == "__main__":
    asyncio.run(main())