from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base

class APIKey(Base):
    """API Key model for authentication."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), nullable=True)  # Email or username of the creator
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    usage_logs = relationship("APIKeyUsageLog", back_populates="api_key")
    
    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired


class APIKeyUsageLog(Base):
    """Log of API key usage for analytics and monitoring."""
    __tablename__ = "api_key_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(String(3), nullable=True)
    client_ip = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
