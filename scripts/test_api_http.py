#!/usr/bin/env python
"""
HTTP Test script for SurgeonMatch API endpoints.
This follows the SurgeonMatch Project Standards for testing and validation.
"""
import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

import httpx

# API configuration
API_BASE_URL = "http://localhost:8888"
API_KEY = "7716103218ca43bed0aabe70c382eea2cecd676e990190bf66c701712b1a6136"
API_PREFIX = "/api/v1"

# Headers for all requests
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

async def test_health_endpoint():
    """Test the health check endpoint."""
    logger.info("=== Testing Health Endpoint ===")
    
    # Test root health endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health", headers=HEADERS)
        
        if response.status_code == 200:
            logger.info(f"✅ Root health endpoint: {response.status_code}")
            logger.info(f"   Response: {response.json()}")
        else:
            logger.error(f"❌ Root health endpoint failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
    
    # Test API health endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}{API_PREFIX}/health", headers=HEADERS)
        
        if response.status_code == 200:
            logger.info(f"✅ API health endpoint: {response.status_code}")
            logger.info(f"   Response: {response.json()}")
        else:
            logger.error(f"❌ API health endpoint failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")

async def test_surgeons_endpoints():
    """Test the surgeons endpoints."""
    logger.info("=== Testing Surgeons Endpoints ===")
    
    # GET /surgeons
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}{API_PREFIX}/surgeons", headers=HEADERS)
        
        if response.status_code == 200:
            surgeons = response.json()
            logger.info(f"✅ GET surgeons: {response.status_code}")
            logger.info(f"   Found {len(surgeons)} surgeons")
            
            # If surgeons found, test the detail endpoint
            if surgeons:
                surgeon_id = surgeons[0]["id"]
                detail_response = await client.get(
                    f"{API_BASE_URL}{API_PREFIX}/surgeons/{surgeon_id}", 
                    headers=HEADERS
                )
                
                if detail_response.status_code == 200:
                    logger.info(f"✅ GET surgeon detail: {detail_response.status_code}")
                    logger.info(f"   Surgeon: {detail_response.json()['first_name']} {detail_response.json()['last_name']}")
                else:
                    logger.error(f"❌ GET surgeon detail failed: {detail_response.status_code}")
                    logger.error(f"   Response: {detail_response.text}")
        else:
            logger.error(f"❌ GET surgeons failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")

async def test_claims_endpoints():
    """Test the claims endpoints."""
    logger.info("=== Testing Claims Endpoints ===")
    
    # GET /claims
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}{API_PREFIX}/claims", headers=HEADERS)
        
        if response.status_code == 200:
            claims = response.json()
            logger.info(f"✅ GET claims: {response.status_code}")
            logger.info(f"   Found {len(claims)} claims")
            
            # If claims found, test the detail endpoint
            if claims:
                claim_id = claims[0]["id"]
                detail_response = await client.get(
                    f"{API_BASE_URL}{API_PREFIX}/claims/{claim_id}", 
                    headers=HEADERS
                )
                
                if detail_response.status_code == 200:
                    logger.info(f"✅ GET claim detail: {detail_response.status_code}")
                    logger.info(f"   Claim ID: {detail_response.json()['claim_id']}")
                else:
                    logger.error(f"❌ GET claim detail failed: {detail_response.status_code}")
                    logger.error(f"   Response: {detail_response.text}")
                    
            # Test claims by surgeon
            surgeons_response = await client.get(f"{API_BASE_URL}{API_PREFIX}/surgeons", headers=HEADERS)
            if surgeons_response.status_code == 200:
                surgeons = surgeons_response.json()
                if surgeons:
                    surgeon_id = surgeons[0]["id"]
                    surgeon_claims_response = await client.get(
                        f"{API_BASE_URL}{API_PREFIX}/surgeons/{surgeon_id}/claims", 
                        headers=HEADERS
                    )
                    
                    if surgeon_claims_response.status_code == 200:
                        logger.info(f"✅ GET surgeon claims: {surgeon_claims_response.status_code}")
                        logger.info(f"   Found {len(surgeon_claims_response.json())} claims for surgeon")
                    else:
                        logger.error(f"❌ GET surgeon claims failed: {surgeon_claims_response.status_code}")
                        logger.error(f"   Response: {surgeon_claims_response.text}")
        else:
            logger.error(f"❌ GET claims failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")

async def test_quality_metrics_endpoints():
    """Test the quality metrics endpoints."""
    logger.info("=== Testing Quality Metrics Endpoints ===")
    
    # GET /quality-metrics
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}{API_PREFIX}/quality-metrics", headers=HEADERS)
        
        if response.status_code == 200:
            metrics = response.json()
            logger.info(f"✅ GET quality metrics: {response.status_code}")
            logger.info(f"   Found {len(metrics)} quality metrics")
            
            # If metrics found, test the detail endpoint
            if metrics:
                metric_id = metrics[0]["id"]
                detail_response = await client.get(
                    f"{API_BASE_URL}{API_PREFIX}/quality-metrics/{metric_id}", 
                    headers=HEADERS
                )
                
                if detail_response.status_code == 200:
                    logger.info(f"✅ GET quality metric detail: {detail_response.status_code}")
                    logger.info(f"   Metric: {detail_response.json()['metric_name']}")
                else:
                    logger.error(f"❌ GET quality metric detail failed: {detail_response.status_code}")
                    logger.error(f"   Response: {detail_response.text}")
                    
            # Test quality metrics by surgeon
            surgeons_response = await client.get(f"{API_BASE_URL}{API_PREFIX}/surgeons", headers=HEADERS)
            if surgeons_response.status_code == 200:
                surgeons = surgeons_response.json()
                if surgeons:
                    surgeon_id = surgeons[0]["id"]
                    surgeon_metrics_response = await client.get(
                        f"{API_BASE_URL}{API_PREFIX}/surgeons/{surgeon_id}/quality-metrics", 
                        headers=HEADERS
                    )
                    
                    if surgeon_metrics_response.status_code == 200:
                        logger.info(f"✅ GET surgeon quality metrics: {surgeon_metrics_response.status_code}")
                        logger.info(f"   Found {len(surgeon_metrics_response.json())} metrics for surgeon")
                    else:
                        logger.error(f"❌ GET surgeon quality metrics failed: {surgeon_metrics_response.status_code}")
                        logger.error(f"   Response: {surgeon_metrics_response.text}")
        else:
            logger.error(f"❌ GET quality metrics failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")

async def main():
    """Run all HTTP tests for the SurgeonMatch API."""
    logger.info(f"Testing SurgeonMatch API endpoints at {API_BASE_URL}")
    
    # Check if the API server is running
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{API_BASE_URL}/health", timeout=2.0)
        logger.info("✅ API server is running")
    except httpx.ConnectError:
        logger.error("❌ API server is not running. Please start the server before running this script.")
        return
    except Exception as e:
        logger.error(f"❌ Error connecting to API server: {str(e)}")
        return
    
    # Run tests
    await test_health_endpoint()
    await test_surgeons_endpoints()
    await test_claims_endpoints()
    await test_quality_metrics_endpoints()
    
    logger.info("✅ All HTTP API tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
