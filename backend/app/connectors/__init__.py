"""
Database connector factory for BIthere.
"""

from app.connectors.base import BaseConnector
from app.connectors.postgres import PostgresConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.mongodb import MongoDBConnector
from app.core.config import settings
from app.core.logging import logger


def get_connector() -> BaseConnector:
    """
    Returns appropriate connector based on DB_TYPE setting.
    """

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
    return connector_class()


__all__ = ["BaseConnector", "get_connector"]