"""
Cache invalidation utilities for the SurgeonMatch API.

This module provides functions to automatically invalidate cache entries when
data is modified, ensuring that API responses remain up-to-date.
"""
import logging
from typing import Dict, List, Optional, Set, Union

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from surgeonmatch.core.cache import RedisCache
from surgeonmatch.db.base import get_db

logger = logging.getLogger(__name__)


class CacheInvalidator:
    """Cache invalidation manager for database operations."""

    def __init__(self, cache: RedisCache, db: AsyncSession):
        """Initialize the cache invalidator.
        
        Args:
            cache: Redis cache instance
            db: Database session
        """
        self.cache = cache
        self.db = db
        self.entity_prefixes = {
            "surgeon": "api:/api/v1/surgeons",
            "claim": "api:/api/v1/claims",
            "quality_metric": "api:/api/v1/quality-metrics",
        }

    async def invalidate_entity(self, entity_type: str, entity_id: Optional[str] = None) -> None:
        """Invalidate cache for a specific entity type and optional ID.
        
        Args:
            entity_type: Type of entity (surgeon, claim, quality_metric)
            entity_id: Optional entity ID to invalidate specific entity
        """
        prefix = self.entity_prefixes.get(entity_type)
        if not prefix:
            logger.warning(f"Unknown entity type for cache invalidation: {entity_type}")
            return

        if entity_id:
            # Invalidate specific entity
            specific_prefix = f"{prefix}/{entity_id}"
            await self.cache.clear_prefix(specific_prefix)
            logger.info(f"Invalidated cache for {entity_type} with ID {entity_id}")
        
        # Always invalidate list endpoints when any entity changes
        await self.cache.clear_prefix(prefix)
        logger.info(f"Invalidated cache for {entity_type} list")

    async def invalidate_surgeon(self, surgeon_id: str) -> None:
        """Invalidate cache for a specific surgeon.
        
        Args:
            surgeon_id: ID of the surgeon to invalidate
        """
        await self.invalidate_entity("surgeon", surgeon_id)
        
        # Also invalidate related entities
        await self.invalidate_entity("claim")  # Claims may be filtered by surgeon
        await self.invalidate_entity("quality_metric")  # Metrics are linked to surgeons

    async def invalidate_claim(self, claim_id: str) -> None:
        """Invalidate cache for a specific claim.
        
        Args:
            claim_id: ID of the claim to invalidate
        """
        await self.invalidate_entity("claim", claim_id)

    async def invalidate_quality_metric(self, metric_id: str) -> None:
        """Invalidate cache for a specific quality metric.
        
        Args:
            metric_id: ID of the quality metric to invalidate
        """
        await self.invalidate_entity("quality_metric", metric_id)

    async def invalidate_all(self) -> None:
        """Invalidate all API cache entries."""
        await self.cache.clear_prefix("api:")
        logger.info("Invalidated all API cache entries")


async def get_cache_invalidator(
    cache: RedisCache, db: AsyncSession = Depends(get_db)
) -> CacheInvalidator:
    """FastAPI dependency for getting a cache invalidator instance."""
    return CacheInvalidator(cache, db)
