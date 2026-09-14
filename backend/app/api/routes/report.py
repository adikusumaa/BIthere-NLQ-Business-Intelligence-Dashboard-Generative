"""
Report API routes.

Delivers insights to one or more channels: PDF export, Slack, Email.
All delivery goes through MCP tools from step 5.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.mcp.tools.export_pdf import export_pdf
from app.mcp.tools.send_slack import send_slack
from app.mcp.tools.send_email import send_email
from app.core.logging import log_process, log_error


router = APIRouter(prefix="/api/report", tags=["report"])


VALID_CHANNELS = {"pdf", "slack", "email"}


class SendReportRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    insight: str = Field(..., min_length=1, max_length=20000)
    dashboard_url: str | None = None
    channels: list[str] = Field(default_factory=lambda: ["pdf"])
    kpis: list[dict] | None = None
    slack_message: str | None = None
    email_recipient: str | None = None
    email_subject: str | None = None


class ChannelResult(BaseModel):
    channel: str
    success: bool
    detail: dict[str, Any] | None = None
    error: str | None = None


class SendReportResponse(BaseModel):
    success: bool
    results: list[ChannelResult]
    error: str | None


async def _dispatch_pdf(payload: SendReportRequest) -> ChannelResult:
    result = await export_pdf(
        title=payload.title,
        insight=payload.insight,
        dashboard_url=payload.dashboard_url,
        kpis=payload.kpis,
        capture_screenshot=False,
    )
    return ChannelResult(
        channel="pdf",
        success=bool(result.get("success")),
        detail={
            "filename": result.get("filename"),
            "pdf_path": result.get("pdf_path"),
            "engine": result.get("engine"),
        },
        error=result.get("error"),
    )


async def _dispatch_slack(payload: SendReportRequest) -> ChannelResult:
    message = payload.slack_message or (
        f"*{payload.title}*\n\n{payload.insight}"
    )
    result = await send_slack(message, payload.dashboard_url)
    return ChannelResult(
        channel="slack",
        success=bool(result.get("success")),
        detail={"channel": "slack"},
        error=result.get("error"),
    )


async def _dispatch_email(payload: SendReportRequest) -> ChannelResult:
    if not payload.email_recipient:
        return ChannelResult(
            channel="email",
            success=False,
            error="email_recipient is required for email channel",
        )

    subject = payload.email_subject or f"[BIthere] {payload.title}"
    result = await send_email(
        to_email=payload.email_recipient,
        subject=subject,
        body=payload.insight,
        is_html=False,
    )
    return ChannelResult(
        channel="email",
        success=bool(result.get("success")),
        detail={"to": payload.email_recipient},
        error=result.get("error"),
    )


@router.post("", response_model=SendReportResponse)
async def send_report(
    payload: SendReportRequest,
    user: dict = Depends(get_current_user),
) -> SendReportResponse:
    """Deliver a report to the requested channels."""
    log_process(
        f"report: user={user.get('email')} "
        f"channels={payload.channels} title='{payload.title[:40]}'"
    )

    if not payload.channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one channel is required",
        )

    invalid = [c for c in payload.channels if c not in VALID_CHANNELS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channels: {invalid}. Allowed: {sorted(VALID_CHANNELS)}",
        )

    results: list[ChannelResult] = []

    for channel in payload.channels:
        try:
            if channel == "pdf":
                results.append(await _dispatch_pdf(payload))
            elif channel == "slack":
                results.append(await _dispatch_slack(payload))
            elif channel == "email":
                results.append(await _dispatch_email(payload))
        except Exception as exc:
            log_error(f"report: channel '{channel}' raised: {exc}")
            results.append(
                ChannelResult(
                    channel=channel,
                    success=False,
                    error=str(exc),
                )
            )

    overall = all(r.success for r in results)
    return SendReportResponse(success=overall, results=results, error=None)