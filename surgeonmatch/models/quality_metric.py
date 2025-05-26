from sqlalchemy import Column, String, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from .base import Base

class QualityMetric(Base):
    """Quality metrics for surgeons based on claims data."""
    __tablename__ = "quality_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    surgeon_id = Column(UUID(as_uuid=True), ForeignKey("surgeons.id"), nullable=False, index=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    
    # Time period for the metric
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Additional metadata
    procedure_code = Column(String(10), nullable=True, index=True, 
                          comment="If metric is specific to a procedure")
    details = Column(JSONB, nullable=True, comment="Additional metric details")
    
    # Timestamps
    calculated_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    surgeon = relationship("Surgeon", back_populates="quality_metrics")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_quality_metric_surgeon_metric', 'surgeon_id', 'metric_name'),
        Index('idx_quality_metric_date_range', 'start_date', 'end_date'),
        Index('idx_quality_metric_procedure', 'procedure_code'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quality metric object to dictionary."""
        return {
            "id": str(self.id),
            "surgeon_id": str(self.surgeon_id),
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "procedure_code": self.procedure_code,
            "details": self.details,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }
    
    @classmethod
    def get_metric_display_name(cls, metric_name: str) -> str:
        """Get a human-readable display name for a metric."""
        display_names = {
            "readmission_rate": "30-Day Readmission Rate",
            "complication_rate": "Complication Rate",
            "mortality_rate": "Mortality Rate",
            "length_of_stay": "Average Length of Stay (days)",
            "patient_satisfaction": "Patient Satisfaction Score",
            "surgical_site_infection": "Surgical Site Infection Rate",
            "emergency_room_visits": "30-Day Emergency Room Visits",
        }
        return display_names.get(metric_name, metric_name.replace("_", " ").title())
    
    @classmethod
    def get_metric_unit(cls, metric_name: str) -> str:
        """Get the appropriate unit for a metric."""
        units = {
            "readmission_rate": "%",
            "complication_rate": "%",
            "mortality_rate": "%",
            "length_of_stay": "days",
            "patient_satisfaction": "out of 5",
            "surgical_site_infection": "%",
            "emergency_room_visits": "count",
        }
        return units.get(metric_name, "")
