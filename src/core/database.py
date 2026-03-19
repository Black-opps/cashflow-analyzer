"""
Database connection management (if needed).
"""
import redis
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

# Redis connection (optional)
redis_client = None
if settings.REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5
        )
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")


def get_redis():
    """Get Redis client."""
    return redis_client