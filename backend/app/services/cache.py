"""
Redis cache service for BIthere.
Handles caching for query results, LLM responses, embeddings, and dashboards.
"""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import logger


class RedisCache:
    """
    Redis cache wrapper with async operations.
    """

    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache by key.
        Returns None if key does not exist.
        """

        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as error:
            logger.error(f"Cache get failed for key {key}: {str(error)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Store value in cache with TTL.
        Returns True if successful.
        """

        try:
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as error:
            logger.error(f"Cache set failed for key {key}: {str(error)}")
            return False

    async def delete(self, pattern: str) -> int:
        """
        Delete keys matching pattern.
        Returns number of keys deleted.
        """

        try:
            keys = await self.client.keys(pattern)
            if not keys:
                return 0
            return await self.client.delete(*keys)
        except Exception as error:
            logger.error(f"Cache delete failed for pattern {pattern}: {str(error)}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        """

        try:
            return await self.client.exists(key) > 0
        except Exception as error:
            logger.error(f"Cache exists check failed for key {key}: {str(error)}")
            return False

    async def close(self) -> None:
        """
        Close Redis connection.
        """

        await self.client.close()
        logger.info("Redis connection closed")


cache = RedisCache()