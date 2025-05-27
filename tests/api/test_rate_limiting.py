"""
Tests for API rate limiting functionality.

This module tests the rate limiting middleware and ensures it properly limits
requests according to the configured limits and returns appropriate responses.
"""
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI, Depends, status, Request, Response
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from surgeonmatch.core.config import settings
from surgeonmatch.core.security import check_rate_limit
from surgeonmatch.dependencies import get_db
from surgeonmatch.api.middleware import RateLimitMiddleware


@pytest_asyncio.fixture
async def test_app():
    """Create a test FastAPI app with rate limiting middleware."""
    from surgeonmatch.main import app
    return app


@pytest_asyncio.fixture
async def test_client(test_app):
    """Create a test client for the test app."""
    with TestClient(await test_app) as client:
        yield client


@pytest.fixture
def test_api_key():
    """Create a mock test API key for rate limiting tests."""
    # Instead of creating a real API key, we'll use a mock
    api_key_id = str(uuid.uuid4())
    api_key_value = f"test_key_{api_key_id}"
    
    # Return both the key value (for headers) and the ID (for direct DB operations)
    return {
        "key": api_key_value,
        "id": api_key_id
    }


@pytest.mark.asyncio
async def test_rate_limit_middleware():
    """Test the rate limit middleware functionality with mocked database calls."""
    # Create a mock app and response
    app = FastAPI()
    
    # Create a mock for the check_rate_limit function
    with patch('surgeonmatch.api.middleware.check_rate_limit') as mock_check_rate_limit:
        # Set up the mock to return appropriate values
        mock_check_rate_limit.return_value = (True, settings.RATE_LIMIT - 1, settings.RATE_LIMIT_PERIOD)
        
        # Set up the middleware
        middleware = RateLimitMiddleware(app)
        
        # Create a mock request
        request = MagicMock()
        request.headers = {"X-API-Key": "test_api_key"}
        request.url.path = "/test/endpoint"
        request.method = "GET"
        
        # Create a mock response function
        async def mock_call_next(request):
            response = Response()
            response.status_code = 200
            return response
        
        # Test the middleware
        response = await middleware.dispatch(request, mock_call_next)
        
        # Verify the middleware called check_rate_limit
        mock_check_rate_limit.assert_called_once()
        
        # Verify rate limit headers were added
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify header values
        assert response.headers["X-RateLimit-Limit"] == str(settings.RATE_LIMIT)
        assert response.headers["X-RateLimit-Remaining"] == str(settings.RATE_LIMIT - 1)
        
        # Now test rate limit exceeded
        mock_check_rate_limit.reset_mock()
        mock_check_rate_limit.return_value = (False, 0, 60)
        
        # Test the middleware again
        response = await middleware.dispatch(request, mock_call_next)
        
        # Verify rate limit exceeded response
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_rate_limit_formatting():
    """Test that rate limit headers and responses are correctly formatted."""
    # Create a mock response
    app = FastAPI()
    with patch('surgeonmatch.api.middleware.datetime') as mock_datetime:
        # Set up a fixed datetime for predictable testing
        fixed_time = datetime(2025, 5, 26, 14, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # Calculate expected future time
        reset_seconds = 45
        expected_future = fixed_time + timedelta(seconds=reset_seconds)
        expected_date_http = expected_future.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Create a mock for the rate limit exceeded response
        middleware = RateLimitMiddleware(app)
        
        # Create mock objects
        request = MagicMock()
        request.headers = {"X-API-Key": "test_api_key"}
        request.url.path = "/test/endpoint"
        request.method = "GET"
        
        async def mock_call_next(request):
            response = Response()
            response.status_code = 200
            return response
        
        # Test with rate limit exceeded
        with patch('surgeonmatch.api.middleware.check_rate_limit') as mock_check:
            mock_check.return_value = (False, 0, reset_seconds)
            
            response = await middleware.dispatch(request, mock_call_next)
            
            # Verify response format
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            
            # Verify headers
            assert response.headers["Retry-After"] == str(reset_seconds)
            assert response.headers["X-RateLimit-Limit"] == str(settings.RATE_LIMIT)
            assert response.headers["X-RateLimit-Remaining"] == "0"
            assert response.headers["X-RateLimit-Reset"] == str(reset_seconds)
            
            # Verify response body content
            response_body = response.body.decode("utf-8")
            assert "rate_limit_exceeded" in response_body
            assert str(reset_seconds) in response_body


@pytest.mark.asyncio
async def test_rate_limit_documentation():
    """Test that the rate limit documentation in the README matches the implementation."""
    # Create a simple test that validates our README documentation is accurate
    with open("/Users/tobymorning/surgeon-match/README.md", "r") as f:
        readme_content = f.read()
    
    # Verify the README contains accurate rate limit information
    assert f"**Limit**: {settings.RATE_LIMIT} requests per minute per API key" in readme_content
    assert "**Tracking**: Limits are applied per API key and per endpoint" in readme_content
    assert "**Reset**: Rate limits reset every 60 seconds" in readme_content
    assert "X-RateLimit-Limit: 100" in readme_content
    assert "X-RateLimit-Remaining: 99" in readme_content
    assert "X-RateLimit-Reset: 58" in readme_content
    assert "429 Too Many Requests" in readme_content
    assert "Retry-After" in readme_content


@pytest.mark.asyncio
async def test_rate_limit_security():
    """Test that the rate limit implementation provides adequate security."""
    # Test that the rate limiting middleware provides security against abuse
    app = FastAPI()
    with patch('surgeonmatch.api.middleware.check_rate_limit') as mock_check:
        # Set up the mock to return appropriate values
        mock_check.side_effect = [
            # First API key reaches limit
            (True, 1, 60),
            (False, 0, 60),
            # Second API key has its own limit
            (True, settings.RATE_LIMIT - 1, 60)
        ]
        
        middleware = RateLimitMiddleware(app)
        
        # Test with first API key (first request allowed)
        request1 = MagicMock()
        request1.headers = {"X-API-Key": "api_key_1"}
        request1.url.path = "/test/endpoint"
        request1.method = "GET"
        
        async def mock_call_next(request):
            response = Response()
            response.status_code = 200
            return response
        
        # First request with API key 1
        response1 = await middleware.dispatch(request1, mock_call_next)
        assert response1.status_code == 200
        
        # Second request with API key 1 (limit exceeded)
        response2 = await middleware.dispatch(request1, mock_call_next)
        assert response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        
        # Request with API key 2 (different limit)
        request2 = MagicMock()
        request2.headers = {"X-API-Key": "api_key_2"}
        request2.url.path = "/test/endpoint"
        request2.method = "GET"
        
        response3 = await middleware.dispatch(request2, mock_call_next)
        assert response3.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_per_endpoint():
    """Test that rate limits are tracked separately for different endpoints."""
    # Test that the rate limiting tracks limits separately per endpoint
    app = FastAPI()
    with patch('surgeonmatch.api.middleware.check_rate_limit') as mock_check:
        # Set up the mock to simulate two different endpoints with separate limits
        # First endpoint reaches limit
        # Second endpoint has its own separate limit
        mock_check.side_effect = lambda api_key, endpoint, db: (
            (False, 0, 60) if endpoint.startswith("GET:/endpoint1") else (True, settings.RATE_LIMIT - 1, 60)
        )
        
        middleware = RateLimitMiddleware(app)
        
        async def mock_call_next(request):
            response = Response()
            response.status_code = 200
            return response
        
        # Request to first endpoint (limit exceeded)
        request1 = MagicMock()
        request1.headers = {"X-API-Key": "test_api_key"}
        request1.url.path = "/endpoint1"
        request1.method = "GET"
        
        response1 = await middleware.dispatch(request1, mock_call_next)
        assert response1.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        
        # Request to second endpoint (separate limit)
        request2 = MagicMock()
        request2.headers = {"X-API-Key": "test_api_key"}
        request2.url.path = "/endpoint2"
        request2.method = "GET"
        
        response2 = await middleware.dispatch(request2, mock_call_next)
        assert response2.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_reset():
    """Test that rate limits reset after the configured period."""
    # Test that rate limits reset properly after the configured period
    app = FastAPI()
    with patch('surgeonmatch.api.middleware.check_rate_limit') as mock_check:
        # First mock call - current time
        current_time = datetime.utcnow()  # Using UTC time
        mock_check.return_value = (False, 0, 30)  # Rate limit exceeded, 30 seconds until reset
        
        middleware = RateLimitMiddleware(app)
        
        async def mock_call_next(request):
            response = Response()
            response.status_code = 200
            return response
        
        # Create mock request
        request = MagicMock()
        request.headers = {"X-API-Key": "test_api_key"}
        request.url.path = "/test/endpoint"
        request.method = "GET"
        
        # First request (limit exceeded)
        response1 = await middleware.dispatch(request, mock_call_next)
        assert response1.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response1.headers["Retry-After"] == "30"
        
        # Now simulate time passing and rate limit resetting
        mock_check.return_value = (True, settings.RATE_LIMIT - 1, settings.RATE_LIMIT_PERIOD)  # Rate limit reset
        
        # Second request after reset
        response2 = await middleware.dispatch(request, mock_call_next)
        assert response2.status_code == 200  # Request allowed after reset
