"""
Query optimization utilities for the SurgeonMatch API.

This module provides functions for optimizing database queries to achieve
the performance requirements specified in the project standards.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from surgeonmatch.models.claim import Claim
from surgeonmatch.models.quality_metric import QualityMetric
from surgeonmatch.models.surgeon import Surgeon

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def optimize_surgeon_query(
    db: AsyncSession,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
    include_metrics: bool = False,
    include_claims: bool = False,
) -> Tuple[List[Surgeon], int]:
    """Optimized query for retrieving surgeons with optional filters.
    
    Args:
        db: Database session
        filters: Optional filters to apply
        skip: Number of results to skip
        limit: Maximum number of results to return
        include_metrics: Whether to include quality metrics
        include_claims: Whether to include claims
        
    Returns:
        Tuple of (list of surgeons, total count)
    """
    # Start with base query
    query = select(Surgeon)
    
    # Add joins if needed for eager loading
    if include_metrics:
        query = query.options(selectinload(Surgeon.quality_metrics))
    
    if include_claims:
        query = query.options(selectinload(Surgeon.claims))
    
    # Apply filters
    if filters:
        if filters.get("specialty"):
            query = query.filter(Surgeon.specialty == filters["specialty"])
        
        if all(key in filters for key in ["lat", "lng", "radius"]):
            # Optimize geospatial query using Haversine formula
            lat, lng, radius = filters["lat"], filters["lng"], filters["radius"]
            # Approximate conversion of miles to degrees (for small distances)
            radius_degrees = radius / 69.0
            
            # First-pass filter using bounding box (fast)
            query = query.filter(
                Surgeon.latitude.between(lat - radius_degrees, lat + radius_degrees),
                Surgeon.longitude.between(lng - radius_degrees, lng + radius_degrees)
            )
            
            # Note: For a full implementation, we would apply the Haversine formula
            # as a second-pass filter for precise distance calculation
        
        if filters.get("npi"):
            query = query.filter(Surgeon.npi == filters["npi"])
        
        if filters.get("state"):
            query = query.filter(Surgeon.state == filters["state"])
        
        if filters.get("city"):
            query = query.filter(Surgeon.city == filters["city"])
    
    # Count total results (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    surgeons = result.scalars().all()
    
    return surgeons, total or 0


async def optimize_claim_query(
    db: AsyncSession,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
    include_surgeon: bool = False,
) -> Tuple[List[Claim], int]:
    """Optimized query for retrieving claims with optional filters.
    
    Args:
        db: Database session
        filters: Optional filters to apply
        skip: Number of results to skip
        limit: Maximum number of results to return
        include_surgeon: Whether to include surgeon data
        
    Returns:
        Tuple of (list of claims, total count)
    """
    # Start with base query
    query = select(Claim)
    
    # Add joins if needed for eager loading
    if include_surgeon:
        query = query.options(joinedload(Claim.surgeon))
    
    # Apply filters
    if filters:
        if filters.get("surgeon_id"):
            query = query.filter(Claim.surgeon_id == filters["surgeon_id"])
        
        if filters.get("procedure_code"):
            query = query.filter(Claim.procedure_code == filters["procedure_code"])
        
        if filters.get("claim_id"):
            query = query.filter(Claim.claim_id == filters["claim_id"])
        
        if filters.get("date_from") and filters.get("date_to"):
            query = query.filter(
                Claim.date.between(filters["date_from"], filters["date_to"])
            )
    
    # Count total results (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    claims = result.scalars().all()
    
    return claims, total or 0


async def optimize_quality_metric_query(
    db: AsyncSession,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
    include_surgeon: bool = False,
) -> Tuple[List[QualityMetric], int]:
    """Optimized query for retrieving quality metrics with optional filters.
    
    Args:
        db: Database session
        filters: Optional filters to apply
        skip: Number of results to skip
        limit: Maximum number of results to return
        include_surgeon: Whether to include surgeon data
        
    Returns:
        Tuple of (list of quality metrics, total count)
    """
    # Start with base query
    query = select(QualityMetric)
    
    # Add joins if needed for eager loading
    if include_surgeon:
        query = query.options(joinedload(QualityMetric.surgeon))
    
    # Apply filters
    if filters:
        if filters.get("surgeon_id"):
            query = query.filter(QualityMetric.surgeon_id == filters["surgeon_id"])
        
        if filters.get("metric_name"):
            query = query.filter(QualityMetric.metric_name == filters["metric_name"])
        
        if filters.get("min_value") is not None:
            query = query.filter(QualityMetric.metric_value >= filters["min_value"])
        
        if filters.get("max_value") is not None:
            query = query.filter(QualityMetric.metric_value <= filters["max_value"])
        
        if filters.get("date_from") and filters.get("date_to"):
            query = query.filter(
                QualityMetric.date.between(filters["date_from"], filters["date_to"])
            )
    
    # Count total results (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return metrics, total or 0


async def run_analyzed_query(
    db: AsyncSession, query: str, explain: bool = False
) -> List[Dict[str, Any]]:
    """Run a raw SQL query with optional EXPLAIN ANALYZE.
    
    This is useful for complex analytics queries that aren't easily
    expressed in the ORM.
    
    Args:
        db: Database session
        query: SQL query to run
        explain: Whether to run with EXPLAIN ANALYZE
        
    Returns:
        List of result rows as dictionaries
    """
    if explain:
        query = f"EXPLAIN ANALYZE {query}"
    
    result = await db.execute(text(query))
    
    if explain:
        # For EXPLAIN queries, return the execution plan
        return [{"plan_line": row[0]} for row in result.all()]
    
    # For regular queries, convert to dictionaries
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.all()]
