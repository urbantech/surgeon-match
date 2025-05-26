"""Script to check database connection and table creation."""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from surgeonmatch.core.database import engine, Base, init_db
from surgeonmatch.models import api_key, rate_limit, surgeon, claim, quality_metric

async def check_database():
    print("Checking database connection and tables...")
    
    # Initialize the database
    await init_db()
    
    # Check if tables exist
    async with engine.begin() as conn:
        # Check if api_keys table exists
        result = await conn.execute(
            text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'api_keys'
            )
            """)
        )
        exists = result.scalar()
        print(f"API Keys table exists: {exists}")
        
        # List all tables
        result = await conn.execute(
            text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """)
        )
        tables = [row[0] for row in result]
        print(f"\nAll tables in database: {tables}")

if __name__ == "__main__":
    asyncio.run(check_database())
