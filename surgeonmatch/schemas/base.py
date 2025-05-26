from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID as PyUUID

class BaseSchema(BaseModel):
    """Base schema with common configurations."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            PyUUID: lambda v: str(v) if v else None
        }
        populate_by_name = True
        
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to handle custom JSON encoders."""
        return super().model_dump(**kwargs)
