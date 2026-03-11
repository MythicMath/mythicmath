import os
from typing import Optional

from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
