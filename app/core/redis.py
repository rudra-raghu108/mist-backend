"""
Redis configuration for SRM Guide Bot
"""

import logging
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise


async def close_redis():
    """Close Redis connection"""
    global redis_client
    
    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")


async def get_redis_client():
    """Get Redis client instance"""
    if redis_client is None:
        await init_redis()
    return redis_client


async def set_cache(key: str, value: str, expire: int = None):
    """Set cache value"""
    try:
        client = await get_redis_client()
        await client.set(key, value, ex=expire or settings.CACHE_TTL)
    except Exception as e:
        logger.error(f"Error setting cache: {str(e)}")


async def get_cache(key: str) -> str:
    """Get cache value"""
    try:
        client = await get_redis_client()
        return await client.get(key)
    except Exception as e:
        logger.error(f"Error getting cache: {str(e)}")
        return None


async def delete_cache(key: str):
    """Delete cache value"""
    try:
        client = await get_redis_client()
        await client.delete(key)
    except Exception as e:
        logger.error(f"Error deleting cache: {str(e)}")


async def clear_cache():
    """Clear all cache"""
    try:
        client = await get_redis_client()
        await client.flushdb()
        logger.info("Cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
