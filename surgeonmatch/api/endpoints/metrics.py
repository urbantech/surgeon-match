"""
Metrics endpoints for monitoring API performance.

This module provides endpoints for monitoring the API's performance metrics,
including response times, cache hit rates, and database query performance.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from surgeonmatch.core.database import get_db, get_redis
from surgeonmatch.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'surgeonmatch_request_total', 
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'surgeonmatch_request_latency_seconds', 
    'Request latency in seconds',
    ['method', 'endpoint']
)

CACHE_HIT_COUNT = Counter(
    'surgeonmatch_cache_hit_total', 
    'Total number of cache hits',
    ['endpoint']
)

CACHE_MISS_COUNT = Counter(
    'surgeonmatch_cache_miss_total', 
    'Total number of cache misses',
    ['endpoint']
)

DB_QUERY_LATENCY = Histogram(
    'surgeonmatch_db_query_latency_seconds', 
    'Database query latency in seconds',
    ['query_type']
)

ACTIVE_DB_CONNECTIONS = Gauge(
    'surgeonmatch_active_db_connections', 
    'Number of active database connections'
)

RATE_LIMIT_EXCEEDED = Counter(
    'surgeonmatch_rate_limit_exceeded_total', 
    'Total number of rate limit exceeded events',
    ['api_key']
)


@router.get(
    "",
    summary="Get API metrics",
    description="Get performance metrics for the API in Prometheus format.",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def get_metrics():
    """Get performance metrics for the API in Prometheus format."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get(
    "/stats",
    summary="Get API statistics",
    description="Get detailed statistics for the API in JSON format.",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    start_time: Optional[datetime] = Query(
        None, description="Start time for statistics (ISO format)"
    ),
    end_time: Optional[datetime] = Query(
        None, description="End time for statistics (ISO format)"
    ),
    interval: str = Query(
        "hour", description="Interval for grouping (minute, hour, day)"
    ),
) -> Dict[str, Any]:
    """Get detailed statistics for the API in JSON format."""
    # Set default time range if not provided
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=1)
    
    # Format for interval grouping
    interval_format = {
        "minute": "YYYY-MM-DD HH24:MI",
        "hour": "YYYY-MM-DD HH24",
        "day": "YYYY-MM-DD",
    }.get(interval, "YYYY-MM-DD HH24")
    
    # Query response time statistics grouped by interval and endpoint
    response_time_query = """
    SELECT 
        TO_CHAR(timestamp, :interval_format) AS time_interval,
        endpoint,
        COUNT(*) AS request_count,
        AVG(response_time) AS avg_response_time,
        MAX(response_time) AS max_response_time,
        MIN(response_time) AS min_response_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time) AS p95_response_time,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time) AS p99_response_time
    FROM api_requests
    WHERE 
        timestamp BETWEEN :start_time AND :end_time
    GROUP BY 
        time_interval, endpoint
    ORDER BY 
        time_interval, endpoint
    """
    
    # Query cache hit statistics grouped by interval and endpoint
    cache_query = """
    SELECT 
        TO_CHAR(timestamp, :interval_format) AS time_interval,
        endpoint,
        SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) AS cache_hits,
        SUM(CASE WHEN NOT cache_hit THEN 1 ELSE 0 END) AS cache_misses,
        COUNT(*) AS total_requests,
        ROUND(SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::NUMERIC / COUNT(*), 2) AS hit_rate
    FROM api_requests
    WHERE 
        timestamp BETWEEN :start_time AND :end_time
    GROUP BY 
        time_interval, endpoint
    ORDER BY 
        time_interval, endpoint
    """
    
    # Query error statistics grouped by interval and status code
    error_query = """
    SELECT 
        TO_CHAR(timestamp, :interval_format) AS time_interval,
        status_code,
        COUNT(*) AS error_count
    FROM api_requests
    WHERE 
        timestamp BETWEEN :start_time AND :end_time
        AND status_code >= 400
    GROUP BY 
        time_interval, status_code
    ORDER BY 
        time_interval, status_code
    """
    
    # Execute queries
    params = {
        "interval_format": interval_format,
        "start_time": start_time,
        "end_time": end_time,
    }
    
    response_time_results = await db.execute(text(response_time_query), params)
    cache_results = await db.execute(text(cache_query), params)
    error_results = await db.execute(text(error_query), params)
    
    # Process results
    response_time_stats = [dict(row._mapping) for row in response_time_results]
    cache_stats = [dict(row._mapping) for row in cache_results]
    error_stats = [dict(row._mapping) for row in error_results]
    
    # Get current database statistics
    db_stats_query = """
    SELECT 
        count(*) AS active_connections,
        max(extract(epoch from (now() - query_start))) AS longest_running_query_seconds,
        count(CASE WHEN state = 'active' THEN 1 END) AS active_queries,
        count(CASE WHEN state = 'idle' THEN 1 END) AS idle_connections
    FROM 
        pg_stat_activity
    WHERE 
        datname = current_database()
    """
    db_stats_result = await db.execute(text(db_stats_query))
    db_stats = dict(db_stats_result.fetchone()._mapping)
    
    # Get Redis statistics
    redis = await get_redis()
    redis_info = await redis.info()
    
    redis_stats = {
        "connected_clients": redis_info.get("connected_clients", 0),
        "used_memory_human": redis_info.get("used_memory_human", "0"),
        "total_commands_processed": redis_info.get("total_commands_processed", 0),
        "keyspace_hits": redis_info.get("keyspace_hits", 0),
        "keyspace_misses": redis_info.get("keyspace_misses", 0),
        "hit_rate": 0,
    }
    
    # Calculate Redis hit rate
    hits = redis_info.get("keyspace_hits", 0)
    misses = redis_info.get("keyspace_misses", 0)
    total = hits + misses
    redis_stats["hit_rate"] = round(hits / total, 2) if total > 0 else 0
    
    # Compile final statistics
    return {
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "interval": interval,
        },
        "response_time_stats": response_time_stats,
        "cache_stats": cache_stats,
        "error_stats": error_stats,
        "database_stats": db_stats,
        "redis_stats": redis_stats,
        "api_version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health-check",
    summary="Detailed health check",
    description="Get detailed health status of the API and its dependencies.",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed health status of the API and its dependencies."""
    start_time = time.time()
    health_status = {"status": "ok", "services": {}}
    
    # Check database connection
    try:
        # Simple query to check database connection
        await db.execute(select(func.now()))
        db_latency = time.time() - start_time
        health_status["services"]["database"] = {
            "status": "ok",
            "latency_ms": round(db_latency * 1000, 2),
        }
    except Exception as e:
        health_status["status"] = "error"
        health_status["services"]["database"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Check Redis connection
    redis_start_time = time.time()
    try:
        redis = await get_redis()
        await redis.ping()
        redis_latency = time.time() - redis_start_time
        health_status["services"]["redis"] = {
            "status": "ok",
            "latency_ms": round(redis_latency * 1000, 2),
        }
    except Exception as e:
        health_status["status"] = "error"
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Add overall latency
    health_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
    health_status["timestamp"] = datetime.utcnow().isoformat()
    health_status["version"] = settings.APP_VERSION
    
    return health_status
