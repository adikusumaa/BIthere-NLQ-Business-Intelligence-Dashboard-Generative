"""
Database connector factory for BIthere.
"""

from app.connectors.base import BaseConnector
from app.connectors.postgres import PostgresConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.mongodb import MongoDBConnector
from app.core.config import settings
from app.core.logging import logger


_singleton: BaseConnector | None = None


def get_connector() -> BaseConnector:
    """
    Return a singleton connector instance for the configured DB_TYPE.

    The same pool is reused across all callers to avoid exhausting
    Supabase pooler limits when many queries run in parallel.
    """
    global _singleton

    if _singleton is not None:
        return _singleton

    connectors = {
        "postgres": PostgresConnector,
        "mysql": MySQLConnector,
        "mongodb": MongoDBConnector,
    }

    connector_class = connectors.get(settings.DB_TYPE.lower())

    if not connector_class:
        logger.error(f"Unsupported database type: {settings.DB_TYPE}")
        raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")

    logger.info(f"Using {settings.DB_TYPE} connector")
    _singleton = connector_class()
    return _singleton


async def close_connector() -> None:
    """Close the singleton connector pool (for graceful shutdown)."""
    global _singleton
    if _singleton and getattr(_singleton, "pool", None):
        await _singleton.disconnect()
    _singleton = None


__all__ = ["BaseConnector", "get_connector", "close_connector"]