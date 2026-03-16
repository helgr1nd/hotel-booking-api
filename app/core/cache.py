import json
from typing import Any
import redis.asyncio as redis
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_cache(key: str) -> Any | None:
    value = await redis_client.get(key)
    if value:
        return json.loads(value)
    return None


async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    await redis_client.setex(key, ttl, json.dumps(value, default=str))


async def delete_cache(key: str) -> None:
    await redis_client.delete(key)


async def delete_cache_pattern(pattern: str) -> None:
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await redis_client.delete(*keys)
