"""
DuckDB connector. Uses a per-workspace file at DUCKDB_DIR/{workspace_id}.duckdb.
DuckDB is synchronous and NOT thread-safe, so all operations run on a
dedicated single-worker thread executor.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import duckdb

from app.connectors.base import BaseConnector, ConnectorConfig
from app.core.config import settings
from app.core.logging import logger


class DuckDBConnector(BaseConnector):
    """DuckDB connector scoped to a workspace database file."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self._path = self._resolve_path()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="duckdb")

    def _resolve_path(self) -> str:
        if self.config:
            if self.config.connection_string:
                return self.config.connection_string
            if self.config.database:
                return self.config.database

        workspace_id = None
        if self.config and self.config.options:
            workspace_id = self.config.options.get("workspace_id")

        base = settings.DUCKDB_DIR
        os.makedirs(base, exist_ok=True)
        filename = f"{workspace_id}.duckdb" if workspace_id else "default.duckdb"
        return os.path.join(base, filename)

    async def connect(self) -> None:
        if self.conn is not None:
            return
        loop = asyncio.get_running_loop()
        try:
            self.conn = await loop.run_in_executor(
                self._executor, duckdb.connect, self._path
            )
            logger.info(f"[SUCCESS] DuckDB connection established: {self._path}")
        except Exception as error:
            logger.error(f"[ERROR] DuckDB connect failed: {error}")
            raise

    async def disconnect(self) -> None:
        if self.conn:
            loop = asyncio.get_running_loop()
            conn = self.conn
            self.conn = None
            await loop.run_in_executor(self._executor, conn.close)
            self._executor.shutdown(wait=False)
            logger.info("[PROCESS] DuckDB connection closed")

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if self.conn is None:
            await self.connect()

        loop = asyncio.get_running_loop()

        def _run() -> List[Dict[str, Any]]:
            result = self.conn.execute(query)
            columns = [d[0] for d in result.description] if result.description else []
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

        return await loop.run_in_executor(self._executor, _run)

    async def get_schema(self) -> Dict[str, Any]:
        if self.conn is None:
            await self.connect()

        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'main'
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
        return "duckdb"