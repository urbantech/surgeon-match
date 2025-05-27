import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from .core.config import settings
from .core.database import init_db, close_db
from .api.middleware import add_middleware
from .api.endpoints.api_keys import router as api_keys_router
from .api.endpoints.surgeons import router as surgeons_router
from .api.endpoints.claims import router as claims_router
from .api.endpoints.quality_metrics import router as quality_metrics_router
from .api.endpoints.test import router as test_router
from .schemas.error import ErrorCodes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Starting up...")
    await init_db()
    
    yield  # The application runs here
    
    # Shutdown: Clean up resources
    logger.info("Shutting down...")
    await close_db()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="SurgeonMatch API - Match surgeons with real-time surgery needs for Medicare patients",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
add_middleware(app)

# Common error responses
common_responses = {
    "401": {"description": "Unauthorized"},
    "403": {"description": "Forbidden"}
}

# Include API routers
app.include_router(
    api_keys_router,
    prefix=f"{settings.API_PREFIX}/api-keys",
    tags=["API Keys"],
    responses=common_responses,
)

app.include_router(
    surgeons_router,
    prefix=f"{settings.API_PREFIX}/surgeons",
    tags=["Surgeons"],
    responses=common_responses,
)

app.include_router(
    claims_router,
    prefix=f"{settings.API_PREFIX}/claims",
    tags=["Claims"],
    responses=common_responses,
)

app.include_router(
    quality_metrics_router,
    prefix=f"{settings.API_PREFIX}/quality-metrics",
    tags=["Quality Metrics"],
    responses=common_responses,
)

app.include_router(
    test_router,
    prefix=f"{settings.API_PREFIX}",
    tags=["Test"],
    responses=common_responses,
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": ErrorCodes.VALIDATION_ERROR[0],
                "message": ErrorCodes.VALIDATION_ERROR[1],
                "details": errors
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": getattr(exc, "code", "http_error"),
                "message": exc.detail,
                "detail": getattr(exc, "detail", None)
            }
        }
    )

# Health check endpoints
@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API is running and healthy.",
    tags=["System"]
)
@app.get(
    f"{settings.API_PREFIX}/health",
    status_code=status.HTTP_200_OK,
    summary="Health check (with API prefix)",
    description="Check if the API is running and healthy.",
    tags=["System"]
)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns a simple status message indicating the API is running.
    """
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        SurgeonMatch API - Match surgeons with real-time surgery needs for Medicare patients.
        
        ## Authentication
        This API uses API keys for authentication. To use the API, include your API key in the `X-API-Key` header.
        
        Example:
        ```
        X-API-Key: your-api-key-here
        ```
        
        ## Rate Limiting
        The API is rate limited to 100 requests per minute per API key.
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication"
        }
    }
    
    # Add security requirements to all operations
    for path in openapi_schema["paths"].values():
        for method in path.values():
            # Skip the health check endpoint
            if method.get("summary") == "Health check":
                continue
                
            # Add security requirement
            method["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Set the custom OpenAPI schema
app.openapi = custom_openapi

# Root endpoint
@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def root():
    """Root endpoint that redirects to the API documentation."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "API documentation is not available in production"
    }
