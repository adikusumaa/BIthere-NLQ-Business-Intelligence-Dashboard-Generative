"""
Undo/Redo stack per session, backed by Redis lists.
Each entry stores the patch dict that produced a version.
"""

import json
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger


UNDO_TTL = 3600


class UndoRedoError(Exception):
    """Raised when undo/redo cannot be performed."""


_redis: aioredis.Redis | None = None
_redis_loop = None


def _get_redis() -> aioredis.Redis:
    global _redis, _redis_loop
    try:
        import asyncio
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if _redis is None or _redis_loop is not loop:
        import asyncio
        _redis = aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        _redis_loop = loop
    return _redis


def _undo_key(session_id: str) -> str:
    return f"undo:{session_id}"


def _redo_key(session_id: str) -> str:
    return f"redo:{session_id}"


async def push_undo(session_id: str, patch: Any) -> None:
    """
    Push a patch onto the undo stack and clear the redo stack
    (standard undo/redo semantics).
    """
    redis = _get_redis()
    payload = json.dumps(
        patch.model_dump(mode="json") if hasattr(patch, "model_dump") else patch,
        default=str,
    )
    await redis.lpush(_undo_key(session_id), payload)
    await redis.expire(_undo_key(session_id), UNDO_TTL)
    await redis.delete(_redo_key(session_id))
    logger.info(f"[PROCESS] Undo push for session {session_id}")


async def undo(session_id: str) -> Optional[Dict[str, Any]]:
    """Pop from undo, push onto redo, return the patch dict."""
    redis = _get_redis()
    payload = await redis.lpop(_undo_key(session_id))
    if not payload:
        return None
    await redis.lpush(_redo_key(session_id), payload)
    await redis.expire(_redo_key(session_id), UNDO_TTL)
    logger.info(f"[PROCESS] Undo popped for session {session_id}")
    return json.loads(payload)


async def redo(session_id: str) -> Optional[Dict[str, Any]]:
    """Pop from redo, push back onto undo, return the patch dict."""
    redis = _get_redis()
    payload = await redis.lpop(_redo_key(session_id))
    if not payload:
        return None
    await redis.lpush(_undo_key(session_id), payload)
    await redis.expire(_undo_key(session_id), UNDO_TTL)
    logger.info(f"[PROCESS] Redo popped for session {session_id}")
    return json.loads(payload)


async def clear_stack(session_id: str) -> None:
    redis = _get_redis()
    await redis.delete(_undo_key(session_id))
    await redis.delete(_redo_key(session_id))