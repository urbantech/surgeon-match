from typing import List, Optional, Dict, Any
from pydantic import Field, validator, HttpUrl, EmailStr
from datetime import datetime
from .base import BaseSchema

class Address(BaseSchema):
    """Schema for address information."""
    line1: str = Field(..., description="First line of the address")
    line2: Optional[str] = Field(None, description="Second line of the address")
    city: str = Field(..., description="City name")
    state: str = Field(..., min_length=2, max_length=2, description="State code (2 letters)")
    zip_code: str = Field(..., min_length=5, max_length=10, description="ZIP or postal code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Geographic latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Geographic longitude")

class SurgeonBase(BaseSchema):
    """Base schema for surgeon information."""
    npi: str = Field(..., min_length=10, max_length=10, description="National Provider Identifier (10 digits)")
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    specialty_code: str = Field(..., max_length=10, description="Specialty code")
    specialty_description: Optional[str] = Field(None, max_length=255, description="Specialty description")
    
    # Contact information
    email: Optional[EmailStr] = Field(None, description="Professional email address")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    
    # Practice information
    accepts_medicare: bool = Field(False, description="Whether the surgeon accepts Medicare")
    is_active: bool = Field(True, description="Whether the surgeon is currently active")
    
    # Address
    address: Optional[Address] = Field(None, description="Primary practice address")
    
    @validator('npi')
    def validate_npi(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("NPI must be a 10-digit number")
        return v

class SurgeonCreate(SurgeonBase):
    """Schema for creating a new surgeon."""
    pass

class SurgeonUpdate(BaseSchema):
    """Schema for updating an existing surgeon."""
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    specialty_code: Optional[str] = Field(None, max_length=10, description="Specialty code")
    specialty_description: Optional[str] = Field(None, max_length=255, description="Specialty description")
    email: Optional[EmailStr] = Field(None, description="Professional email address")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    accepts_medicare: Optional[bool] = Field(None, description="Whether the surgeon accepts Medicare")
    is_active: Optional[bool] = Field(None, description="Whether the surgeon is currently active")
    address: Optional[Address] = Field(None, description="Primary practice address")

class SurgeonInDB(SurgeonBase):
    """Schema for surgeon data stored in the database."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_claims: int = Field(0, description="Total number of claims")
    average_quality_score: Optional[float] = Field(None, description="Average quality score (0-100)")
    
    class Config:
        from_attributes = True

class SurgeonResponse(SurgeonInDB):
    """Schema for surgeon API response."""
    pass

class SurgeonListResponse(BaseSchema):
    """Schema for paginated list of surgeons."""
    items: List[SurgeonResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")
    total_pages: int = Field(0, description="Total number of pages")

class SurgeonSearchFilters(BaseSchema):
    """Schema for surgeon search filters."""
    name: Optional[str] = Field(None, description="Search by surgeon name")
    specialty: Optional[str] = Field(None, description="Filter by specialty code")
    accepts_medicare: Optional[bool] = Field(None, description="Filter by Medicare acceptance")
    min_quality_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum quality score")
    location: Optional[Dict[str, float]] = Field(
        None,
        description="Geo-location filter with 'lat' and 'lng' keys and radius in miles"
    )
    radius_miles: Optional[float] = Field(25.0, ge=0, le=500, description="Search radius in miles")
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None:
            if 'lat' not in v or 'lng' not in v:
                raise ValueError("Location must include 'lat' and 'lng'")
            if not (-90 <= v['lat'] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v['lng'] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v
