import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..core.config import settings
from ..models import Base  # Import Base from models to ensure all models are registered

# Configure logging
logger = logging.getLogger(__name__)


# Create SQLAlchemy engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Base class is imported from models to ensure all models are registered
# Database session factory is now in dependencies.py to avoid circular imports

# Database initialization
async def init_db() -> None:
    """Initialize database connection and create tables."""
    logger.info("Initializing database...")
    
    # Import all models here to ensure they are registered with SQLAlchemy
    from ..models import api_key, rate_limit, surgeon, claim, quality_metric
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")

async def close_db() -> None:
    """Close database connection."""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")

# Helper function to get a new session for testing
async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a new database session for testing.
    
    This creates a new connection with a savepoint that is rolled back after the test.
    """
    async with async_session_factory() as session:
        # Start a transaction
        transaction = await session.begin()
        
        try:
            yield session
        finally:
            # Roll back the transaction to clean up test data
            await transaction.rollback()
            await session.close()

# Helper function to get a raw database connection
async def get_connection():
    """Get a raw database connection."""
    return await engine.connect()
