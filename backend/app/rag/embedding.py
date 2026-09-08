"""
Embedding client using Google Generative Language REST API v1.
Includes Redis caching to avoid repeated API calls.
"""

import asyncio
import hashlib
from typing import List

import requests

from app.core.config import settings
from app.core.logging import logger
from app.services.cache import cache


EMBEDDING_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1/models/"
    f"{settings.EMBEDDING_MODEL}:embedContent"
)


def _get_cache_key(text: str) -> str:
    """
    Generate cache key based on text hash.
    """

    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return f"embedding:{text_hash}"


def _call_embedding_api(text: str) -> List[float]:
    """
    Call Google Generative Language REST API v1 for embedding.
    """

    response = requests.post(
        EMBEDDING_ENDPOINT,
        params={"key": settings.GOOGLE_API_KEY},
        json={"content": {"parts": [{"text": text}]}},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["embedding"]["values"]


async def embed_text(text: str) -> List[float]:
    """
    Get embedding for text with Redis caching.
    """

    cache_key = _get_cache_key(text)

    cached = await cache.get(cache_key)
    if cached:
        logger.info(f"Embedding cache hit for key {cache_key}")
        return cached

    logger.process(f"Calling embedding API for text: {text[:50]}...")
    embedding = await asyncio.to_thread(_call_embedding_api, text)

    await cache.set(cache_key, embedding, ttl=settings.CACHE_EMBEDDING_TTL)
    logger.success("Embedding generated and cached")

    return embedding