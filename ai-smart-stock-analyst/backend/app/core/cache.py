"""
Redis wrapper used for:
  - response caching (quotes, fundamentals, news — short TTLs)
  - rate limiting counters
  - queueing background/refresh jobs
Spec section 39: "ใช้ Redis สำหรับ Caching / Real-time Data / Rate Limiting / Queue"
"""
import json
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()
_pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)


class Cache:
    """Thin helper around redis get/set with JSON (de)serialization."""

    # Suggested TTLs by data class (seconds)
    TTL_QUOTE = 30            # intraday price — short-lived
    TTL_FUNDAMENTAL = 60 * 60 * 12   # fundamentals change daily at most
    TTL_NEWS = 60 * 5
    TTL_AI_SCORE = 60 * 60 * 6
    TTL_TOP10 = 60 * 60 * 24 * 7     # refreshed weekly by the cron job

    def __init__(self, client: redis.Redis | None = None):
        self.client = client or get_redis()

    async def get_json(self, key: str) -> Any | None:
        raw = await self.client.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        await self.client.set(key, json.dumps(value, default=str), ex=ttl)

    async def invalidate(self, key: str) -> None:
        await self.client.delete(key)

    async def rate_limit_hit(self, identifier: str, limit: int, window_seconds: int = 60) -> bool:
        """Returns True if the caller is OVER the limit (should be rejected)."""
        key = f"ratelimit:{identifier}"
        current = await self.client.incr(key)
        if current == 1:
            await self.client.expire(key, window_seconds)
        return current > limit
