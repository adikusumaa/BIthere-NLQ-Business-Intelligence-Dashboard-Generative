"""
Query executor node.
Executes SQL via a workspace-scoped connector (v2) or platform singleton (v1).
"""

from typing import Any

from app.connectors.base import BaseConnector
from app.core.logging import log_info, log_error


async def execute(
    generated_query: str,
    connector: BaseConnector,
) -> list[dict[str, Any]]:
    """
    Execute SQL against the given connector.

    Args:
        generated_query: Validated + optimized SQL.
        connector: Workspace connector instance. Caller is responsible
                   for calling connect() / disconnect().

    Returns:
        List of row dicts.

    Raises:
        Exception on query failure.
    """
    if not generated_query:
        raise ValueError("No SQL query provided")

    if connector is None:
        raise ValueError("Connector is required for query execution")

    try:
        await connector.connect()
        rows = await connector.execute_query(generated_query)
        log_info(f"Query executor returned {len(rows)} rows via {connector.get_dialect()}")
        return rows
    except Exception as exc:
        log_error(f"Query executor failed: {exc}")
        raise