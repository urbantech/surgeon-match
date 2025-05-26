import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List, Type, Any

from sqlalchemy import text, MetaData, Table, Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql.ddl import CreateTable

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from surgeonmatch.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine and session
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def create_tables():
    """Create all database tables."""
    from surgeonmatch.models import Base
    
    logger.info("Creating database tables...")
    
    # Import all models to ensure they are registered with SQLAlchemy
    from surgeonmatch.models import (
        api_key,
        rate_limit,
        surgeon,
        claim,
        quality_metric
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")

async def drop_tables():
    """Drop all database tables."""
    from surgeonmatch.models import Base
    
    logger.warning("Dropping all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("All database tables dropped")

async def check_database_connection():
    """Check if the database connection is working."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def init_db():
    """Initialize the database by creating all tables."""
    if await check_database_connection():
        await create_tables()
    else:
        logger.error("Failed to initialize database: Could not connect to database")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management")
    parser.add_argument(
        "--drop", 
        action="store_true", 
        help="Drop all tables before creating them"
    )
    
    args = parser.parse_args()
    
    async def main():
        if args.drop:
            await drop_tables()
        await init_db()
    
    asyncio.run(main())
