"""
MCP tool: send_email
Send emails via SMTP (Mailtrap, Gmail, etc.).
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

from app.core.config import settings
from app.core.logging import log_process, log_success, log_error


def _build_message(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
) -> MIMEMultipart:
    """Build a MIME email message."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER or "bithere@localhost"
    msg["To"] = to_email

    mime_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, mime_type, "utf-8"))
    return msg


def _send_sync(to_email: str, msg: MIMEMultipart) -> None:
    """Blocking SMTP send (called inside a thread)."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
) -> dict[str, Any]:
    """
    Send an email via SMTP.

    Args:
        to_email: Recipient email address.
        subject: Email subject.
        body: Email body (plain text or HTML).
        is_html: If True, treat body as HTML.

    Returns:
        dict with keys:
            - success (bool)
            - channel (str)
            - to (str)
            - error (str | None)
    """
    log_process(f"send_email: preparing for {to_email} (subject={subject[:40]}...)")

    if not settings.SMTP_HOST or not settings.SMTP_PORT:
        log_error("send_email: SMTP not configured")
        return {
            "success": False,
            "channel": "email",
            "to": to_email,
            "error": "SMTP_HOST or SMTP_PORT not configured",
        }

    if not to_email or "@" not in to_email:
        log_error(f"send_email: invalid recipient '{to_email}'")
        return {
            "success": False,
            "channel": "email",
            "to": to_email,
            "error": "Invalid recipient email address",
        }

    if not subject.strip() or not body.strip():
        log_error("send_email: empty subject or body")
        return {
            "success": False,
            "channel": "email",
            "to": to_email,
            "error": "Subject and body must not be empty",
        }

    try:
        import asyncio
        msg = _build_message(to_email, subject, body, is_html)
        await asyncio.to_thread(_send_sync, to_email, msg)
        log_success(f"send_email: delivered to {to_email}")
        return {
            "success": True,
            "channel": "email",
            "to": to_email,
            "error": None,
        }
    except smtplib.SMTPAuthenticationError:
        log_error("send_email: SMTP authentication failed")
        return {
            "success": False,
            "channel": "email",
            "to": to_email,
            "error": "SMTP authentication failed (check SMTP_USER/SMTP_PASSWORD)",
        }
    except Exception as exc:
        log_error(f"send_email failed: {exc}")
        return {
            "success": False,
            "channel": "email",
            "to": to_email,
            "error": str(exc),
        }