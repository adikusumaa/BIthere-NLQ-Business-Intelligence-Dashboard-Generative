"""
Workspace-aware chat endpoint v2 with SSE streaming.
Full agent pipeline via graph_v2, using workspace context.
"""

import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.context import AgentContext
from app.agents.graph_v2 import compile_graph_v2
from app.core.logging import log_error, log_info, log_process
from app.core.security import get_current_user
from app.services.cache import cache
from app.workspace import audit
from app.workspace.context import WorkspaceContext, get_workspace_context
from app.workspace.data_sources import (
    DataSourceNotFoundError,
    get_workspace_connector,
)


router = APIRouter(prefix="/api/chat/v2", tags=["Chat v2"])


SESSION_TTL = 3600
TOKEN_CHUNK_SIZE = 40


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _chunk_text(text: str, size: int) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


async def _load_session(redis_prefix: str, session_id: str) -> dict:
    cached = await cache.get(f"{redis_prefix}session:{session_id}")
    if cached and isinstance(cached, dict):
        return cached
    return {"session_id": session_id, "messages": []}


async def _save_session(redis_prefix: str, session_id: str, session: dict) -> None:
    await cache.set(f"{redis_prefix}session:{session_id}", session, ttl=SESSION_TTL)


def _append_message(session: dict, role: str, content: str, **extra) -> None:
    msg = {"role": role, "content": content}
    msg.update(extra)
    session.setdefault("messages", []).append(msg)


async def _stream_events(
    prompt: str,
    session_id: str,
    ctx: WorkspaceContext,
    user_email: str,
    user_id: str,
) -> AsyncGenerator[str, None]:
    """Run graph_v2 and stream SSE events."""

    session = await _load_session(ctx.redis_prefix, session_id)
    _append_message(session, "user", prompt)

    yield _sse("start", {"session_id": session_id, "workspace_id": ctx.workspace_id})

    connector = None
    try:
        connector = await get_workspace_connector(ctx.workspace_id)
    except DataSourceNotFoundError:
        yield _sse("error", {
            "message": "Workspace has no data source configured. "
                       "Please complete the setup wizard first."
        })
        yield _sse("done", {"session_id": session_id})
        return
    except Exception as exc:
        log_error(f"chat_v2: connector resolution failed: {exc}")
        yield _sse("error", {"message": f"Cannot resolve data source: {exc}"})
        yield _sse("done", {"session_id": session_id})
        return

    agent_ctx = AgentContext.from_workspace_context(ctx, connector=connector)

    try:
        graph = compile_graph_v2()
        result = await graph.ainvoke({
            "prompt": prompt,
            "session_id": session_id,
            "user_email": user_email,
            "context": agent_ctx,
        })
    except Exception as exc:
        log_error(f"chat_v2: graph execution failed: {exc}")
        yield _sse("error", {"message": "Agent execution failed. Please try again."})
        yield _sse("done", {"session_id": session_id})
        return
    finally:
        if connector:
            try:
                await connector.disconnect()
            except Exception:
                pass

    final_response = result.get("final_response") or ""
    for chunk in _chunk_text(final_response, TOKEN_CHUNK_SIZE):
        yield _sse("token", {"text": chunk})

    insight = result.get("insight")
    if insight:
        yield _sse("insight", {"text": insight})

    dashboard_url = result.get("dashboard_url")
    dashboard_mb_id = result.get("dashboard_metabase_id")
    if dashboard_url:
        yield _sse("dashboard", {
            "url": dashboard_url,
            "metabase_id": dashboard_mb_id,
        })

    error = result.get("error")
    if error:
        yield _sse("error", {"message": error})

    _append_message(
        session, "assistant", final_response,
        insight=insight, dashboard_url=dashboard_url,
    )
    await _save_session(ctx.redis_prefix, session_id, session)

    try:
        await audit.log_query_executed(
            ctx.workspace_id, user_id, prompt,
            status="error" if error else "success",
        )
    except Exception as exc:
        log_error(f"chat_v2: audit log failed: {exc}")

    log_info(f"chat_v2: session {session_id} done (workspace={ctx.workspace_id})")
    yield _sse("done", {"session_id": session_id})


@router.post("")
async def chat_workspace(
    body: ChatRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Submit a prompt and stream agent events via SSE (workspace-aware)."""

    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    session_id = body.session_id or str(uuid.uuid4())
    log_process(
        f"chat_v2: user={user.get('email')} workspace={ctx.workspace_id} "
        f"session={session_id}"
    )

    return StreamingResponse(
        _stream_events(body.message, session_id, ctx, user.get("email", ""), user["id"]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/context")
async def get_context(
    ctx: WorkspaceContext = Depends(get_workspace_context),
) -> dict:
    """Debug: show resolved workspace context (keys masked)."""
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


@router.get("/history")
async def chat_history(
    session_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
) -> dict:
    session = await _load_session(ctx.redis_prefix, session_id)
    return {
        "session_id": session_id,
        "workspace_id": ctx.workspace_id,
        "messages": session.get("messages", []),
    }