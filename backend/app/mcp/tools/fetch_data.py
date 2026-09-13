"""
MCP tool: fetch_data
Execute SQL queries via the configured database connector.
"""

from typing import Any

from app.connectors import get_connector
from app.core.logging import log_process, log_success, log_error


async def fetch_data(sql: str) -> dict[str, Any]:
    """
    Execute a SQL query and return the results.

    Args:
        sql: A SELECT query string.

    Returns:
        dict with keys:
            - success (bool)
            - row_count (int)
            - data (list of dicts)
            - error (str | None)
    """
    # Validasi DULU sebelum pakai len(sql)
    if not sql or not sql.strip():
        log_error("fetch_data: empty query string")
        return {
            "success": False,
            "row_count": 0,
            "data": [],
            "error": "Empty query string",
        }

    log_process(f"fetch_data: executing query ({len(sql)} chars)")

    try:
        connector = get_connector()
        rows = await connector.execute_query(sql)
        log_success(f"fetch_data: returned {len(rows)} rows")
        return {
            "success": True,
            "row_count": len(rows),
            "data": rows,
            "error": None,
        }
    except Exception as exc:
        log_error(f"fetch_data failed: {exc}")
        return {
            "success": False,
            "row_count": 0,
            "data": [],
            "error": str(exc),
        }