from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime as SQLDateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base

class RateLimit(Base):
    """Rate limiting model to track and enforce API rate limits."""
    __tablename__ = "rate_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), nullable=False, index=True, comment="Composite key: 'api_key:endpoint:period'")
    count = Column(Integer, default=0, nullable=False)
    period = Column(Integer, nullable=False, comment="Rate limit period in seconds")
    expires_at = Column(SQLDateTime, nullable=False, index=True)
    created_at = Column(SQLDateTime, server_default=func.now())
    updated_at = Column(SQLDateTime, onupdate=func.now())
    
    # Removed PostgreSQL partitioning for simplicity
    
    def is_exceeded(self, limit: int) -> bool:
        """Check if the rate limit has been exceeded."""
        return self.count >= limit
    
    def increment(self) -> None:
        """Increment the request count."""
        self.count += 1
        self.updated_at = datetime.utcnow()
    
    def reset(self) -> None:
        """Reset the rate limit counter."""
        self.count = 0
        self.updated_at = datetime.utcnow()
