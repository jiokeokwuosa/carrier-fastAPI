"""Optional Redis cache with graceful fallback when Redis is unavailable."""

import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Thin wrapper around Redis for hot-path caching (e.g. carrier OAuth tokens).

    When REDIS_URL is not set, all operations are no-ops and callers fall back to DB.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self._client = None
        self._url = redis_url if redis_url is not None else settings.REDIS_URL

    async def connect(self) -> None:
        if not self._url:
            return
        try:
            import redis.asyncio as redis

            self._client = redis.from_url(self._url, decode_responses=True)
            await self._client.ping()
            logger.info("Redis cache connected")
        except Exception:
            logger.warning("Redis unavailable — falling back to database cache")
            self._client = None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            raw = await self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            logger.warning("Redis GET failed for key %s", key)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if not self._client:
            return
        try:
            await self._client.setex(key, ttl_seconds, json.dumps(value))
        except Exception:
            logger.warning("Redis SET failed for key %s", key)

    async def delete(self, key: str) -> None:
        if not self._client:
            return
        try:
            await self._client.delete(key)
        except Exception:
            logger.warning("Redis DELETE failed for key %s", key)
