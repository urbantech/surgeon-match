from .api_keys import router as api_keys_router
from .surgeons import router as surgeons_router
from .claims import router as claims_router
from .quality_metrics import router as quality_metrics_router

# Export routers for use in main.py
router = api_keys_router
surgeons = surgeons_router
claims = claims_router
quality_metrics = quality_metrics_router

__all__ = ["router", "surgeons", "claims", "quality_metrics"]
