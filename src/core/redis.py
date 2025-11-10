from typing import AsyncGenerator
import redis.asyncio as aioredis
from redis.asyncio import Redis

from src.core.logger import get_logger
from src.core.config import settings

logger = get_logger(__name__)

redis_client: Redis | None = None


def init_redis():
    """
    Initialize the Redis connection pool.
    """
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.CELERY_BROKER_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency to get the Redis client.
    """
    if redis_client is None:
        raise RuntimeError("Redis client not initialized.")
    try:
        yield redis_client
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        raise
