from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db
from ...core.security import get_current_user

router = APIRouter(prefix="/test", tags=["Test"])

@router.get("/rate-limit")
async def test_rate_limit(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint for rate limiting.
    This endpoint requires authentication and is subject to rate limiting.
    """
    # In a real-world scenario, we'd process the request here
    # For testing, we'll just return helpful information
    
    # The rate limit headers aren't available in the request yet
    # They're added to the response after this function returns
    # For testing, we'll use the test API key values
    from ...core.config import settings
    
    # Check if we're using the test API key
    using_test_key = False
    if settings.DEBUG and hasattr(settings, 'TEST_API_KEY'):
        using_test_key = request.headers.get("x-api-key") == settings.TEST_API_KEY
    
    return {
        "message": "Rate limit test successful",
        "user": current_user,
        "api_key": {
            "id": current_user.get("api_key_id"),
            "name": current_user.get("name"),
            "is_test_key": using_test_key
        },
        "expected_rate_limit_headers": {
            "limit": 5 if using_test_key else settings.DEFAULT_RATE_LIMIT,
            "remaining": 4 if using_test_key else "varies",
            "reset": 60 if using_test_key else settings.DEFAULT_RATE_LIMIT_PERIOD
        },
        "request_info": {
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers),
        }
    }
