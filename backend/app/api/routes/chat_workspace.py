"""
Workspace-aware chat endpoint (v2).
Placeholder pipeline: resolves context + returns echo + insight stub.
Full agent orchestration will be wired in Tahap 8.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.logging import logger
from app.core.security import get_current_user
from app.workspace import audit
from app.workspace.context import get_workspace_context, WorkspaceContext


router = APIRouter(
    prefix="/api/chat/v2",
    tags=["Chat v2"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("")
async def chat_workspace(
    body: ChatRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Workspace-aware chat endpoint.
    Resolves connector + namespace + decrypted keys from workspace context.
    For now returns a routing echo; LangGraph orchestration comes in Tahap 8.
    """
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    await audit.log_query_executed(
        ctx.workspace_id, user["id"], body.message, status="received"
    )

    logger.info(
        f"[PROCESS] Chat request in workspace {ctx.workspace_id} "
        f"(groq={'yes' if ctx.groq_key else 'no'}, "
        f"google={'yes' if ctx.google_key else 'no'}, "
        f"pinecone={'yes' if ctx.pinecone_key else 'no'})"
    )

    return {
        "workspace_id": ctx.workspace_id,
        "workspace_name": ctx.workspace_name,
        "session_id": body.session_id,
        "echo": body.message,
        "ready": {
            "groq": bool(ctx.groq_key),
            "google": bool(ctx.google_key),
            "pinecone": bool(ctx.pinecone_key),
            "metabase": bool(ctx.metabase_key),
            "slack": bool(ctx.slack_webhook),
            "email": bool(ctx.email_key),
        },
        "setup_completed": ctx.setup_completed,
        "note": "Full agent pipeline will be wired in Tahap 8 (Integrasi End-to-End).",
    }


@router.get("/context")
async def get_context(
    ctx: WorkspaceContext = Depends(get_workspace_context),
) -> dict:
    """Debug endpoint: show resolved workspace context (keys masked)."""
    return {
        "workspace_id": ctx.workspace_id,
        "workspace_name": ctx.workspace_name,
        "owner_id": ctx.owner_id,
        "plan": ctx.plan,
        "redis_prefix": ctx.redis_prefix,
        "pinecone_namespace": ctx.pinecone_namespace,
        "setup_completed": ctx.setup_completed,
        "has_keys": {
            "groq": bool(ctx.groq_key),
            "google": bool(ctx.google_key),
            "pinecone": bool(ctx.pinecone_key),
            "metabase": bool(ctx.metabase_key),
            "slack": bool(ctx.slack_webhook),
            "email": bool(ctx.email_key),
        },
    }