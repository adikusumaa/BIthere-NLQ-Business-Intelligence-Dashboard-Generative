"""
Chat API routes with Server-Sent Events (SSE) streaming.

Endpoints:
    POST /api/chat            - submit a prompt and stream agent events
    GET  /api/chat/history    - retrieve chat history for a session

SSE events emitted (per PRJ 8.3):
    start      -> { session_id }
    token      -> { text }      partial answer text
    insight    -> { text }      business insight block
    dashboard  -> { url }       Metabase embed URL
    error      -> { message }   user-friendly error
    done       -> { session_id }
"""

import json
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.graph import compile_graph
from app.api.deps import get_current_user
from app.services.cache import cache
from app.core.logging import log_process, log_info, log_error


router = APIRouter(prefix="/api/chat", tags=["chat"])

SESSION_TTL = 3600
TOKEN_CHUNK_SIZE = 40


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]


def _sse(event: str, data: dict) -> str:
    """Format an SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _chunk_text(text: str, size: int) -> list[str]:
    """Split text into fixed-size chunks for pseudo-streaming."""
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


async def _load_session(session_id: str) -> dict:
    """Load the session state from Redis, or return an empty shell."""
    cached = await cache.get(f"session:{session_id}")
    if cached and isinstance(cached, dict):
        return cached
    return {"session_id": session_id, "messages": []}


async def _save_session(session_id: str, session: dict) -> None:
    """Persist the session state to Redis."""
    await cache.set(f"session:{session_id}", session, ttl=SESSION_TTL)


def _append_message(session: dict, role: str, content: str, **extra: Any) -> None:
    """Append a message to the session's message list."""
    message = {"role": role, "content": content}
    message.update(extra)
    session.setdefault("messages", []).append(message)


async def _stream_events(
    prompt: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """Run the agent graph and stream SSE events."""
    session = await _load_session(session_id)
    _append_message(session, "user", prompt)

    yield _sse("start", {"session_id": session_id})

    try:
        graph = compile_graph()
        result = await graph.ainvoke({"prompt": prompt, "session_id": session_id})
    except Exception as exc:
        log_error(f"chat: graph execution failed: {exc}")
        yield _sse("error", {"message": "Agent execution failed. Please try again."})
        yield _sse("done", {"session_id": session_id})
        return

    final_response = result.get("final_response") or ""
    for chunk in _chunk_text(final_response, TOKEN_CHUNK_SIZE):
        yield _sse("token", {"text": chunk})

    insight = result.get("insight")
    if insight:
        yield _sse("insight", {"text": insight})

    dashboard_url = result.get("dashboard_url")
    if dashboard_url:
        yield _sse("dashboard", {"url": dashboard_url})

    error = result.get("error")
    if error:
        yield _sse("error", {"message": error})

    _append_message(
        session,
        "assistant",
        final_response,
        insight=insight,
        dashboard_url=dashboard_url,
    )
    await _save_session(session_id, session)

    log_info(f"chat: session {session_id} completed")
    yield _sse("done", {"session_id": session_id})


@router.post("")
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Submit a prompt and stream agent events via SSE."""
    session_id = request.session_id or str(uuid.uuid4())
    log_process(
        f"chat: user={user.get('email', 'unknown')} session={session_id}"
    )

    return StreamingResponse(
        _stream_events(request.message, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Retrieve the message history for a session."""
    session = await _load_session(session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=session.get("messages", []),
    )