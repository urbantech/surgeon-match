from typing import List, Optional, Dict, Any
from pydantic import Field, validator, HttpUrl, condecimal
from datetime import datetime, date
from decimal import Decimal
from .base import BaseSchema

class ClaimBase(BaseSchema):
    """Base schema for claim information."""
    claim_id: str = Field(..., max_length=50, description="Unique claim identifier")
    surgeon_id: str = Field(..., description="ID of the surgeon who performed the procedure")
    patient_id: str = Field(..., max_length=50, description="Patient identifier")
    
    # Procedure information
    procedure_code: str = Field(..., max_length=10, description="Procedure code (CPT/HCPCS)")
    procedure_description: Optional[str] = Field(None, max_length=255, description="Procedure description")
    claim_date: date = Field(..., description="Date the procedure was performed")
    
    # Financial information
    paid_amount: condecimal(ge=0, decimal_places=2) = Field(..., description="Amount paid for the claim")
    allowed_amount: condecimal(ge=0, decimal_places=2) = Field(..., description="Allowed amount for the claim")
    
    # Additional details
    place_of_service: Optional[str] = Field(None, max_length=10, description="Place of service code")
    diagnosis_codes: Optional[List[str]] = Field(None, description="List of diagnosis codes (ICD-10)")
    
    @validator('diagnosis_codes', each_item=True)
    def validate_diagnosis_codes(cls, v):
        if not v:
            return v
        if not isinstance(v, str) or len(v) < 3:
            raise ValueError("Diagnosis codes must be strings with at least 3 characters")
        return v.upper()

class ClaimCreate(ClaimBase):
    """Schema for creating a new claim."""
    pass

class ClaimUpdate(BaseSchema):
    """Schema for updating an existing claim."""
    procedure_code: Optional[str] = Field(None, max_length=10, description="Procedure code (CPT/HCPCS)")
    procedure_description: Optional[str] = Field(None, max_length=255, description="Procedure description")
    claim_date: Optional[date] = Field(None, description="Date the procedure was performed")
    paid_amount: Optional[Decimal] = Field(None, ge=0, description="Amount paid for the claim")
    allowed_amount: Optional[Decimal] = Field(None, ge=0, description="Allowed amount for the claim")
    place_of_service: Optional[str] = Field(None, max_length=10, description="Place of service code")
    diagnosis_codes: Optional[List[str]] = Field(None, description="List of diagnosis codes (ICD-10)")

class ClaimInDB(ClaimBase):
    """Schema for claim data stored in the database."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }

class ClaimResponse(ClaimInDB):
    """Schema for claim API response."""
    pass

class ClaimListResponse(BaseSchema):
    """Schema for paginated list of claims."""
    items: List[ClaimResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")
    total_pages: int = Field(0, description="Total number of pages")

class ClaimSearchFilters(BaseSchema):
    """Schema for claim search filters."""
    surgeon_id: Optional[str] = Field(None, description="Filter by surgeon ID")
    patient_id: Optional[str] = Field(None, description="Filter by patient ID")
    procedure_code: Optional[str] = Field(None, description="Filter by procedure code")
    min_date: Optional[date] = Field(None, description="Earliest claim date (inclusive)")
    max_date: Optional[date] = Field(None, description="Latest claim date (inclusive)")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum paid amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum paid amount")
    
    @validator('max_date')
    def validate_dates(cls, v, values):
        if 'min_date' in values and v and values['min_date'] and v < values['min_date']:
            raise ValueError("max_date cannot be before min_date")
        return v
    
    @validator('max_amount')
    def validate_amounts(cls, v, values):
        if 'min_amount' in values and v is not None and values['min_amount'] is not None and v < values['min_amount']:
            raise ValueError("max_amount cannot be less than min_amount")
        return v
