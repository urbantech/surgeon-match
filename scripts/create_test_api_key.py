#!/usr/bin/env python
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from surgeonmatch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from surgeonmatch.core.security import create_api_key
from surgeonmatch.core.config import settings

async def main():
    # Create a database connection
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create a session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create an API key
    async with async_session() as session:
        key_value, key_id = await create_api_key(
            name="Test API Key",
            description="API key for testing rate limiting",
            db=session,
            is_active=True,
        )
        
        print(f"Created API key with ID: {key_id}")
        print(f"API key value: {key_value}")
        print(f"Use this key in the X-API-Key header for testing")

if __name__ == "__main__":
    asyncio.run(main())
