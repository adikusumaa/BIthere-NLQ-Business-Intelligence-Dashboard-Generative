"""
Unit test untuk MCP tool: fetch_data
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.mcp.tools.fetch_data import fetch_data


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_connector():
    """Connector palsu dengan execute_query() async."""
    connector = AsyncMock()
    connector.execute_query = AsyncMock()
    return connector


# ---------------------------------------------------------------------------
# 1. Validasi input
# ---------------------------------------------------------------------------
async def test_empty_query_returns_error():
    result = await fetch_data("")

    assert result["success"] is False
    assert result["row_count"] == 0
    assert result["data"] == []
    assert result["error"] == "Empty query string"


async def test_whitespace_only_query_returns_error():
    result = await fetch_data("   \n\t  ")

    assert result["success"] is False
    assert result["row_count"] == 0
    assert result["data"] == []
    assert result["error"] == "Empty query string"


async def test_none_query_returns_error():
    result = await fetch_data(None)

    assert result["success"] is False
    assert result["error"] == "Empty query string"


# ---------------------------------------------------------------------------
# 2. Happy path
# ---------------------------------------------------------------------------
async def test_successful_query_returns_rows(mock_connector):
    mock_connector.execute_query.return_value = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    with patch("app.mcp.tools.fetch_data.get_connector", return_value=mock_connector):
        result = await fetch_data("SELECT * FROM users")

    assert result["success"] is True
    assert result["row_count"] == 2
    assert len(result["data"]) == 2
    assert result["data"][0]["name"] == "Alice"
    assert result["error"] is None

    mock_connector.execute_query.assert_awaited_once_with("SELECT * FROM users")


async def test_empty_result_set(mock_connector):
    mock_connector.execute_query.return_value = []

    with patch("app.mcp.tools.fetch_data.get_connector", return_value=mock_connector):
        result = await fetch_data("SELECT * FROM users WHERE 1=0")

    assert result["success"] is True
    assert result["row_count"] == 0
    assert result["data"] == []
    assert result["error"] is None


async def test_sql_passed_through_unchanged(mock_connector):
    """Pastikan SQL tidak dimodifikasi sebelum dikirim ke connector."""
    mock_connector.execute_query.return_value = []

    sql = "SELECT id, name FROM users WHERE age > 18 ORDER BY name LIMIT 10"

    with patch("app.mcp.tools.fetch_data.get_connector", return_value=mock_connector):
        await fetch_data(sql)

    mock_connector.execute_query.assert_awaited_once_with(sql)


# ---------------------------------------------------------------------------
# 3. Error handling
# ---------------------------------------------------------------------------
async def test_query_exception_is_caught(mock_connector):
    mock_connector.execute_query.side_effect = Exception("DB connection lost")

    with patch("app.mcp.tools.fetch_data.get_connector", return_value=mock_connector):
        result = await fetch_data("SELECT * FROM users")

    assert result["success"] is False
    assert result["row_count"] == 0
    assert result["data"] == []
    assert "DB connection lost" in result["error"]


async def test_get_connector_exception_is_caught():
    with patch(
        "app.mcp.tools.fetch_data.get_connector",
        side_effect=Exception("Connector config missing"),
    ):
        result = await fetch_data("SELECT 1")

    assert result["success"] is False
    assert result["row_count"] == 0
    assert result["data"] == []
    assert "Connector config missing" in result["error"]


async def test_sql_syntax_error_from_connector(mock_connector):
    mock_connector.execute_query.side_effect = Exception(
        'syntax error at or near "SELEC"'
    )

    with patch("app.mcp.tools.fetch_data.get_connector", return_value=mock_connector):
        result = await fetch_data("SELEC * FROM users")

    assert result["success"] is False
    assert "syntax error" in result["error"]