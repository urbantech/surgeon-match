"""
Script to create an initial API key in the database.
This is used for bootstrapping the system.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import hashlib
import uuid
from typing import Optional
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from surgeonmatch.core.config import settings
from surgeonmatch.core.database import engine, Base

async def create_initial_api_key() -> None:
    """Create an initial API key in the database."""
    print("Creating initial API key...")
    
    # Generate a new API key
    api_key = settings.API_KEY  # Use the key from settings
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create a SQLAlchemy async connection
    async with engine.begin() as conn:
        # Create api_keys table if it doesn't exist
        await conn.run_sync(Base.metadata.create_all)
        
        # Check if api_key already exists
        result = await conn.execute(
            text("""
            SELECT COUNT(*) FROM api_keys 
            WHERE key = :hashed_key
            """),
            {"hashed_key": hashed_key}
        )
        count = result.scalar()
        
        if count > 0:
            print(f"API key already exists: {api_key}")
            return
        
        # Calculate expiration date (1 year from now)
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Insert API key
        await conn.execute(
            text("""
            INSERT INTO api_keys 
            (id, name, key, expires_at, created_by, created_at, updated_at, is_active)
            VALUES 
            (:id, :name, :key, :expires_at, :created_by, :created_at, :updated_at, :is_active)
            """),
            {
                "id": str(uuid.uuid4()),
                "name": "Initial API Key",
                "key": hashed_key,
                "expires_at": expires_at,
                "created_by": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
        )
        
        print(f"Created initial API key: {api_key}")
        print("You can use this API key to authenticate API requests with the X-API-Key header.")

if __name__ == "__main__":
    asyncio.run(create_initial_api_key())
