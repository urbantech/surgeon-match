"""Script to verify database connection and create tables."""
import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.sql.ddl import CreateTable

from surgeonmatch.core.config import settings
from surgeonmatch.models.base import Base

# Import all models to ensure they are registered with SQLAlchemy
from surgeonmatch.models import (
    api_key,  # noqa: F401
    rate_limit,  # noqa: F401
    surgeon,  # noqa: F401
    claim,  # noqa: F401
    quality_metric,  # noqa: F401
)

def get_table_names(engine: AsyncEngine) -> list:
    """Get list of table names in the database."""
    inspector = inspect(engine.sync_engine)
    return inspector.get_table_names()

async def verify_database():
    """Verify database connection and create tables."""
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    
    # Create a new engine with echo=True for debugging
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True,
    )
    
    try:
        # Test connection
        async with engine.connect() as conn:
            logger.info("Testing connection...")
            result = await conn.execute(text("SELECT 1"))
            logger.info(f"Connection test result: {result.scalar()}")
            
            # Check current tables
            result = await conn.execute(
                text("SELECT current_database()")
            )
            db_name = result.scalar()
            logger.info(f"Connected to database: {db_name}")
            
            # List all tables before creation
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
            logger.info(f"Tables in database before creation: {tables}")
        
        # Create all tables
        logger.info("\nCreating tables...")
        async with engine.begin() as conn:
            # Log the tables that will be created
            for table_name, table in Base.metadata.tables.items():
                logger.info(f"Will create table: {table_name}")
                # Log the SQL that would be executed
                create_sql = str(CreateTable(table).compile(engine.sync_engine))
                logger.debug(f"SQL for {table_name}:\n{create_sql}")
            
            # Create tables
            logger.info("Executing table creation...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Table creation command completed.")
            
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
            logger.info(f"Tables in database after creation: {tables}")
            
            if not tables:
                logger.error("No tables were created. Checking for errors...")
                # Try to create a test table directly
                try:
                    logger.info("Attempting to create a test table...")
                    await conn.execute(
                        text("""
                        CREATE TABLE IF NOT EXISTS test_table (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(100)
                        )
                        """)
                    )
                    logger.info("Test table created successfully.")
                    
                    # Verify test table exists
                    result = await conn.execute(
                        text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'test_table'
                        """)
                    )
                    test_table_exists = bool(result.scalar())
                    logger.info(f"Test table exists: {test_table_exists}")
                    
                except Exception as e:
                    logger.error(f"Error creating test table: {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_database())
