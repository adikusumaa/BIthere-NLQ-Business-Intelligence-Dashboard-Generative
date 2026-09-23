"""
PostgreSQL connector implementation using asyncpg.
"""

import asyncio
from typing import Any, Dict, List, Optional

import asyncpg

from app.connectors.base import BaseConnector, ConnectorConfig
from app.core.config import settings
from app.core.logging import logger


class PostgresConnector(BaseConnector):
    """
    PostgreSQL connector. If no config is passed, uses platform-level
    SUPABASE_DB_URL (v1 behavior).
    """

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    def _dsn(self) -> str:
        if self.config and self.config.connection_string:
            return self.config.connection_string
        return settings.SUPABASE_DB_URL

    async def connect(self) -> None:
        if self.pool is not None:
            return

        async with self._lock:
            if self.pool is not None:
                return
            try:
                dsn = self._dsn()
                if not dsn:
                    raise ValueError("PostgreSQL DSN is not set")

                self.pool = await asyncpg.create_pool(
                    dsn,
                    min_size=1,
                    max_size=8,
                    timeout=60,
                    command_timeout=600,
                )
                logger.info("[SUCCESS] PostgreSQL connection pool created")
            except Exception as error:
                logger.error(f"[ERROR] Failed to connect to PostgreSQL: {error}")
                raise

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("[PROCESS] PostgreSQL connection pool closed")

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as connection:
                records = await connection.fetch(query)
                return [dict(record) for record in records]
        except Exception as error:
            logger.error(f"[ERROR] Query execution failed: {error}")
            raise

    async def get_schema(self) -> Dict[str, Any]:
        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        results = await self.execute_query(query)

        schema: Dict[str, Any] = {}
        for row in results:
            table = row["table_name"]
            schema.setdefault(table, []).append({
                "column": row["column_name"],
                "type": row["data_type"],
            })
        return schema

    def get_dialect(self) -> str:
        return "postgresql"