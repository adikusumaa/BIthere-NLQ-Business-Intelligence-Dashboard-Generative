"""
Abstract base class for database connectors.

v2 additions:
- ConnectorConfig: per-workspace connection settings
- test_connection(), get_dialect(), supports_sql()
- All new methods have defaults, so v1 subclasses remain compatible.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConnectorConfig:
    """Connection settings for a single data source."""
    type: str
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base class that all database connectors must implement.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries."""
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Retrieve database schema information."""
        pass

    async def test_connection(self) -> bool:
        """
        Ping the database. Default implementation connects and disconnects.
        Override for a lighter check if the driver supports it.
        """
        try:
            await self.connect()
            await self.disconnect()
            return True
        except Exception:
            return False

    def get_dialect(self) -> str:
        """Return the SQL dialect name (used for query generation)."""
        return "sql"

    def supports_sql(self) -> bool:
        """Whether this connector accepts SQL queries."""
        return True