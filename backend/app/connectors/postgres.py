"""
PostgreSQL connector implementation using asyncpg.
"""

from typing import Any, Dict, List

import asyncpg

from app.connectors.base import BaseConnector
from app.core.config import settings
from app.core.logging import logger


class PostgresConnector(BaseConnector):
    """
    PostgreSQL connector for Supabase database.
    """

    def __init__(self):
        self.pool = None

    async def connect(self) -> None:
        """
        Create connection pool to PostgreSQL using SUPABASE_DB_URL.
        """
        try:
            database_url = settings.SUPABASE_DB_URL
            if not database_url:
                raise ValueError("SUPABASE_DB_URL is not set in .env")

            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=5,
                timeout=10,
                command_timeout=30,
            )
            logger.success("PostgreSQL connection pool created")
        except Exception as error:
            logger.error(f"Failed to connect to PostgreSQL: {str(error)}")
            raise

    async def disconnect(self) -> None:
        """
        Close connection pool.
        """
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as connection:
                records = await connection.fetch(query)
                return [dict(record) for record in records]
        except Exception as error:
            logger.error(f"Query execution failed: {str(error)}")
            raise

    async def get_schema(self) -> Dict[str, Any]:
        """
        Retrieve database schema (tables and columns).
        """
        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        results = await self.execute_query(query)

        schema = {}
        for row in results:
            table = row["table_name"]
            if table not in schema:
                schema[table] = []
            schema[table].append({
                "column": row["column_name"],
                "type": row["data_type"],
            })

        return schema