from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from typing import List, Optional

from ...dependencies import get_db
from ...models.quality_metric import QualityMetric
from ...schemas.quality_metric import QualityMetricCreate, QualityMetricUpdate, QualityMetricInDB

router = APIRouter()

@router.post("/", response_model=QualityMetricInDB, status_code=status.HTTP_201_CREATED)
async def create_quality_metric(
    quality_metric: QualityMetricCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new quality metric.
    """
    db_metric = QualityMetric(**quality_metric.dict())
    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)
    return db_metric

@router.get("/", response_model=List[QualityMetricInDB])
async def list_quality_metrics(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all quality metrics with pagination.
    """
    result = await db.execute(
        select(QualityMetric).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{metric_id}", response_model=QualityMetricInDB)
async def get_quality_metric(
    metric_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific quality metric by ID.
    """
    result = await db.execute(
        select(QualityMetric).where(QualityMetric.id == metric_id)
    )
    metric = result.scalars().first()
    if metric is None:
        raise HTTPException(status_code=404, detail="Quality metric not found")
    return metric
