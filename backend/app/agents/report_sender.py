import httpx
from app.core.config import settings
from app.core.logging import log_info, log_error


async def send_slack(insight: str, dashboard_url: str | None = None) -> bool:
    """Send report to Slack via incoming webhook."""
    if not settings.SLACK_WEBHOOK_URL:
        log_error("SLACK_WEBHOOK_URL not configured")
        return False

    text = f"*BIthere Report*\n\n{insight}"
    if dashboard_url:
        text += f"\n\n<{dashboard_url}|View Dashboard>"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(settings.SLACK_WEBHOOK_URL, json={"text": text})
            response.raise_for_status()
        log_info("Slack report sent")
        return True
    except Exception as exc:
        log_error(f"Slack send failed: {exc}")
        return False


async def send_report(
    insight: str,
    channel: str,
    dashboard_url: str | None = None,
) -> dict:
    """Dispatcher for report sending."""
    if channel == "slack":
        ok = await send_slack(insight, dashboard_url)
        return {"sent": ok, "channel": "slack"}
    return {"sent": False, "channel": channel, "reason": "unsupported channel"}