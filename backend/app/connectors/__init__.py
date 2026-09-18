"""
Database connector factory.
- get_connector(): v1 singleton, platform-level DB_TYPE.
- build_connector(config): v2, per-workspace, based on ConnectorConfig.
"""

from typing import Optional

from app.connectors.base import BaseConnector, ConnectorConfig
from app.connectors.postgres import PostgresConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.mongodb import MongoDBConnector
from app.connectors.sqlite import SQLiteConnector
from app.connectors.duckdb import DuckDBConnector
from app.core.config import settings
from app.core.logging import logger


CONNECTOR_REGISTRY = {
    "postgres": PostgresConnector,
    "postgresql": PostgresConnector,
    "mysql": MySQLConnector,
    "mariadb": MySQLConnector,
    "mongodb": MongoDBConnector,
    "mongo": MongoDBConnector,
    "sqlite": SQLiteConnector,
    "duckdb": DuckDBConnector,
}


_singleton: Optional[BaseConnector] = None


def get_connector() -> BaseConnector:
    """
    Return the singleton connector for platform-level DB_TYPE (v1 behavior).
    """
    global _singleton

    if _singleton is not None:
        return _singleton

    db_type = settings.DB_TYPE.lower()
    connector_class = CONNECTOR_REGISTRY.get(db_type)

    if not connector_class:
        logger.error(f"[ERROR] Unsupported database type: {settings.DB_TYPE}")
        raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")

    logger.info(f"[PROCESS] Using platform connector: {db_type}")
    _singleton = connector_class()
    return _singleton


async def close_connector() -> None:
    """Close the singleton connector pool (graceful shutdown)."""
    global _singleton
    if _singleton and getattr(_singleton, "pool", None):
        await _singleton.disconnect()
    _singleton = None


def build_connector(config: ConnectorConfig) -> BaseConnector:
    """
    Build a new connector instance from a ConnectorConfig (v2).
    Not cached — caller decides lifecycle.
    """
    key = config.type.lower()
    connector_class = CONNECTOR_REGISTRY.get(key)

    if not connector_class:
        raise ValueError(f"Unsupported connector type: {config.type}")

    return connector_class(config)


__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "get_connector",
    "close_connector",
    "build_connector",
    "CONNECTOR_REGISTRY",
]