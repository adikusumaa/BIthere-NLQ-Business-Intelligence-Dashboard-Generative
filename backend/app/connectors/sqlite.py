"""
SQLite connector implementation using aiosqlite.
"""

from typing import Any, Dict, List, Optional

import aiosqlite

from app.connectors.base import BaseConnector, ConnectorConfig
from app.core.logging import logger


class SQLiteConnector(BaseConnector):
    """SQLite connector. Path comes from config.database or connection_string."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config
        self.conn: Optional[aiosqlite.Connection] = None

    def _path(self) -> str:
        if not self.config:
            raise ValueError("SQLiteConnector requires a ConnectorConfig")
        return self.config.connection_string or self.config.database or ":memory:"

    async def connect(self) -> None:
        if self.conn is not None:
            return
        try:
            self.conn = await aiosqlite.connect(self._path(), isolation_level=None)
            self.conn.row_factory = aiosqlite.Row
            logger.info("[SUCCESS] SQLite connection established")
        except Exception as error:
            logger.error(f"[ERROR] SQLite connect failed: {error}")
            raise

    async def disconnect(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("[PROCESS] SQLite connection closed")

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if self.conn is None:
            await self.connect()

        cursor = await self.conn.execute(query)
        try:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            await cursor.close()

    async def get_schema(self) -> Dict[str, Any]:
        if self.conn is None:
            await self.connect()

        cursor = await self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        await cursor.close()

        schema: Dict[str, Any] = {}
        for table in tables:
            cur = await self.conn.execute(f"PRAGMA table_info({table})")
            cols = await cur.fetchall()
            await cur.close()
            schema[table] = [
                {"column": c["name"], "type": c["type"]} for c in cols
            ]
        return schema

    def get_dialect(self) -> str:
        return "sqlite"