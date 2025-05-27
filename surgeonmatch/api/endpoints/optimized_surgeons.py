"""
Optimized Surgeons API endpoints.

This module provides endpoints for retrieving surgeon data with optimized
database queries and automatic caching for high performance.
"""
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from surgeonmatch.core.database import get_db
from surgeonmatch.core.cache import RedisCache, get_cache, get_cache_key_from_request, cached_response
from surgeonmatch.core.query_optimizer import optimize_surgeon_query
from surgeonmatch.models.surgeon import Surgeon
from surgeonmatch.schemas.surgeon import SurgeonRead, SurgeonList, SurgeonDetail
from surgeonmatch.schemas.error import ErrorCodes

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=SurgeonList,
    summary="List all surgeons",
    description="Get a list of all surgeons with pagination and filtering options."
)
async def list_surgeons(
    request: Request,
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    lat: Optional[float] = Query(None, description="Latitude for location-based search"),
    lng: Optional[float] = Query(None, description="Longitude for location-based search"),
    radius: Optional[float] = Query(None, description="Radius in miles for location search"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> SurgeonList:
    """List surgeons with optimized performance using caching and efficient queries."""
    # Prepare filters
    filters = {}
    if specialty:
        filters["specialty"] = specialty
    if state:
        filters["state"] = state
    if city:
        filters["city"] = city
    if all([lat, lng, radius]):
        filters["lat"] = lat
        filters["lng"] = lng
        filters["radius"] = radius

    # Generate cache key
    cache_key = get_cache_key_from_request(request, "surgeons:list")
    
    # Define async data retrieval function for cache miss
    async def get_data():
        surgeons, total = await optimize_surgeon_query(
            db, filters=filters, skip=skip, limit=limit
        )
        
        return {
            "data": [SurgeonRead.model_validate(s).model_dump() for s in surgeons],
            "meta": {
                "page": skip // limit + 1 if limit > 0 else 1,
                "per_page": limit,
                "total": total
            }
        }
    
    # Get data from cache or database with automatic caching
    result = await cached_response(cache, cache_key, get_data)
    
    return SurgeonList.model_validate(result)


@router.get(
    "/{surgeon_id}",
    response_model=SurgeonDetail,
    summary="Get surgeon by ID",
    description="Get detailed information about a surgeon by their ID."
)
async def get_surgeon(
    request: Request,
    surgeon_id: str = Path(..., description="Surgeon ID"),
    include_metrics: bool = Query(False, description="Include quality metrics"),
    include_claims: bool = Query(False, description="Include claims data"),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> SurgeonDetail:
    """Get a specific surgeon with optimized performance using caching and efficient queries."""
    # Generate cache key
    cache_key = get_cache_key_from_request(
        request, f"surgeons:detail:{surgeon_id}"
    )
    
    # Define async data retrieval function for cache miss
    async def get_data():
        # Use optimized query with eager loading based on includes
        surgeons, _ = await optimize_surgeon_query(
            db, 
            filters={"id": surgeon_id}, 
            limit=1,
            include_metrics=include_metrics,
            include_claims=include_claims
        )
        
        if not surgeons:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Surgeon with ID {surgeon_id} not found",
                code=ErrorCodes.SURGEON_NOT_FOUND[0]
            )
        
        surgeon = surgeons[0]
        return SurgeonDetail.model_validate(surgeon).model_dump()
    
    # Get data from cache or database with automatic caching
    try:
        result = await cached_response(cache, cache_key, get_data)
        return SurgeonDetail.model_validate(result)
    except HTTPException:
        # Don't cache errors, re-raise them
        raise


@router.get(
    "/npi/{npi}",
    response_model=SurgeonDetail,
    summary="Get surgeon by NPI",
    description="Get detailed information about a surgeon by their NPI number."
)
async def get_surgeon_by_npi(
    request: Request,
    npi: str = Path(..., description="Surgeon NPI number"),
    include_metrics: bool = Query(False, description="Include quality metrics"),
    include_claims: bool = Query(False, description="Include claims data"),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> SurgeonDetail:
    """Get a surgeon by NPI with optimized performance using caching and efficient queries."""
    # Generate cache key
    cache_key = get_cache_key_from_request(
        request, f"surgeons:npi:{npi}"
    )
    
    # Define async data retrieval function for cache miss
    async def get_data():
        # Use optimized query with eager loading based on includes
        surgeons, _ = await optimize_surgeon_query(
            db, 
            filters={"npi": npi}, 
            limit=1,
            include_metrics=include_metrics,
            include_claims=include_claims
        )
        
        if not surgeons:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Surgeon with NPI {npi} not found",
                code=ErrorCodes.SURGEON_NOT_FOUND[0]
            )
        
        surgeon = surgeons[0]
        return SurgeonDetail.model_validate(surgeon).model_dump()
    
    # Get data from cache or database with automatic caching
    try:
        result = await cached_response(cache, cache_key, get_data)
        return SurgeonDetail.model_validate(result)
    except HTTPException:
        # Don't cache errors, re-raise them
        raise
