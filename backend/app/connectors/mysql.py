"""
MySQL connector stub for future implementation.
"""

from typing import Any, Dict, List

from app.connectors.base import BaseConnector
from app.core.logging import logger


class MySQLConnector(BaseConnector):
    """
    MySQL connector placeholder.
    """

    async def connect(self) -> None:
        """
        Establish connection to MySQL.
        """

        logger.warning("MySQL connector not implemented yet")
        raise NotImplementedError("MySQL connector not implemented yet")

    async def disconnect(self) -> None:
        """
        Close MySQL connection.
        """

        pass

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute query on MySQL.
        """

        raise NotImplementedError("MySQL connector not implemented yet")

    async def get_schema(self) -> Dict[str, Any]:
        """
        Retrieve MySQL schema.
        """

        raise NotImplementedError("MySQL connector not implemented yet")