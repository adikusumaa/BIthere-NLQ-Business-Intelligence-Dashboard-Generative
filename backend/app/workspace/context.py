"""
Workspace context resolution.
Resolves workspace_id from JWT, loads workspace metadata,
decrypts required API keys, and caches the context in Redis.
"""

from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_current_user
from app.workspace.secrets import get_secret_or_none
from app.workspace.service import get_workspace, WorkspaceNotFoundError
import asyncio
from typing import Optional

_redis: Optional[aioredis.Redis] = None
_redis_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_redis() -> aioredis.Redis:
    """
    Return a Redis client bound to the current event loop.
    Rebuilds the client when the loop changes (e.g., across tests or worker reloads).
    """
    global _redis, _redis_loop

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _redis is None or _redis_loop is not current_loop:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        _redis_loop = current_loop

    return _redis


class WorkspaceContext(BaseModel):
    """
    Resolved context for a single request.
    Contains workspace metadata plus decrypted secrets the agent may need.
    """
    workspace_id: str
    workspace_name: str
    owner_id: str
    plan: str
    redis_prefix: str
    pinecone_namespace: str

    groq_key: Optional[str] = None
    google_key: Optional[str] = None
    pinecone_key: Optional[str] = None
    slack_webhook: Optional[str] = None
    email_key: Optional[str] = None
    metabase_key: Optional[str] = None

    setup_completed: bool = False


def _redis_key(workspace_id: str) -> str:
    return f"{settings.REDIS_WORKSPACE_PREFIX}context:{workspace_id}"


async def _build_context(workspace_id: str) -> WorkspaceContext:
    """Fetch workspace metadata + decrypt all needed secrets."""
    try:
        workspace = await get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found",
        )

    ctx = WorkspaceContext(
        workspace_id=workspace["id"],
        workspace_name=workspace["name"],
        owner_id=workspace["owner_id"],
        plan=workspace.get("plan", "free"),
        redis_prefix=f"{settings.REDIS_WORKSPACE_PREFIX}{workspace['id']}:",
        pinecone_namespace=f"workspace_{workspace['id']}",
        setup_completed=workspace.get("setup_completed", False),
        groq_key=await get_secret_or_none(workspace["id"], "groq"),
        google_key=await get_secret_or_none(workspace["id"], "google"),
        pinecone_key=await get_secret_or_none(workspace["id"], "pinecone"),
        slack_webhook=await get_secret_or_none(workspace["id"], "slack"),
        email_key=await get_secret_or_none(workspace["id"], "email"),
        metabase_key=await get_secret_or_none(workspace["id"], "metabase"),
    )
    return ctx


async def resolve_workspace(workspace_id: str) -> WorkspaceContext:
    """
    Resolve workspace context with Redis caching (TTL 5 min).
    Falls back to DB on cache miss or cache error.
    """
    key = _redis_key(workspace_id)
    try:
        cached = await _get_redis().get(key)
        if cached:
            return WorkspaceContext.model_validate_json(cached)
    except Exception as exc:
        logger.warning(f"[WARNING] Redis read failed, falling back to DB: {exc}")

    ctx = await _build_context(workspace_id)

    try:
        await _get_redis().setex(
            key,
            settings.CACHE_WORKSPACE_CONTEXT_TTL,
            ctx.model_dump_json(),
        )
    except Exception as exc:
        logger.warning(f"[WARNING] Redis write failed: {exc}")

    return ctx


async def invalidate_workspace_context(workspace_id: str) -> None:
    """Remove cached context (call after secret rotation, etc.)."""
    try:
        await _get_redis().delete(_redis_key(workspace_id))
        logger.info(f"[SUCCESS] Workspace context invalidated: {workspace_id}")
    except Exception as exc:
        logger.warning(f"[WARNING] Redis delete failed: {exc}")


async def get_workspace_context(
    x_workspace_id: Optional[str] = Header(default=None, alias="X-Workspace-ID"),
    user=Depends(get_current_user),
) -> WorkspaceContext:
    """
    FastAPI dependency: resolve workspace context from header X-Workspace-ID.
    Validates that the authenticated user is a member of the workspace.
    """
    if not x_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Workspace-ID' is required",
        )

    ctx = await resolve_workspace(x_workspace_id)

    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cannot determine user id from token",
        )

    from app.workspace.service import list_members
    members = await list_members(x_workspace_id)
    if not any(m["user_id"] == user_id for m in members):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )

    return ctx