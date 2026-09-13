"""
Unit test untuk MCP tool: send_slack
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.mcp.tools.send_slack import send_slack


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def mock_settings(monkeypatch):
    """Set SLACK_WEBHOOK_URL default yang valid untuk semua test."""
    from app.core import config
    monkeypatch.setattr(
        config.settings,
        "SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/services/TEST/XXX",
    )
    return config.settings


@pytest.fixture
def mock_httpx_client():
    """
    Patch httpx.AsyncClient supaya tidak benar-benar hit network.

    Yield:
        (mock_client_class, mock_post, mock_response)
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()  # tidak raise = sukses

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)

    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__ = AsyncMock(
        return_value=mock_client_instance
    )
    mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("app.mcp.tools.send_slack.httpx.AsyncClient", mock_client_class):
        yield mock_client_class, mock_client_instance.post, mock_response


# ===========================================================================
# 1. CONFIG CHECK
# ===========================================================================

async def test_missing_webhook_url_returns_error(monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "SLACK_WEBHOOK_URL", "")

    result = await send_slack("Hello")

    assert result["success"] is False
    assert result["channel"] == "slack"
    assert "SLACK_WEBHOOK_URL not configured" in result["error"]


async def test_missing_webhook_url_none(monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "SLACK_WEBHOOK_URL", None)

    result = await send_slack("Hello")

    assert result["success"] is False
    assert "SLACK_WEBHOOK_URL not configured" in result["error"]


# ===========================================================================
# 2. VALIDASI MESSAGE
# ===========================================================================

async def test_empty_message_returns_error(mock_settings):
    result = await send_slack("")

    assert result["success"] is False
    assert result["channel"] == "slack"
    assert result["error"] == "Message is empty"


async def test_whitespace_only_message_returns_error(mock_settings):
    result = await send_slack("   \n\t  ")

    assert result["success"] is False
    assert result["error"] == "Message is empty"


async def test_none_message_returns_error(mock_settings):
    result = await send_slack(None)

    assert result["success"] is False
    assert result["error"] == "Message is empty"


# ===========================================================================
# 3. HAPPY PATH
# ===========================================================================

async def test_successful_send(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client

    result = await send_slack("Halo dunia")

    assert result["success"] is True
    assert result["channel"] == "slack"
    assert result["error"] is None

    mock_post.assert_awaited_once()
    kwargs = mock_post.call_args.kwargs
    assert "*BIthere Report*" in kwargs["json"]["text"]
    assert "Halo dunia" in kwargs["json"]["text"]


async def test_send_to_correct_url(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client

    await send_slack("Halo")

    args, _ = mock_post.call_args
    assert args[0] == mock_settings.SLACK_WEBHOOK_URL


async def test_dashboard_url_appended(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client

    await send_slack(
        "Laporan siap",
        dashboard_url="https://example.com/dashboard/123",
    )

    text = mock_post.call_args.kwargs["json"]["text"]
    assert "Laporan siap" in text
    assert "<https://example.com/dashboard/123|View Dashboard>" in text


async def test_dashboard_url_not_provided(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client

    await send_slack("Halo")

    text = mock_post.call_args.kwargs["json"]["text"]
    assert "View Dashboard" not in text


async def test_message_with_slack_markdown(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client

    msg = "*Bold* _italic_ `code`"
    await send_slack(msg)

    text = mock_post.call_args.kwargs["json"]["text"]
    assert msg in text


# ===========================================================================
# 4. ERROR HANDLING
# ===========================================================================

async def test_http_status_error(mock_settings, mock_httpx_client):
    _, _, mock_response = mock_httpx_client

    mock_response.status_code = 404
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=httpx.Request("POST", "https://hooks.slack.com/x"),
            response=mock_response,
        )
    )

    result = await send_slack("Halo")

    assert result["success"] is False
    assert result["channel"] == "slack"
    assert "404" in result["error"]
    assert "HTTP 404" in result["error"]


async def test_network_error_is_caught(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client
    mock_post.side_effect = httpx.ConnectError("Connection refused")

    result = await send_slack("Halo")

    assert result["success"] is False
    assert "Connection refused" in result["error"]


async def test_generic_exception_is_caught(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client
    mock_post.side_effect = Exception("Something unexpected")

    result = await send_slack("Halo")

    assert result["success"] is False
    assert "Something unexpected" in result["error"]


async def test_timeout_exception(mock_settings, mock_httpx_client):
    _, mock_post, _ = mock_httpx_client
    mock_post.side_effect = httpx.TimeoutException("Request timed out")

    result = await send_slack("Halo")

    assert result["success"] is False
    assert "timed out" in result["error"].lower()