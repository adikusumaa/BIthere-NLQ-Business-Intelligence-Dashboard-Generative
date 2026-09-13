import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.connectors import get_connector


async def main():
    connector = get_connector()
    await connector.connect()
    result = await connector.execute_query("SELECT COUNT(*) AS total FROM users")
    print("[RESULT]", result)
    await connector.disconnect()


if __name__ == "__main__":
    asyncio.run(main())