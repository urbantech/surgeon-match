from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from .base import Base

class Surgeon(Base):
    """Surgeon model representing a healthcare provider."""
    __tablename__ = "surgeons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npi = Column(String(10), unique=True, index=True, nullable=False, comment="National Provider Identifier")
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    specialty_code = Column(String(10), nullable=False, index=True)
    specialty_description = Column(String(255), nullable=True)
    
    # Location information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True, index=True)
    zip_code = Column(String(10), nullable=True, index=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    
    # Practice information
    accepts_medicare = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Statistics (pre-calculated for performance)
    total_claims = Column(Integer, default=0, nullable=False)
    average_quality_score = Column(Float, default=0.0, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="surgeon")
    quality_metrics = relationship("QualityMetric", back_populates="surgeon")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_surgeon_geo', 'latitude', 'longitude'),
        Index('idx_surgeon_specialty_medicare', 'specialty_code', 'accepts_medicare', 'is_active'),
    )
    
    @property
    def full_name(self) -> str:
        """Return the full name of the surgeon."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert surgeon object to dictionary."""
        return {
            "id": str(self.id),
            "npi": self.npi,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "specialty_code": self.specialty_code,
            "specialty_description": self.specialty_description,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "zip_code": self.zip_code,
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "accepts_medicare": self.accepts_medicare,
            "is_active": self.is_active,
            "total_claims": self.total_claims,
            "average_quality_score": self.average_quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
