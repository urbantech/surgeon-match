"""
Cache middleware for the SurgeonMatch API.

This middleware provides automatic caching for API responses based on request path and parameters.
"""
import json
import time
from typing import Callable, Dict, List, Optional, Set, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from surgeonmatch.core.cache import RedisCache, get_cache_key_from_request


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware that caches API responses in Redis."""

    def __init__(
        self, 
        app: ASGIApp, 
        redis_cache: RedisCache,
        cacheable_paths: Set[str] = None,
        exclude_paths: Set[str] = None,
        ttl: int = 3600
    ):
        """Initialize the cache middleware.
        
        Args:
            app: The ASGI app
            redis_cache: The Redis cache instance
            cacheable_paths: Optional set of path prefixes to cache
            exclude_paths: Optional set of path prefixes to exclude from caching
            ttl: Default cache TTL in seconds
        """
        super().__init__(app)
        self.redis_cache = redis_cache
        self.cacheable_paths = cacheable_paths or {"/api/v1/surgeons", "/api/v1/claims", "/api/v1/quality-metrics"}
        self.exclude_paths = exclude_paths or {"/api/v1/api-keys", "/health", "/metrics"}
        self.ttl = ttl
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process an incoming request.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware/route handler
            
        Returns:
            The response
        """
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
            
        # Check if path should be cached
        path = request.url.path
        if not any(path.startswith(prefix) for prefix in self.cacheable_paths):
            return await call_next(request)
            
        # Check if path should be excluded
        if any(path.startswith(prefix) for prefix in self.exclude_paths):
            return await call_next(request)
        
        # Generate cache key
        cache_key = get_cache_key_from_request(request, f"api:{path}")
        
        # Try to get response from cache
        cached_response = await self.redis_cache.get(cache_key)
        if cached_response:
            # Parse the cached response
            cached_data = json.loads(cached_response)
            headers = cached_data.get("headers", {})
            
            # Add cache hit header
            headers["X-Cache"] = "HIT"
            
            # Create response from cached data
            return Response(
                content=cached_data.get("content", ""),
                status_code=cached_data.get("status_code", 200),
                headers=headers,
                media_type=cached_data.get("media_type", "application/json")
            )
        
        # Cache miss, process the request
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # Only cache successful responses
        if 200 <= response.status_code < 400:
            # Get response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Prepare headers for caching (convert to dict)
            headers_dict = dict(response.headers.items())
            
            # Add cache miss header and response time
            headers_dict["X-Cache"] = "MISS"
            headers_dict["X-Response-Time"] = f"{response_time:.6f}s"
            
            # Prepare data for caching
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": headers_dict,
                "media_type": response.media_type
            }
            
            # Cache the response
            await self.redis_cache.set(
                cache_key, 
                json.dumps(cache_data),
                self.ttl
            )
            
            # Create a new response with the captured body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=headers_dict,
                media_type=response.media_type
            )
        
        # Return the original response for non-cacheable responses
        return response
