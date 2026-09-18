"""
MySQL / MariaDB connector implementation using aiomysql.
"""

from typing import Any, Dict, List, Optional

import aiomysql

from app.connectors.base import BaseConnector, ConnectorConfig
from app.core.logging import logger


class MySQLConnector(BaseConnector):
    """MySQL / MariaDB connector."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config
        self.pool: Optional[aiomysql.Pool] = None

    def _kwargs(self) -> dict:
        if not self.config:
            raise ValueError("MySQLConnector requires a ConnectorConfig")

        if self.config.connection_string:
            return {"dsn": self.config.connection_string}

        return {
            "host": self.config.host or "localhost",
            "port": self.config.port or 3306,
            "user": self.config.username,
            "password": self.config.password,
            "db": self.config.database,
            "charset": "utf8mb4",
            "autocommit": True,
        }

    async def connect(self) -> None:
        if self.pool is not None:
            return
        try:
            kwargs = self._kwargs()
            if "dsn" in kwargs:
                self.pool = await aiomysql.create_pool(
                    host=None, dsn=kwargs["dsn"],
                    minsize=1, maxsize=5, autocommit=True,
                )
            else:
                self.pool = await aiomysql.create_pool(
                    minsize=1, maxsize=5, **kwargs,
                )
            logger.info("[SUCCESS] MySQL connection pool created")
        except Exception as error:
            logger.error(f"[ERROR] MySQL connect failed: {error}")
            raise

    async def disconnect(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("[PROCESS] MySQL connection pool closed")

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query)
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_schema(self) -> Dict[str, Any]:
        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            ORDER BY table_name, ordinal_position
        """
        results = await self.execute_query(query)
        schema: Dict[str, Any] = {}
        for row in results:
            schema.setdefault(row["table_name"], []).append({
                "column": row["column_name"],
                "type": row["data_type"],
            })
        return schema

    def get_dialect(self) -> str:
        return "mysql"