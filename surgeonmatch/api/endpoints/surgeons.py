from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ...dependencies import get_db
from ...models.surgeon import Surgeon
from ...schemas.surgeon import SurgeonCreate, SurgeonUpdate, SurgeonInDB

router = APIRouter()

@router.post("/surgeons/", response_model=SurgeonInDB, status_code=status.HTTP_201_CREATED)
async def create_surgeon(
    surgeon: SurgeonCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new surgeon.
    """
    db_surgeon = Surgeon(**surgeon.dict())
    db.add(db_surgeon)
    await db.commit()
    await db.refresh(db_surgeon)
    return db_surgeon

@router.get("/surgeons/", response_model=List[SurgeonInDB])
async def list_surgeons(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all surgeons with pagination.
    """
    result = await db.execute(
        select(Surgeon).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/surgeons/{surgeon_id}", response_model=SurgeonInDB)
async def get_surgeon(
    surgeon_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific surgeon by ID.
    """
    result = await db.execute(
        select(Surgeon).where(Surgeon.id == surgeon_id)
    )
    surgeon = result.scalars().first()
    if surgeon is None:
        raise HTTPException(status_code=404, detail="Surgeon not found")
    return surgeon
