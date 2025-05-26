#!/usr/bin/env python
"""
Validate SurgeonMatch API functionality using direct database access.
This follows the SurgeonMatch Project Standards for testing and validation.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import uuid
import hashlib

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

# Database connection string
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/surgeonmatch"
)

async def run_query(query, params=None):
    """Run a raw SQL query and return the results."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        result = await conn.execute(text(query), params or {})
        if query.strip().upper().startswith("SELECT"):
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        await conn.commit()
        return None

async def test_api_key():
    """Validate the API key in the database."""
    print("\n=== Testing API Key ===")
    api_key = "7716103218ca43bed0aabe70c382eea2cecd676e990190bf66c701712b1a6136"
    
    # Check if the API key exists in the database
    query = """
    SELECT * FROM api_keys WHERE key = :key
    """
    results = await run_query(query, {"key": api_key})
    
    if results:
        print(f"✅ API Key found: {results[0]['name']}")
        print(f"   - Created at: {results[0]['created_at']}")
        print(f"   - Expires at: {results[0]['expires_at']}")
        print(f"   - Is active: {results[0]['is_active']}")
    else:
        print("❌ API Key not found in database")

async def test_surgeons():
    """Validate the surgeons functionality."""
    print("\n=== Testing Surgeons Endpoint ===")
    
    # List all surgeons
    query = "SELECT * FROM surgeons"
    results = await run_query(query)
    
    if results:
        print(f"✅ Found {len(results)} surgeons in database:")
        for i, surgeon in enumerate(results, 1):
            print(f"{i}. {surgeon['first_name']} {surgeon['last_name']} - {surgeon['specialty']}")
    else:
        print("ℹ️ No surgeons found in database")
        
        # Create a test surgeon
        print("Creating a test surgeon...")
        insert_query = """
        INSERT INTO surgeons (
            id, first_name, last_name, specialty, npi, hospital_affiliation,
            years_of_experience, state_license, board_certified, created_at, updated_at
        ) VALUES (
            :id, :first_name, :last_name, :specialty, :npi, :hospital_affiliation,
            :years_of_experience, :state_license, :board_certified, NOW(), NOW()
        )
        """
        surgeon_id = str(uuid.uuid4())
        params = {
            "id": surgeon_id,
            "first_name": "John",
            "last_name": "Doe",
            "specialty": "Cardiology",
            "npi": "1234567890",
            "hospital_affiliation": "General Hospital",
            "years_of_experience": 10,
            "state_license": "CA12345",
            "board_certified": True
        }
        await run_query(insert_query, params)
        print(f"✅ Created test surgeon with ID: {surgeon_id}")
        
        # Verify surgeon was created
        verify_query = "SELECT * FROM surgeons WHERE id = :id"
        verify_results = await run_query(verify_query, {"id": surgeon_id})
        if verify_results:
            print(f"✅ Verified surgeon creation: {verify_results[0]['first_name']} {verify_results[0]['last_name']}")

