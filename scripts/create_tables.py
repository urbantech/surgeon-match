"""Script to manually create database tables."""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from surgeonmatch.core.database import engine, Base
from surgeonmatch.models import (
    api_key,  # noqa: F401
    rate_limit,  # noqa: F401
    surgeon,  # noqa: F401
    claim,  # noqa: F401
    quality_metric,  # noqa: F401
)

async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    
    # Create all tables
    async with engine.begin() as conn:
        print("Dropping all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # Verify tables were created
        result = await conn.execute(
            text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                """
            )
        )
        tables = [row[0] for row in result]
        print(f"\nCreated tables: {tables}")

if __name__ == "__main__":
    asyncio.run(create_tables())
