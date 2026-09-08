"""
MongoDB connector stub for future implementation.
"""

from typing import Any, Dict, List

from app.connectors.base import BaseConnector
from app.core.logging import logger


class MongoDBConnector(BaseConnector):
    """
    MongoDB connector placeholder.
    """

    async def connect(self) -> None:
        """
        Establish connection to MongoDB.
        """

        logger.warning("MongoDB connector not implemented yet")
        raise NotImplementedError("MongoDB connector not implemented yet")

    async def disconnect(self) -> None:
        """
        Close MongoDB connection.
        """

        pass

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute query on MongoDB.
        """

        raise NotImplementedError("MongoDB connector not implemented yet")

    async def get_schema(self) -> Dict[str, Any]:
        """
        Retrieve MongoDB schema.
        """

        raise NotImplementedError("MongoDB connector not implemented yet")