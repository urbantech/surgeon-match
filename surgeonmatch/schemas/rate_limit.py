from datetime import datetime
from pydantic import Field, validator, conint
from typing import Optional, Dict, Any
from .base import BaseSchema

class RateLimitBase(BaseSchema):
    """Base schema for rate limiting."""
    key: str = Field(..., description="Rate limit key (usually 'api_key:endpoint')")
    limit: int = Field(..., ge=1, description="Maximum number of requests allowed")
    period: int = Field(..., ge=1, description="Time period in seconds")

class RateLimitCreate(RateLimitBase):
    """Schema for creating a new rate limit rule."""
    pass

class RateLimitUpdate(BaseSchema):
    """Schema for updating an existing rate limit rule."""
    limit: Optional[int] = Field(None, ge=1, description="Maximum number of requests allowed")
    period: Optional[int] = Field(None, ge=1, description="Time period in seconds")
    is_active: Optional[bool] = Field(None, description="Whether the rate limit is active")

class RateLimitInDB(RateLimitBase):
    """Schema for rate limit stored in the database."""
    id: str
    count: int = Field(0, ge=0, description="Current request count")
    expires_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = Field(True, description="Whether the rate limit is active")
    
    class Config:
        from_attributes = True

class RateLimitResponse(RateLimitInDB):
    """Schema for rate limit response."""
    remaining: int = Field(0, ge=0, description="Remaining requests in the current period")
    reset_in: int = Field(0, ge=0, description="Seconds until the rate limit resets")
    
    @validator('remaining', pre=True, always=True)
    def calculate_remaining(cls, v, values):
        return values.get('limit', 0) - values.get('count', 0)
    
    @validator('reset_in', pre=True, always=True)
    def calculate_reset_in(cls, v, values):
        expires_at = values.get('expires_at')
        if not expires_at:
            return 0
        return max(0, int((expires_at - datetime.utcnow()).total_seconds()))

class RateLimitStats(BaseSchema):
    """Schema for rate limit statistics."""
    total_requests: int = Field(0, description="Total number of requests")
    allowed_requests: int = Field(0, description="Number of allowed requests")
    blocked_requests: int = Field(0, description="Number of blocked requests")
    active_rules: int = Field(0, description="Number of active rate limit rules")
    
    class Config:
        from_attributes = True

class RateLimitHeaders(BaseSchema):
    """Schema for rate limit HTTP headers."""
    ratelimit_limit: int = Field(..., alias="X-RateLimit-Limit")
    ratelimit_remaining: int = Field(..., alias="X-RateLimit-Remaining")
    ratelimit_reset: int = Field(..., alias="X-RateLimit-Reset")
    
    class Config:
        allow_population_by_field_name = True
