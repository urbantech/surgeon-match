"""Script to check database connection and list tables."""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from surgeonmatch.core.config import settings

async def check_connection():
    """Check database connection and list tables."""
    print(f"Connecting to database: {settings.DATABASE_URL}")
    
    # Create a new engine with echo=True for debugging
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True,
    )
    
    try:
        async with engine.connect() as conn:
            # Test connection
            print("Testing connection...")
            result = await conn.execute(text("SELECT 1"))
            print(f"Connection test result: {result.scalar()}")
            
            # List all tables in the database
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
            print(f"\nTables in database: {tables}")
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_connection())
