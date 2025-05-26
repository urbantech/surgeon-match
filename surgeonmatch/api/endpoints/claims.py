from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from typing import List, Optional

from ...dependencies import get_db
from ...models.claim import Claim
from ...schemas.claim import ClaimCreate, ClaimUpdate, ClaimInDB

router = APIRouter()

@router.post("/", response_model=ClaimInDB, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim: ClaimCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new claim.
    """
    db_claim = Claim(**claim.dict())
    db.add(db_claim)
    await db.commit()
    await db.refresh(db_claim)
    return db_claim

@router.get("/", response_model=List[ClaimInDB])
async def list_claims(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all claims with pagination.
    """
    result = await db.execute(
        select(Claim).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{claim_id}", response_model=ClaimInDB)
async def get_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific claim by ID.
    """
    result = await db.execute(
        select(Claim).where(Claim.id == claim_id)
    )
    claim = result.scalars().first()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim
