"""
Redis client for async operations.
Uses redis-py with async support (redis >= 5.0).
"""

from typing import Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.settings import settings


# Global instances
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """
    Initialize Redis connection pool and client.
    Called during application startup.
    """
    global _redis_pool, _redis_client

    _redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=10,
        decode_responses=True,
    )
    _redis_client = redis.Redis(connection_pool=_redis_pool)

    # Test connection
    await _redis_client.ping()

    return _redis_client


async def close_redis() -> None:
    """
    Close Redis connections.
    Called during application shutdown.
    """
    global _redis_client, _redis_pool

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


async def get_redis() -> redis.Redis:
    """
    FastAPI dependency to get Redis client.

    Usage:
        @router.get("/example")
        async def example(redis: redis.Redis = Depends(get_redis)):
            await redis.set("key", "value")
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _redis_client


def get_redis_sync() -> Optional[redis.Redis]:
    """
    Get Redis client synchronously (for use in Celery tasks).
    Returns None if not initialized.
    """
    return _redis_client
