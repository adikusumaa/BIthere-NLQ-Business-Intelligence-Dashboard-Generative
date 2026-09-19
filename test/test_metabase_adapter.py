"""
Tests for metabase_adapter (mocked HTTP).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.dashboard import metabase_adapter as ma
from app.dashboard.metabase_adapter import MetabaseAdapterError, MetabaseSession


# =====================================================
# Session login
# =====================================================

async def test_login_success():
    session = MetabaseSession("http://mb:3000", "admin", "pass")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "sess-123"}

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)):
        sid = await session.login()
        assert sid == "sess-123"
        assert session.session_id == "sess-123"


async def test_login_failure():
    session = MetabaseSession("http://mb:3000", "admin", "bad")
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "unauthorized"

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(MetabaseAdapterError):
            await session.login()


async def test_headers_require_login():
    session = MetabaseSession("http://mb:3000", "admin", "pass")
    with pytest.raises(MetabaseAdapterError):
        session._headers()


# =====================================================
# create_card
# =====================================================

async def test_create_card():
    session = MetabaseSession("http://mb:3000", "admin", "pass")
    session.session_id = "sess"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": 42}

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)):
        card_id = await session.create_card(
            title="Test", sql="SELECT 1", chart_type="bar",
        )
        assert card_id == 42


async def test_create_card_no_sql_uses_dummy():
    session = MetabaseSession("http://mb:3000", "admin", "pass")
    session.session_id = "sess"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": 1}

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)) as mock:
        await session.create_card(title="X", sql=None, chart_type="text")
        payload = mock.call_args.kwargs["json"]
        assert "SELECT 1 AS dummy" in payload["dataset_query"]["native"]["query"]


async def test_create_card_failure():
    session = MetabaseSession("http://mb:3000", "admin", "pass")
    session.session_id = "sess"

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "server error"

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(MetabaseAdapterError):
            await session.create_card(title="X", sql="SELECT 1", chart_type="bar")


# =====================================================
# execute_actions
# =====================================================

async def test_execute_create_and_attach():
    session = MagicMock()
    session.create_card = AsyncMock(return_value=101)
    session.add_card_to_dashboard = AsyncMock(return_value=202)

    actions = [
        {"action": "create_card", "card_id": "card-a", "title": "A", "chart_type": "bar", "sql": "SELECT 1"},
        {"action": "attach_card_to_dashboard", "card_id": "card-a", "position": {"row": 0, "col": 0, "size_x": 6, "size_y": 3}},
    ]

    results = await ma.execute_actions(session, dashboard_id=5, actions=actions)
    assert len(results) == 2
    assert results[0]["ok"] is True
    assert results[1]["ok"] is True


async def test_execute_unknown_action():
    session = MagicMock()
    results = await ma.execute_actions(
        session, dashboard_id=5, actions=[{"action": "wat"}]
    )
    assert results[0]["ok"] is False


async def test_execute_handles_exception_per_action():
    session = MagicMock()
    session.create_card = AsyncMock(side_effect=Exception("boom"))

    results = await ma.execute_actions(
        session, dashboard_id=5,
        actions=[{"action": "create_card", "card_id": "x", "title": "X", "chart_type": "bar", "sql": "SELECT 1"}],
    )
    assert results[0]["ok"] is False
    assert "boom" in results[0]["error"]