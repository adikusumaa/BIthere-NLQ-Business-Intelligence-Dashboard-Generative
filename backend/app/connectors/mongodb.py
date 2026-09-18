"""
MongoDB connector implementation using motor.
No SQL — accepts aggregation pipeline as JSON string.
"""

import json
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.connectors.base import BaseConnector, ConnectorConfig
from app.core.logging import logger


class MongoDBConnector(BaseConnector):
    """
    MongoDB connector. execute_query() expects a JSON string:
    {"collection": "name", "pipeline": [{"$match": {...}}], "limit": 100}
    """

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    def _uri(self) -> str:
        if not self.config:
            raise ValueError("MongoDBConnector requires a ConnectorConfig")
        if self.config.connection_string:
            return self.config.connection_string
        user = self.config.username or ""
        pwd = self.config.password or ""
        host = self.config.host or "localhost"
        port = self.config.port or 27017
        cred = f"{user}:{pwd}@" if user else ""
        return f"mongodb://{cred}{host}:{port}"

    async def connect(self) -> None:
        if self.client is not None:
            return
        try:
            self.client = AsyncIOMotorClient(self._uri(), serverSelectionTimeoutMS=5000)
            await self.client.admin.command("ping")
            db_name = (self.config.database if self.config else None) or "admin"
            self.db = self.client[db_name]
            logger.info("[SUCCESS] MongoDB connection established")
        except Exception as error:
            logger.error(f"[ERROR] MongoDB connect failed: {error}")
            raise

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("[PROCESS] MongoDB connection closed")

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if self.client is None:
            await self.connect()

        try:
            spec = json.loads(query)
        except json.JSONDecodeError as exc:
            raise ValueError(f"MongoDB query must be valid JSON: {exc}") from exc

        collection = spec.get("collection")
        if not collection:
            raise ValueError("MongoDB query must include 'collection'")

        pipeline = spec.get("pipeline", [])
        limit = spec.get("limit", 100)

        cursor = self.db[collection].aggregate(pipeline)
        results: List[Dict[str, Any]] = []
        async for doc in cursor:
            doc["_id"] = str(doc.get("_id"))
            results.append(doc)
            if len(results) >= limit:
                break
        return results

    async def get_schema(self) -> Dict[str, Any]:
        if self.client is None:
            await self.connect()

        schema: Dict[str, Any] = {}
        collections = await self.db.list_collection_names()
        for name in collections:
            sample = await self.db[name].find_one()
            columns = []
            if sample:
                for key, value in sample.items():
                    columns.append({
                        "column": key,
                        "type": type(value).__name__,
                    })
            schema[name] = columns
        return schema

    def get_dialect(self) -> str:
        return "mongodb"

    def supports_sql(self) -> bool:
        return False