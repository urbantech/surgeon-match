from typing import List, Optional, Dict, Any, Literal
from pydantic import Field, validator, condecimal
from datetime import date, datetime
from .base import BaseSchema

class QualityMetricBase(BaseSchema):
    """Base schema for quality metrics."""
    surgeon_id: str = Field(..., description="ID of the surgeon")
    metric_name: str = Field(..., max_length=100, description="Name of the quality metric")
    metric_value: float = Field(..., description="Numeric value of the metric")
    metric_unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    
    # Time period for the metric
    start_date: date = Field(..., description="Start date of the measurement period")
    end_date: date = Field(..., description="End date of the measurement period")
    
    # Additional metadata
    procedure_code: Optional[str] = Field(None, max_length=10, description="Procedure code if metric is procedure-specific")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional metric details")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v and values['start_date'] and v < values['start_date']:
            raise ValueError("end_date cannot be before start_date")
        return v

class QualityMetricCreate(QualityMetricBase):
    """Schema for creating a new quality metric."""
    pass

class QualityMetricUpdate(BaseSchema):
    """Schema for updating an existing quality metric."""
    metric_value: Optional[float] = Field(None, description="Numeric value of the metric")
    metric_unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    start_date: Optional[date] = Field(None, description="Start date of the measurement period")
    end_date: Optional[date] = Field(None, description="End date of the measurement period")
    procedure_code: Optional[str] = Field(None, max_length=10, description="Procedure code if metric is procedure-specific")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional metric details")

class QualityMetricInDB(QualityMetricBase):
    """Schema for quality metric data stored in the database."""
    id: str
    calculated_at: datetime
    
    class Config:
        from_attributes = True

class QualityMetricResponse(QualityMetricInDB):
    """Schema for quality metric API response."""
    metric_display_name: Optional[str] = Field(None, description="Human-readable display name for the metric")
    
    @validator('metric_display_name', pre=True, always=True)
    def set_display_name(cls, v, values):
        if v is None and 'metric_name' in values:
            # Simple conversion from snake_case to Title Case
            return values['metric_name'].replace('_', ' ').title()
        return v

class QualityMetricListResponse(BaseSchema):
    """Schema for paginated list of quality metrics."""
    items: List[QualityMetricResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")
    total_pages: int = Field(0, description="Total number of pages")

class QualityMetricSearchFilters(BaseSchema):
    """Schema for quality metric search filters."""
    surgeon_id: Optional[str] = Field(None, description="Filter by surgeon ID")
    metric_name: Optional[str] = Field(None, description="Filter by metric name")
    procedure_code: Optional[str] = Field(None, description="Filter by procedure code")
    min_value: Optional[float] = Field(None, description="Minimum metric value")
    max_value: Optional[float] = Field(None, description="Maximum metric value")
    start_date: Optional[date] = Field(None, description="Filter by start date (inclusive)")
    end_date: Optional[date] = Field(None, description="Filter by end date (inclusive)")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v and values['start_date'] and v < values['start_date']:
            raise ValueError("end_date cannot be before start_date")
        return v

class QualityMetricSummary(BaseSchema):
    """Schema for quality metric summary statistics."""
    metric_name: str
    average_value: float
    min_value: float
    max_value: float
    count: int
    last_updated: datetime

class SurgeonQualityProfile(BaseSchema):
    """Schema for a surgeon's quality profile."""
    surgeon_id: str
    surgeon_name: str
    metrics: List[QualityMetricResponse] = Field(default_factory=list)
    overall_score: Optional[float] = Field(None, description="Composite quality score (0-100)")
    percentile_rank: Optional[float] = Field(None, description="Percentile rank compared to peers (0-100)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
