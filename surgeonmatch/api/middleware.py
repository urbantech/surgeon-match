import time
import logging
from typing import Dict, Any, AsyncGenerator

from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.middleware.base import RequestResponseEndpoint

from ..core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

from ..core.security import verify_api_key, log_api_key_usage, check_rate_limit
from ..dependencies import get_db
from ..schemas.error import ErrorCodes, ErrorResponses

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API keys for all incoming requests.
    
    This middleware checks for a valid API key in the request headers and verifies
    it against the database. It also handles logging API key usage for analytics.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ):
        # Skip API key check for docs, openapi.json, and health endpoint
        if request.url.path in ["/docs", "/openapi.json", "/redoc", "/", "/health"]:
            return await call_next(request)
            
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        # Get database session using async context manager
        db_gen = get_db()
        db: AsyncGenerator[Any, None] = db_gen
        try:
            # Get the session from the generator
            session = await anext(db)
            
            # Verify API key
            is_valid, api_key_record, error = await verify_api_key(api_key, session)
            
            if not is_valid or not api_key_record:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": {
                            "code": ErrorCodes.API_KEY_INVALID[0],
                            "message": error or "Invalid API key"
                        }
                    }
                )
            
            # Store API key info in request state for use in route handlers
            request.state.api_key_id = str(api_key_record.id)
            request.state.api_key_name = api_key_record.name
            
            # Process the request
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add X-Process-Time header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log the API key usage
            await log_api_key_usage(
                api_key_id=request.state.api_key_id,
                request=request,
                status_code=response.status_code,
                db=session
            )
            
            return response
            
        except HTTPException as http_exc:
            # Re-raise HTTP exceptions
            raise http_exc
        except Exception as exc:
            # Log other exceptions
            logger.error(f"Error processing request: {str(exc)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        finally:
            # Close the session
            if 'session' in locals():
                await session.close()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting for API requests.
    
    This middleware checks if the request rate has exceeded the allowed limit
    for the given API key and endpoint combination.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ):
        # Skip rate limiting for docs, openapi.json, and health endpoint
        if request.url.path in ["/docs", "/openapi.json", "/redoc", "/", "/health"]:
            return await call_next(request)
            
        # Get API key from request state (set by APIKeyMiddleware)
        api_key_id = getattr(request.state, "api_key_id", None)
        
        if not api_key_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": ErrorCodes.API_KEY_MISSING[0],
                        "message": "API key is required"
                    }
                }
            )
            
        # Get endpoint identifier (method + path)
        endpoint = f"{request.method}:{request.url.path}"
        
        # Get database session using async context manager
        db_gen = get_db()
        db: AsyncGenerator[Any, None] = db_gen
        try:
            # Get the session from the generator
            session = await anext(db)
            
            # Check rate limit
            is_allowed, remaining, reset_in = await check_rate_limit(
                api_key_id=api_key_id,
                endpoint=endpoint,
                db=session
            )
            
            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_in)
            
            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": ErrorCodes.RATE_LIMIT_EXCEEDED[0],
                            "message": "Rate limit exceeded. Please try again later.",
                            "retry_after": reset_in
                        }
                    },
                    headers={
                        "Retry-After": str(reset_in),
                        "X-RateLimit-Limit": str(settings.RATE_LIMIT),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_in)
                    }
                )
                
            return response
            
        except HTTPException as http_exc:
            # Re-raise HTTP exceptions
            raise http_exc
        except Exception as exc:
            # Log other exceptions
            logger.error(f"Error in RateLimitMiddleware: {str(exc)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        finally:
            # Close the session
            if 'session' in locals():
                await session.close()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ):
        # Log request
        print(f"Request: {request.method} {request.url}")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        print(f"Response: {response.status_code} (took {process_time:.2f}s)")
        
        return response

# Helper function to add all middleware
def add_middleware(app: ASGIApp):
    """Add all middleware to the FastAPI application."""
    # Note: The order matters - middlewares are called in reverse order of addition
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIKeyMiddleware)
    
    return app
