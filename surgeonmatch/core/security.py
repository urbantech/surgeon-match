import secrets
import string
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from fastapi import HTTPException, status, Request, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from ..core.config import settings
from ..models.api_key import APIKey, APIKeyUsageLog
from ..schemas.error import ErrorCodes
from ..dependencies import get_db

# API Key Security
api_key_header = APIKeyHeader(
    name=settings.API_KEY_HEADER,
    auto_error=False,
    description="API key for authentication"
)

# JWT Settings
ALGORITHM = "HS256"

def generate_api_key(length: int = 32) -> Tuple[str, str]:
    """
    Generate a new API key and its hash for storage.
    
    Returns:
        Tuple of (key, hashed_key)
    """
    # Generate a random string for the API key
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Generate a hash of the key for storage
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    
    return key, hashed_key

async def verify_api_key(
    api_key: str,
    db: AsyncSession
) -> Tuple[bool, Optional[APIKey], Optional[str]]:
    """
    Verify an API key and return the associated API key record if valid.
    
    Args:
        api_key: The API key to verify
        db: Database session
        
    Returns:
        Tuple of (is_valid, api_key_record, error_message)
    """
    if not api_key:
        return False, None, "API key is required"
    
    # Hash the provided API key for comparison with stored hash
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Query the database for the API key
    result = await db.execute(
        """
        SELECT * FROM api_keys 
        WHERE key = :hashed_key AND is_active = TRUE
        """,
        {"hashed_key": hashed_key}
    )
    api_key_record = result.first()
    
    if not api_key_record:
        return False, None, "Invalid API key"
    
    api_key_record = APIKey(**dict(api_key_record))
    
    # Check if the key has expired
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        return False, None, "API key has expired"
    
    # Update last used timestamp
    api_key_record.last_used_at = datetime.utcnow()
    await db.execute(
        """
        UPDATE api_keys 
        SET last_used_at = :last_used_at 
        WHERE id = :id
        """,
        {"last_used_at": api_key_record.last_used_at, "id": api_key_record.id}
    )
    await db.commit()
    
    return True, api_key_record, None

async def log_api_key_usage(
    api_key_id: str,
    request: Request,
    status_code: int,
    db: AsyncSession
) -> None:
    """
    Log API key usage for analytics and monitoring.
    
    Args:
        api_key_id: ID of the API key being used
        request: The incoming request
        status_code: HTTP status code of the response
        db: Database session
    """
    # Get client IP address
    client_ip = request.client.host if request.client else None
    
    # Get user agent
    user_agent = request.headers.get("user-agent")
    
    # Log the usage
    log = APIKeyUsageLog(
        api_key_id=api_key_id,
        endpoint=request.url.path,
        method=request.method,
        status_code=str(status_code),
        client_ip=client_ip,
        user_agent=user_agent
    )
    
    # Save to database
    await db.execute(
        """
        INSERT INTO api_key_usage_logs 
        (id, api_key_id, endpoint, method, status_code, client_ip, user_agent, created_at)
        VALUES 
        (:id, :api_key_id, :endpoint, :method, :status_code, :client_ip, :user_agent, :created_at)
        """,
        {
            "id": log.id,
            "api_key_id": log.api_key_id,
            "endpoint": log.endpoint,
            "method": log.method,
            "status_code": log.status_code,
            "client_ip": log.client_ip,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
    )
    await db.commit()

# Rate Limiting
async def check_rate_limit(
    api_key: str,
    endpoint: str,
    db: AsyncSession
) -> Tuple[bool, int, int]:
    """
    Check if the rate limit has been exceeded for the given API key and endpoint.
    
    Args:
        api_key: The API key to check
        endpoint: The endpoint being accessed
        db: Database session
        
    Returns:
        Tuple of (is_allowed, remaining, reset_in_seconds)
    """
    # Generate a unique key for this rate limit window
    period = settings.RATE_LIMIT_PERIOD
    time_window = (datetime.utcnow().timestamp() // period) * period
    key = f"{api_key}:{endpoint}:{time_window}"
    
    # Check if we have a record of this key in the current window
    result = await db.execute(
        """
        SELECT * FROM rate_limits 
        WHERE key = :key AND expires_at > NOW()
        """,
        {"key": key}
    )
    rate_limit = result.first()
    
    if rate_limit:
        rate_limit = dict(rate_limit)
        # Check if we've exceeded the limit
        if rate_limit["count"] >= settings.RATE_LIMIT:
            # Calculate when the current window resets
            reset_time = rate_limit["expires_at"]
            reset_in = int((reset_time - datetime.utcnow()).total_seconds())
            return False, 0, reset_in
        
        # Increment the counter
        await db.execute(
            """
            UPDATE rate_limits 
            SET count = count + 1 
            WHERE id = :id
            """,
            {"id": rate_limit["id"]}
        )
        remaining = settings.RATE_LIMIT - (rate_limit["count"] + 1)
    else:
        # Create a new rate limit record
        expires_at = datetime.utcnow() + timedelta(seconds=period)
        await db.execute(
            """
            INSERT INTO rate_limits 
            (id, key, count, period, expires_at, created_at, updated_at, is_active)
            VALUES 
            (:id, :key, 1, :period, :expires_at, NOW(), NOW(), TRUE)
            """,
            {
                "id": str(uuid.uuid4()),
                "key": key,
                "period": period,
                "expires_at": expires_at
            }
        )
        remaining = settings.RATE_LIMIT - 1
    
    await db.commit()
    return True, remaining, period

# JWT Authentication
def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to include in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=ALGORITHM
    )

async def get_current_user(
    token: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        db: Database session
        
    Returns:
        User information from the token
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        api_key_id: str = payload.get("sub")
        if api_key_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Verify the API key still exists and is valid
    is_valid, api_key, error = await verify_api_key(api_key_id, db)
    if not is_valid or not api_key:
        raise credentials_exception
    
    return {"api_key_id": str(api_key.id), "name": api_key.name}
