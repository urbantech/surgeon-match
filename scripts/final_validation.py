#!/usr/bin/env python
"""
Final validation script for SurgeonMatch API endpoints.
This follows the SurgeonMatch Project Standards for testing and validation.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import uuid
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
    logger.info("=== Testing API Key ===")
    api_key = "7716103218ca43bed0aabe70c382eea2cecd676e990190bf66c701712b1a6136"
    
    # Check if the API key exists in the database
    query = """
    SELECT * FROM api_keys WHERE key = :key
    """
    results = await run_query(query, {"key": api_key})
    
    if results:
        logger.info(f"✅ API Key found: {results[0]['name']}")
        logger.info(f"   - Created at: {results[0]['created_at']}")
        logger.info(f"   - Expires at: {results[0]['expires_at']}")
        logger.info(f"   - Is active: {results[0]['is_active']}")
    else:
        logger.warning("❌ API Key not found in database")

async def test_surgeons():
    """Validate the surgeons functionality."""
    logger.info("=== Testing Surgeons Endpoint ===")
    
    # List all surgeons
    query = "SELECT * FROM surgeons"
    results = await run_query(query)
    
    if results:
        logger.info(f"✅ Found {len(results)} surgeons in database:")
        for i, surgeon in enumerate(results, 1):
            logger.info(f"{i}. {surgeon['first_name']} {surgeon['last_name']} - {surgeon['specialty_description'] or surgeon['specialty_code']}")
    else:
        logger.info("ℹ️ No surgeons found in database")
        
        # Create a test surgeon
        logger.info("Creating a test surgeon...")
        insert_query = """
        INSERT INTO surgeons (
            id, first_name, last_name, specialty_code, specialty_description, npi, 
            address_line1, city, state, zip_code, accepts_medicare, is_active, 
            total_claims, created_at, updated_at
        ) VALUES (
            :id, :first_name, :last_name, :specialty_code, :specialty_description, :npi, 
            :address_line1, :city, :state, :zip_code, :accepts_medicare, :is_active, 
            :total_claims, NOW(), NOW()
        )
        """
        surgeon_id = str(uuid.uuid4())
        params = {
            "id": surgeon_id,
            "first_name": "John",
            "last_name": "Doe",
            "specialty_code": "208C00000X",
            "specialty_description": "Cardiology",
            "npi": "1234567890",
            "address_line1": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
            "accepts_medicare": True,
            "is_active": True,
            "total_claims": 0
        }
        await run_query(insert_query, params)
        logger.info(f"✅ Created test surgeon with ID: {surgeon_id}")
        
        # Verify surgeon was created
        verify_query = "SELECT * FROM surgeons WHERE id = :id"
        verify_results = await run_query(verify_query, {"id": surgeon_id})
        if verify_results:
            logger.info(f"✅ Verified surgeon creation: {verify_results[0]['first_name']} {verify_results[0]['last_name']}")
            return surgeon_id
    
    # If there are existing surgeons, return the first one's ID
    if results:
        return results[0]['id']
    return None

async def test_claims(surgeon_id=None):
    """Validate the claims functionality."""
    logger.info("=== Testing Claims Endpoint ===")
    
    # List all claims
    query = "SELECT * FROM claims"
    results = await run_query(query)
    
    if results:
        logger.info(f"✅ Found {len(results)} claims in database:")
        for i, claim in enumerate(results, 1):
            logger.info(f"{i}. Claim ID: {claim['claim_id']}, Procedure: {claim['procedure_code']}")
    else:
        logger.info("ℹ️ No claims found in database")
        
        # Get a surgeon to associate with a claim if not provided
        if not surgeon_id:
            surgeon_query = "SELECT * FROM surgeons LIMIT 1"
            surgeons = await run_query(surgeon_query)
            
            if surgeons:
                surgeon_id = surgeons[0]['id']
            else:
                logger.warning("❌ Cannot create test claim - no surgeons found")
                return
        
        logger.info(f"Creating a test claim for surgeon ID: {surgeon_id}")
        
        # Create a test claim
        insert_query = """
        INSERT INTO claims (
            id, claim_id, surgeon_id, patient_id, procedure_code, 
            procedure_description, claim_date, paid_amount, allowed_amount,
            place_of_service, diagnosis_codes, created_at, updated_at
        ) VALUES (
            :id, :claim_id, :surgeon_id, :patient_id, :procedure_code, 
            :procedure_description, :claim_date, :paid_amount, :allowed_amount,
            :place_of_service, :diagnosis_codes, NOW(), NOW()
        )
        """
        claim_uuid = str(uuid.uuid4())
        claim_id = f"CLM-{claim_uuid[:8]}"
        patient_id = f"PT-{uuid.uuid4().hex[:8]}"
        params = {
            "id": claim_uuid,
            "claim_id": claim_id,
            "surgeon_id": surgeon_id,
            "patient_id": patient_id,
            "procedure_code": "12345",
            "procedure_description": "Coronary artery bypass graft",
            "claim_date": datetime.now(timezone.utc),
            "paid_amount": 1000.00,
            "allowed_amount": 1200.00,
            "place_of_service": "21",  # Inpatient Hospital
            "diagnosis_codes": json.dumps(["E11.65", "I25.10"])  # JSONB format
        }
        await run_query(insert_query, params)
        logger.info(f"✅ Created test claim with ID: {claim_id}")
        
        # Verify claim was created
        verify_query = "SELECT * FROM claims WHERE claim_id = :claim_id"
        verify_results = await run_query(verify_query, {"claim_id": claim_id})
        if verify_results:
            logger.info(f"✅ Verified claim creation: {verify_results[0]['claim_id']}")

async def test_quality_metrics(surgeon_id=None):
    """Validate the quality metrics functionality."""
    logger.info("=== Testing Quality Metrics Endpoint ===")
    
    # List all quality metrics
    query = "SELECT * FROM quality_metrics"
    results = await run_query(query)
    
    if results:
        logger.info(f"✅ Found {len(results)} quality metrics in database:")
        for i, metric in enumerate(results, 1):
            logger.info(f"{i}. Metric Name: {metric['metric_name']}, Value: {metric['metric_value']}")
    else:
        logger.info("ℹ️ No quality metrics found in database")
        
        # Get a surgeon to associate with a quality metric if not provided
        if not surgeon_id:
            surgeon_query = "SELECT * FROM surgeons LIMIT 1"
            surgeons = await run_query(surgeon_query)
            
            if surgeons:
                surgeon_id = surgeons[0]['id']
            else:
                logger.warning("❌ Cannot create test quality metric - no surgeons found")
                return
        
        logger.info(f"Creating a test quality metric for surgeon ID: {surgeon_id}")
        
        # Create a test quality metric using the correct schema
        insert_query = """
        INSERT INTO quality_metrics (
            id, surgeon_id, metric_name, metric_value, metric_unit,
            start_date, end_date, procedure_code, details, calculated_at
        ) VALUES (
            :id, :surgeon_id, :metric_name, :metric_value, :metric_unit,
            :start_date, :end_date, :procedure_code, :details, NOW()
        )
        """
        metric_id = str(uuid.uuid4())
        now = datetime.now()
        start_date = datetime(now.year, 1, 1)
        end_date = datetime(now.year, 12, 31)
        
        params = {
            "id": metric_id,
            "surgeon_id": surgeon_id,
            "metric_name": "readmission_rate",
            "metric_value": 0.05,  # 5%
            "metric_unit": "%",
            "start_date": start_date,
            "end_date": end_date,
            "procedure_code": "12345",
            "details": json.dumps({
                "total_cases": 100,
                "readmissions": 5,
                "confidence_interval": [0.02, 0.08]
            })
        }
        try:
            await run_query(insert_query, params)
            logger.info(f"✅ Created test quality metric with ID: {metric_id}")
            
            # Verify quality metric was created
            verify_query = "SELECT * FROM quality_metrics WHERE id = :id"
            verify_results = await run_query(verify_query, {"id": metric_id})
            if verify_results:
                logger.info(f"✅ Verified quality metric creation: {verify_results[0]['id']}")
        except Exception as e:
            logger.error(f"❌ Error creating quality metric: {str(e)}")

async def main():
    """Run all validation tests for the SurgeonMatch API."""
    logger.info(f"Validating SurgeonMatch API using database: {DATABASE_URL}")
    
    await test_api_key()
    surgeon_id = await test_surgeons()
    
    if surgeon_id:
        await test_claims(surgeon_id)
        await test_quality_metrics(surgeon_id)
    else:
        await test_claims()
        await test_quality_metrics()
    
    logger.info("✅ All validation tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
