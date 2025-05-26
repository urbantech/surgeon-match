from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from http import HTTPStatus

class ErrorDetail(BaseModel):
    """Schema for error details."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[Union[str, Dict[str, Any], List[Any]]] = Field(
        None, 
        description="Additional error details"
    )

class HTTPError(BaseModel):
    """Base schema for HTTP error responses."""
    error: ErrorDetail = Field(..., description="Error details")

# Common error responses
def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    detail: Optional[Union[str, Dict[str, Any], List[Any]]] = None
) -> Dict[str, Any]:
    """Helper function to create a standardized error response."""
    return {
        "error": {
            "code": error_code,
            "message": message,
            "detail": detail
        }
    }

# Common error responses
class ErrorResponses:
    """Common error responses for the API."""
    
    @staticmethod
    def not_found(resource: str = "Resource") -> Dict[int, Dict[str, Any]]:
        """404 Not Found error."""
        return {
            "model": HTTPError,
            "description": f"{resource} not found",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.NOT_FOUND,
                        error_code="not_found",
                        message=f"{resource} not found"
                    )
                }
            }
        }
    
    @staticmethod
    def unauthorized(message: str = "Not authenticated") -> Dict[int, Dict[str, Any]]:
        """401 Unauthorized error."""
        return {
            "model": HTTPError,
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.UNAUTHORIZED,
                        error_code="unauthorized",
                        message=message
                    )
                }
            }
        }
    
    @staticmethod
    def forbidden(message: str = "Not authorized") -> Dict[int, Dict[str, Any]]:
        """403 Forbidden error."""
        return {
            "model": HTTPError,
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.FORBIDDEN,
                        error_code="forbidden",
                        message=message
                    )
                }
            }
        }
    
    @staticmethod
    def bad_request(message: str = "Invalid request") -> Dict[int, Dict[str, Any]]:
        """400 Bad Request error."""
        return {
            "model": HTTPError,
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.BAD_REQUEST,
                        error_code="bad_request",
                        message=message
                    )
                }
            }
        }
    
    @staticmethod
    def conflict(message: str = "Resource already exists") -> Dict[int, Dict[str, Any]]:
        """409 Conflict error."""
        return {
            "model": HTTPError,
            "description": "Resource conflict",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.CONFLICT,
                        error_code="conflict",
                        message=message
                    )
                }
            }
        }
    
    @staticmethod
    def rate_limit_exceeded(retry_after: int = 60) -> Dict[int, Dict[str, Any]]:
        """429 Too Many Requests error."""
        return {
            "model": HTTPError,
            "description": "Rate limit exceeded",
            "headers": {
                "Retry-After": str(retry_after)
            },
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.TOO_MANY_REQUESTS,
                        error_code="rate_limit_exceeded",
                        message="Rate limit exceeded",
                        detail={
                            "retry_after_seconds": retry_after,
                            "limit": 100,
                            "period_seconds": 60
                        }
                    )
                }
            }
        }
    
    @staticmethod
    def internal_server_error() -> Dict[int, Dict[str, Any]]:
        """500 Internal Server Error."""
        return {
            "model": HTTPError,
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        error_code="internal_server_error",
                        message="An unexpected error occurred"
                    )
                }
            }
        }

# Common error codes and messages
class ErrorCodes:
    """Common error codes and messages."""
    # API Key errors
    API_KEY_MISSING = ("api_key_missing", "API key is missing")
    API_KEY_INVALID = ("api_key_invalid", "Invalid API key")
    API_KEY_EXPIRED = ("api_key_expired", "API key has expired")
    API_KEY_INSUFFICIENT_PERMISSIONS = ("api_key_insufficient_permissions", "Insufficient permissions")
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = ("rate_limit_exceeded", "Rate limit exceeded")
    
    # Validation errors
    VALIDATION_ERROR = ("validation_error", "Validation error")
    INVALID_INPUT = ("invalid_input", "Invalid input data")
    
    # Resource errors
    RESOURCE_NOT_FOUND = ("not_found", "Resource not found")
    RESOURCE_EXISTS = ("resource_exists", "Resource already exists")
    
    # Authentication/Authorization
    AUTH_REQUIRED = ("authentication_required", "Authentication required")
    INVALID_CREDENTIALS = ("invalid_credentials", "Invalid credentials")
    TOKEN_EXPIRED = ("token_expired", "Token has expired")
    TOKEN_INVALID = ("token_invalid", "Invalid token")
    
    # Server errors
    INTERNAL_ERROR = ("internal_error", "Internal server error")
    SERVICE_UNAVAILABLE = ("service_unavailable", "Service temporarily unavailable")
