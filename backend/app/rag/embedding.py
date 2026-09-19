"""
Embedding client using Google Generative Language REST API v1.
Supports workspace-scoped API keys and per-workspace Redis cache prefix.
"""

import asyncio
import hashlib
from typing import List, Optional

import requests

from app.core.config import settings
from app.core.logging import logger
from app.services.cache import cache


def _endpoint() -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1/models/"
        f"{settings.EMBEDDING_MODEL}:embedContent"
    )


def _cache_key(text: str, prefix: str) -> str:
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return f"{prefix}embedding:{text_hash}"


def _call_embedding_api(text: str, api_key: str) -> List[float]:
    response = requests.post(
        _endpoint(),
        params={"key": api_key},
        json={"content": {"parts": [{"text": text}]}},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["embedding"]["values"]


async def embed_text(
    text: str,
    api_key: Optional[str] = None,
    redis_prefix: str = "",
) -> List[float]:
    """
    Get embedding for text with Redis caching.
    If api_key is None, falls back to platform-level GOOGLE_API_KEY (v1 behavior).
    """
    key = api_key or settings.GOOGLE_API_KEY
    if not key:
        raise ValueError("No Google API key available for embedding")

    cache_key = _cache_key(text, redis_prefix)

    cached = await cache.get(cache_key)
    if cached:
        logger.info(f"[PROCESS] Embedding cache hit: {cache_key}")
        return cached

    logger.info(f"[PROCESS] Calling embedding API for text: {text[:50]}...")
    embedding = await asyncio.to_thread(_call_embedding_api, text, key)

    await cache.set(cache_key, embedding, ttl=settings.CACHE_EMBEDDING_TTL)
    logger.info("[SUCCESS] Embedding generated and cached")
    return embedding


async def embed_batch(
    texts: List[str],
    api_key: Optional[str] = None,
    redis_prefix: str = "",
) -> List[List[float]]:
    """Embed a batch of texts sequentially (Google v1 API has no batch)."""
    results = []
    for t in texts:
        results.append(await embed_text(t, api_key=api_key, redis_prefix=redis_prefix))
    return results