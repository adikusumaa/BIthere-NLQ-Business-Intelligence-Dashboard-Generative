"""
Abstract base class for database connectors.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseConnector(ABC):
    """
    Abstract base class that all database connectors must implement.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the database.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close database connection.
        """
        pass

    @abstractmethod
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as list of dictionaries.
        """
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        Retrieve database schema information.
        """
        pass