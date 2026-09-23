"""
Embedding client using Google Generative Language REST API v1.
Includes Redis caching and exponential backoff for 429 rate limits.
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


async def _call_with_retry(
    text: str,
    api_key: str,
    max_retries: int = 5,
) -> List[float]:
    """Call embedding API with exponential backoff for 429 / 5xx."""
    delay = 5
    last_error = None
    for attempt in range(max_retries):
        try:
            return await asyncio.to_thread(_call_embedding_api, text, api_key)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            last_error = exc
            if status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                logger.warning(
                    f"[WARNING] Embedding {status} error, waiting {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("Embedding retries exhausted")


async def embed_text(
    text: str,
    api_key: Optional[str] = None,
    redis_prefix: str = "",
) -> List[float]:
    key = api_key or settings.GOOGLE_API_KEY
    if not key:
        raise ValueError("No Google API key available for embedding")

    cache_key = _cache_key(text, redis_prefix)

    cached = await cache.get(cache_key)
    if cached:
        logger.info(f"[PROCESS] Embedding cache hit: {cache_key}")
        return cached

    logger.info(f"[PROCESS] Calling embedding API for text: {text[:50]}...")
    embedding = await _call_with_retry(text, key)

    await cache.set(cache_key, embedding, ttl=settings.CACHE_EMBEDDING_TTL)
    logger.info("[SUCCESS] Embedding generated and cached")
    return embedding


async def embed_batch(
    texts: List[str],
    api_key: Optional[str] = None,
    redis_prefix: str = "",
) -> List[List[float]]:
    results = []
    for t in texts:
        results.append(await embed_text(t, api_key=api_key, redis_prefix=redis_prefix))
    return results