async def test_claims():
    """Validate the claims functionality."""
    print("\n=== Testing Claims Endpoint ===")
    
    # List all claims
    query = "SELECT * FROM claims"
    results = await run_query(query)
    
    if results:
        print(f"✅ Found {len(results)} claims in database:")
        for i, claim in enumerate(results, 1):
            print(f"{i}. Claim ID: {claim['id']}, Procedure: {claim['procedure_code']}")
    else:
        print("ℹ️ No claims found in database")
        
        # Get a surgeon to associate with a claim
        surgeon_query = "SELECT * FROM surgeons LIMIT 1"
        surgeons = await run_query(surgeon_query)
        
        if surgeons:
            surgeon_id = surgeons[0]['id']
            print(f"Creating a test claim for surgeon ID: {surgeon_id}")
            
            # Create a test claim
            insert_query = """
            INSERT INTO claims (
                id, surgeon_id, procedure_date, procedure_code, diagnosis_code,
                billed_amount, allowed_amount, paid_amount, patient_deductible,
                patient_coinsurance, patient_copay, insurance_type, claim_status,
                created_at, updated_at
            ) VALUES (
                :id, :surgeon_id, :procedure_date, :procedure_code, :diagnosis_code,
                :billed_amount, :allowed_amount, :paid_amount, :patient_deductible,
                :patient_coinsurance, :patient_copay, :insurance_type, :claim_status,
                NOW(), NOW()
            )
            """
            claim_id = str(uuid.uuid4())
            params = {
                "id": claim_id,
                "surgeon_id": surgeon_id,
                "procedure_date": datetime.utcnow(),
                "procedure_code": "12345",
                "diagnosis_code": "E11.65",
                "billed_amount": 1500.00,
                "allowed_amount": 1200.00,
                "paid_amount": 1000.00,
                "patient_deductible": 200.00,
                "patient_coinsurance": 0.00,
                "patient_copay": 0.00,
                "insurance_type": "Medicare",
                "claim_status": "paid"
            }
            await run_query(insert_query, params)
            print(f"✅ Created test claim with ID: {claim_id}")
            
            # Verify claim was created
            verify_query = "SELECT * FROM claims WHERE id = :id"
            verify_results = await run_query(verify_query, {"id": claim_id})
            if verify_results:
                print(f"✅ Verified claim creation: {verify_results[0]['id']}")
        else:
            print("❌ Cannot create test claim - no surgeons found")

async def test_quality_metrics():
    """Validate the quality metrics functionality."""
    print("\n=== Testing Quality Metrics Endpoint ===")
    
    # List all quality metrics
    query = "SELECT * FROM quality_metrics"
    results = await run_query(query)
    
    if results:
        print(f"✅ Found {len(results)} quality metrics in database:")
        for i, metric in enumerate(results, 1):
            print(f"{i}. Metric ID: {metric['id']}, Surgeon: {metric['surgeon_id']}")
    else:
        print("ℹ️ No quality metrics found in database")
        
        # Get a surgeon to associate with a quality metric
        surgeon_query = "SELECT * FROM surgeons LIMIT 1"
        surgeons = await run_query(surgeon_query)
        
        if surgeons:
            surgeon_id = surgeons[0]['id']
            print(f"Creating a test quality metric for surgeon ID: {surgeon_id}")
            
            # Create a test quality metric
            insert_query = """
            INSERT INTO quality_metrics (
                id, surgeon_id, overall_score, complication_rate, readmission_rate,
                patient_satisfaction, quality_data, review_period_start,
                review_period_end, created_at, updated_at
            ) VALUES (
                :id, :surgeon_id, :overall_score, :complication_rate, :readmission_rate,
                :patient_satisfaction, :quality_data, :review_period_start,
                :review_period_end, NOW(), NOW()
            )
            """
            metric_id = str(uuid.uuid4())
            params = {
                "id": metric_id,
                "surgeon_id": surgeon_id,
                "overall_score": 4.5,
                "complication_rate": 0.02,
                "readmission_rate": 0.03,
                "patient_satisfaction": 4.7,
                "quality_data": {},
                "review_period_start": datetime(2024, 1, 1),
                "review_period_end": datetime(2024, 12, 31)
            }
            await run_query(insert_query, params)
            print(f"✅ Created test quality metric with ID: {metric_id}")
            
            # Verify quality metric was created
            verify_query = "SELECT * FROM quality_metrics WHERE id = :id"
            verify_results = await run_query(verify_query, {"id": metric_id})
            if verify_results:
                print(f"✅ Verified quality metric creation: {verify_results[0]['id']}")
        else:
            print("❌ Cannot create test quality metric - no surgeons found")

async def main():
    """Run all validation tests for the SurgeonMatch API."""
    print(f"Validating SurgeonMatch API using database: {DATABASE_URL}")
    
    await test_api_key()
    await test_surgeons()
    await test_claims()
    await test_quality_metrics()
    
    print("\n✅ All validation tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
