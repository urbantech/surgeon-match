"""
Test configuration and fixtures for the SurgeonMatch project.

This module contains pytest fixtures that are available to all test modules.
"""
import os
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from surgeonmatch.core.database import get_test_db
from surgeonmatch.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for testing async code."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session with transaction rollback."""
    async for session in get_test_db():
        yield session
