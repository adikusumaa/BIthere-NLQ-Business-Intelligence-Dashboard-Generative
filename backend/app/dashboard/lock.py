"""
Redis mutex per dashboard. Prevents concurrent apply.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger


LOCK_TTL_SECONDS = 30
LOCK_PREFIX = "dashboard_lock:"

_redis: aioredis.Redis | None = None
_redis_loop = None


def _get_redis() -> aioredis.Redis:
    global _redis, _redis_loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if _redis is None or _redis_loop is not loop:
        _redis = aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        _redis_loop = loop
    return _redis


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


@asynccontextmanager
async def lock(dashboard_id: str, timeout_seconds: int = LOCK_TTL_SECONDS) -> AsyncIterator[str]:
    """
    Acquire a Redis mutex for a dashboard.

    Usage:
        async with lock("dash-1"):
            ...
    """
    redis = _get_redis()
    key = f"{LOCK_PREFIX}{dashboard_id}"
    token = uuid.uuid4().hex

    acquired = await redis.set(key, token, nx=True, ex=timeout_seconds)
    if not acquired:
        raise LockError(
            f"Dashboard {dashboard_id} is locked by another operation. Try again."
        )

    logger.info(f"[PROCESS] Lock acquired: {dashboard_id}")

    try:
        yield token
    finally:
        try:
            current = await redis.get(key)
            if current == token:
                await redis.delete(key)
                logger.info(f"[PROCESS] Lock released: {dashboard_id}")
        except Exception as exc:
            logger.warning(f"[WARNING] Lock release failed: {exc}")