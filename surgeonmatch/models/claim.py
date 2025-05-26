from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from .base import Base

class Claim(Base):
    """Claim model representing a medical claim."""
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(String(50), unique=True, nullable=False, index=True)
    surgeon_id = Column(UUID(as_uuid=True), ForeignKey("surgeons.id"), nullable=False, index=True)
    
    # Claim details
    patient_id = Column(String(50), nullable=False, index=True)
    procedure_code = Column(String(10), nullable=False, index=True)
    procedure_description = Column(String(255), nullable=True)
    claim_date = Column(DateTime, nullable=False, index=True)
    paid_amount = Column(Float, nullable=False)
    allowed_amount = Column(Float, nullable=False)
    
    # Additional metadata
    place_of_service = Column(String(10), nullable=True)
    diagnosis_codes = Column(JSONB, nullable=True, comment="Array of diagnosis codes")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    surgeon = relationship("Surgeon", back_populates="claims")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_claim_surgeon_date', 'surgeon_id', 'claim_date'),
        Index('idx_claim_patient', 'patient_id'),
        Index('idx_claim_procedure', 'procedure_code'),
    )
    
    def to_dict(self):
        """Convert claim object to dictionary."""
        return {
            "id": str(self.id),
            "claim_id": self.claim_id,
            "surgeon_id": str(self.surgeon_id),
            "patient_id": self.patient_id,
            "procedure_code": self.procedure_code,
            "procedure_description": self.procedure_description,
            "claim_date": self.claim_date.isoformat() if self.claim_date else None,
            "paid_amount": self.paid_amount,
            "allowed_amount": self.allowed_amount,
            "place_of_service": self.place_of_service,
            "diagnosis_codes": self.diagnosis_codes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
