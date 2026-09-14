"""
Test for the MCP tool server registry.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.mcp.server import list_tools, call_tool
from app.connectors import get_connector


async def main():
    print("=" * 60)
    print("[TEST 1] List registered tools")
    print("=" * 60)
    for tool in list_tools():
        print(f"- {tool['name']}: {tool['description']}")

    print("\n" + "=" * 60)
    print("[TEST 2] Call tool: fetch_data")
    print("=" * 60)
    result = await call_tool(
        "fetch_data",
        sql="SELECT COUNT(*) AS total FROM users",
    )
    print(f"Success  : {result.get('success')}")
    print(f"Row count: {result.get('row_count')}")
    print(f"Data     : {result.get('data')}")

    print("\n" + "=" * 60)
    print("[TEST 3] Call unknown tool (should fail gracefully)")
    print("=" * 60)
    result = await call_tool("nonexistent_tool", foo="bar")
    print(f"Success : {result.get('success')}")
    print(f"Error   : {result.get('error')}")

    print("\n" + "=" * 60)

    try:
        connector = get_connector()
        if getattr(connector, "pool", None):
            await connector.disconnect()
    except Exception:
        pass
    print("[CLEANUP] Connector closed")


if __name__ == "__main__":
    asyncio.run(main())