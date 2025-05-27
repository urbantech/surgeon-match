"""
Redis caching module for the SurgeonMatch API.

This module provides utilities for caching API responses to improve performance.
Cache invalidation is handled automatically on data updates.
"""
import json
import logging
from typing import Any, Dict, List, Optional, TypeVar, Union, cast

from fastapi import Depends, Request
from redis.asyncio import Redis

from surgeonmatch.core.config import settings

T = TypeVar("T")
logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache implementation for API responses."""

    def __init__(self, redis: Redis):
        """Initialize the Redis cache.
        
        Args:
            redis: Redis connection
        """
        self.redis = redis
        self.default_ttl = 3600  # 1 hour default cache expiration

    async def get(self, key: str) -> Optional[str]:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value, or None if not found
        """
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.warning(f"Redis get error: {str(e)}")
            return None

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds, or None for default
        """
        try:
            await self.redis.set(
                key, value, ex=ttl if ttl is not None else self.default_ttl
            )
        except Exception as e:
            logger.warning(f"Redis set error: {str(e)}")

    async def delete(self, key: str) -> None:
        """Delete a value from the cache.
        
        Args:
            key: Cache key to delete
        """
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error: {str(e)}")

    async def clear_prefix(self, prefix: str) -> None:
        """Clear all keys with a given prefix.
        
        Args:
            prefix: Prefix to match for clearing keys
        """
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=f"{prefix}*", count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Redis clear_prefix error: {str(e)}")

    @classmethod
    def generate_key(
        cls, prefix: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a cache key from a prefix and optional parameters.
        
        Args:
            prefix: The prefix for the key
            params: Optional parameters to include in the key
            
        Returns:
            The generated cache key
        """
        if not params:
            return prefix
        # Sort params to ensure consistent keys
        param_str = "_".join(
            f"{k}:{v}" for k, v in sorted(params.items()) if v is not None
        )
        return f"{prefix}_{param_str}"


async def get_cache(redis: Redis = Depends()):
    """FastAPI dependency for getting the Redis cache."""
    return RedisCache(redis)


async def cached_response(
    cache: RedisCache,
    cache_key: str,
    data_callback,
    ttl: Optional[int] = None,
):
    """Get a cached response or generate and cache it.
    
    Args:
        cache: The Redis cache instance
        cache_key: The cache key
        data_callback: Async function to call if cache miss
        ttl: Optional TTL for cache
        
    Returns:
        The cached or freshly generated data
    """
    # Try to get from cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Cache miss, generate data
    data = await data_callback()
    
    # Cache the result
    await cache.set(cache_key, json.dumps(data), ttl)
    return data


def get_cache_key_from_request(request: Request, prefix: str) -> str:
    """Generate a cache key from a FastAPI request.
    
    Args:
        request: The FastAPI request
        prefix: Prefix for the cache key
        
    Returns:
        Generated cache key
    """
    # Include query params in the cache key
    params = dict(request.query_params)
    # Include path params in the cache key
    params.update(request.path_params)
    # Include API key in cache key for potential personalization
    api_key = request.headers.get(settings.API_KEY_HEADER)
    if api_key:
        params["api_key"] = api_key
    
    return RedisCache.generate_key(prefix, params)
