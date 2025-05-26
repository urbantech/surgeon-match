from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import Field, validator, HttpUrl, EmailStr
from .base import BaseSchema

class APIKeyBase(BaseSchema):
    """Base schema for API key operations."""
    name: str = Field(..., description="A descriptive name for the API key")
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Number of days until the key expires (default: never)"
    )

class APIKeyCreate(APIKeyBase):
    """Schema for creating a new API key."""
    pass

class APIKeyUpdate(APIKeyBase):
    """Schema for updating an existing API key."""
    is_active: Optional[bool] = Field(None, description="Whether the key is active")

class APIKeyInDB(APIKeyBase):
    """Schema for API key stored in the database."""
    id: str
    key: Optional[str] = Field(None, description="The actual API key (only shown once on creation)")
    is_active: bool = Field(True, description="Whether the key is active")
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class APIKeyResponse(APIKeyInDB):
    """Schema for API key response (excludes the actual key by default)."""
    key: Optional[str] = Field(None, exclude=True)

class APIKeyWithToken(APIKeyInDB):
    """Schema for API key creation response (includes the actual key)."""
    key: str = Field(..., description="The API key (only shown once)")

class APIKeyUsageLog(BaseSchema):
    """Schema for API key usage logs."""
    id: str
    endpoint: str
    method: str
    status_code: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class APIKeyDetail(APIKeyResponse):
    """Detailed API key information including usage logs."""
    usage_logs: List[APIKeyUsageLog] = Field(default_factory=list)
