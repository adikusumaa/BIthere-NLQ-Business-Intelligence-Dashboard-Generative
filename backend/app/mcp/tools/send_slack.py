"""
MCP tool: send_slack
Send messages to Slack via incoming webhook.
"""

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import log_process, log_success, log_error


async def send_slack(
    message: str,
    dashboard_url: str | None = None,
) -> dict[str, Any]:
    """
    Send a message to Slack via webhook.

    Args:
        message: The main message text (supports Slack markdown).
        dashboard_url: Optional dashboard URL to attach as a link.

    Returns:
        dict with keys:
            - success (bool)
            - channel (str)
            - error (str | None)
    """
    log_process(f"send_slack: preparing message ({len(message)} chars)")

    if not settings.SLACK_WEBHOOK_URL:
        log_error("send_slack: SLACK_WEBHOOK_URL not configured")
        return {
            "success": False,
            "channel": "slack",
            "error": "SLACK_WEBHOOK_URL not configured in .env",
        }

    if not message or not message.strip():
        log_error("send_slack: empty message")
        return {
            "success": False,
            "channel": "slack",
            "error": "Message is empty",
        }

    text = f"*BIthere Report*\n\n{message}"
    if dashboard_url:
        text += f"\n\n<{dashboard_url}|View Dashboard>"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                settings.SLACK_WEBHOOK_URL,
                json={"text": text},
            )
            response.raise_for_status()
        log_success("send_slack: message delivered")
        return {
            "success": True,
            "channel": "slack",
            "error": None,
        }
    except httpx.HTTPStatusError as exc:
        log_error(f"send_slack: HTTP {exc.response.status_code}")
        return {
            "success": False,
            "channel": "slack",
            "error": f"Slack returned HTTP {exc.response.status_code}",
        }
    except Exception as exc:
        log_error(f"send_slack failed: {exc}")
        return {
            "success": False,
            "channel": "slack",
            "error": str(exc),
        }