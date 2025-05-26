#!/usr/bin/env python
"""
Test script for validating SurgeonMatch API endpoints directly without running the server.
This approach allows us to test the API logic and database integration separately from the web server.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from surgeonmatch.core.config import settings
from surgeonmatch.models.base import Base
from surgeonmatch.models.api_key import APIKey
from surgeonmatch.models.surgeon import Surgeon
from surgeonmatch.models.claim import Claim
from surgeonmatch.models.quality_metric import QualityMetric
from surgeonmatch.models.rate_limit import RateLimit

# Import core functionality
from surgeonmatch.core.security import verify_api_key

# Set up database connection
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_db():
    """Get a database session."""
    async with async_session() as session:
        yield session
        await session.close()

async def test_verify_api_key():
    """Test the API key verification logic."""
    print("\n=== Testing API Key Verification ===")
    api_key = "7716103218ca43bed0aabe70c382eea2cecd676e990190bf66c701712b1a6136"
    
    db_gen = get_db()
    session = await anext(db_gen)
    
    try:
        # Test API key verification
        is_valid, api_key_record, error = await verify_api_key(api_key, session)
        if is_valid and api_key_record:
            print(f"✅ API Key verification successful: {api_key_record.name}")
            print(f"   - ID: {api_key_record.id}")
            print(f"   - Created at: {api_key_record.created_at}")
            print(f"   - Expires at: {api_key_record.expires_at}")
            print(f"   - Last used: {api_key_record.last_used_at}")
        else:
            print(f"❌ API Key verification failed: {error}")
    finally:
        await session.close()

async def test_list_surgeons():
    """Test listing surgeons endpoint logic."""
    print("\n=== Testing List Surgeons Endpoint ===")
    db_gen = get_db()
    session = await anext(db_gen)
    
    try:
        # Query all surgeons
        result = await session.execute(select(Surgeon))
        surgeons = result.scalars().all()
        
        # Print results
        if surgeons:
            print(f"✅ Found {len(surgeons)} surgeons:")
            for i, surgeon in enumerate(surgeons, 1):
                print(f"{i}. {surgeon.first_name} {surgeon.last_name} - {surgeon.specialty}")
        else:
            print("⚠️ No surgeons found in the database")
            
            # Create a test surgeon if none exists
            print("Creating a test surgeon...")
            new_surgeon = Surgeon(
                first_name="John",
                last_name="Doe",
                specialty="Cardiology",
                npi="1234567890",
                hospital_affiliation="General Hospital",
                years_of_experience=10,
                state_license="CA12345",
                board_certified=True
            )
            session.add(new_surgeon)
            await session.commit()
            await session.refresh(new_surgeon)
            print(f"✅ Created test surgeon: {new_surgeon.first_name} {new_surgeon.last_name}")
            
    finally:
        await session.close()

async def test_list_claims():
    """Test listing claims endpoint logic."""
    print("\n=== Testing List Claims Endpoint ===")
    db_gen = get_db()
    session = await anext(db_gen)
    
    try:
        # Query all claims
        result = await session.execute(select(Claim))
        claims = result.scalars().all()
        
        # Print results
        if claims:
            print(f"✅ Found {len(claims)} claims:")
            for i, claim in enumerate(claims, 1):
                print(f"{i}. Claim ID: {claim.id}, Procedure: {claim.procedure_code}")
        else:
            print("⚠️ No claims found in the database")
            
            # Create a test claim if none exists
            # First, get a surgeon
            surgeon_result = await session.execute(select(Surgeon).limit(1))
            surgeon = surgeon_result.scalars().first()
            
            if surgeon:
                print(f"Creating a test claim for surgeon: {surgeon.first_name} {surgeon.last_name}")
                new_claim = Claim(
                    surgeon_id=surgeon.id,
                    procedure_date=datetime.utcnow(),
                    procedure_code="12345",
                    diagnosis_code="E11.65",
                    billed_amount=1500.00,
                    allowed_amount=1200.00,
                    paid_amount=1000.00,
                    patient_deductible=200.00,
                    patient_coinsurance=0.00,
                    patient_copay=0.00,
                    insurance_type="Medicare",
                    claim_status="paid"
                )
                session.add(new_claim)
                await session.commit()
                await session.refresh(new_claim)
                print(f"✅ Created test claim: {new_claim.id}")
            else:
                print("❌ Cannot create test claim - no surgeons found")
    finally:
        await session.close()

async def test_quality_metrics():
    """Test quality metrics endpoint logic."""
    print("\n=== Testing Quality Metrics Endpoint ===")
    db_gen = get_db()
    session = await anext(db_gen)
    
    try:
        # Query all quality metrics
        result = await session.execute(select(QualityMetric))
        metrics = result.scalars().all()
        
        # Print results
        if metrics:
            print(f"✅ Found {len(metrics)} quality metrics:")
            for i, metric in enumerate(metrics, 1):
                print(f"{i}. Metric ID: {metric.id}, Score: {metric.overall_score}")
        else:
            print("⚠️ No quality metrics found in the database")
    finally:
        await session.close()

async def main():
    """Run all endpoint tests."""
    print(f"Testing SurgeonMatch API endpoints using DATABASE_URL: {settings.DATABASE_URL}")
    
    await test_verify_api_key()
    await test_list_surgeons()
    await test_list_claims()
    await test_quality_metrics()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
