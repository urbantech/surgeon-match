from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import (
    generate_api_key,
    create_access_token,
    get_current_user,
    APIKeyHeader
)
from ...dependencies import get_db
from ...models.api_key import APIKey, APIKeyUsageLog
from ...schemas.api_key import (
    APIKeyCreate,
    APIKeyInDB,
    APIKeyResponse,
    APIKeyWithToken,
    APIKeyUpdate,
    APIKeyUsageLog as APIKeyUsageLogSchema,
    APIKeyDetail
)
from ...schemas.error import ErrorResponses, ErrorCodes

router = APIRouter()

@router.post(
    "/api-keys",
    response_model=APIKeyWithToken,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    description="Generate a new API key with the specified name and expiration.",
    responses={
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"}
    }
)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key.
    
    - **name**: A descriptive name for the API key
    - **expires_in_days**: Number of days until the key expires (optional)
    """
    # Generate API key and hash
    key, hashed_key = generate_api_key()
    
    # Calculate expiration date if provided
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        name=key_data.name,
        key=hashed_key,
        expires_at=expires_at,
        created_by=current_user.get("api_key_id")  # Track who created this key
    )
    
    # Save to database
    await db.execute(
        """
        INSERT INTO api_keys 
        (id, name, key, expires_at, created_by, created_at, updated_at, is_active)
        VALUES 
        (:id, :name, :key, :expires_at, :created_by, :created_at, :updated_at, :is_active)
        """,
        {
            "id": api_key.id,
            "name": api_key.name,
            "key": api_key.key,
            "expires_at": api_key.expires_at,
            "created_by": api_key.created_by,
            "created_at": api_key.created_at,
            "updated_at": api_key.updated_at,
            "is_active": api_key.is_active
        }
    )
    await db.commit()
    
    # Return the key with the actual token (only shown once)
    return APIKeyWithToken(
        **api_key.dict(exclude={"key"}),
        key=key  # Include the actual key (only time it will be shown)
    )

@router.get(
    "/api-keys",
    response_model=List[APIKeyResponse],
    summary="List API keys",
    description="List all API keys for the current user.",
    responses={
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"}
    }
)
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys for the current user.
    """
    # Only show keys created by the current user
    result = await db.execute(
        """
        SELECT * FROM api_keys 
        WHERE created_by = :created_by
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
        """,
        {"created_by": current_user["api_key_id"], "limit": limit, "skip": skip}
    )
    
    api_keys = result.fetchall()
    return [APIKeyResponse(**dict(key)) for key in api_keys]

@router.get(
    "/api-keys/{key_id}",
    response_model=APIKeyDetail,
    summary="Get API key details",
    description="Get detailed information about a specific API key, including usage logs.",
    responses={
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"},
        "404": {"description": "API key not found"}
    }
        **ErrorResponses.unauthorized(),
        **ErrorResponses.forbidden(),
        **ErrorResponses.not_found("API key")
    }
)
async def get_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific API key.
    """
    # Get API key
    result = await db.execute(
        """
        SELECT * FROM api_keys 
        WHERE id = :key_id AND created_by = :created_by
        """,
        {"key_id": key_id, "created_by": current_user["api_key_id"]}
    )
    
    api_key = result.first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Get usage logs
    result = await db.execute(
        """
        SELECT * FROM api_key_usage_logs 
        WHERE api_key_id = :key_id
        ORDER BY created_at DESC
        LIMIT 100
        """,
        {"key_id": key_id}
    )
    
    usage_logs = result.fetchall()
    
    return APIKeyDetail(
        **dict(api_key),
        usage_logs=[APIKeyUsageLogSchema(**dict(log)) for log in usage_logs]
    )

@router.put(
    "/api-keys/{key_id}",
    response_model=APIKeyInDB,
    summary="Update API key",
    description="Update an existing API key's name or active status.",
    responses={
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"},
        "404": {"description": "API key not found"}
    }
        **ErrorResponses.unauthorized(),
        **ErrorResponses.forbidden(),
        **ErrorResponses.not_found("API key")
    }
)
async def update_api_key(
    key_id: str,
    key_data: APIKeyUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing API key.
    
    - **name**: New name for the API key
    - **is_active**: Whether the key is active
    """
    # Get the API key
    result = await db.execute(
        """
        SELECT * FROM api_keys 
        WHERE id = :key_id AND created_by = :created_by
        """,
        {"key_id": key_id, "created_by": current_user["api_key_id"]}
    )
    
    api_key = result.first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update fields
    update_data = key_data.dict(exclude_unset=True)
    
    # Convert to dict for easier manipulation
    api_key_dict = dict(api_key)
    
    # Update only the fields that were provided
    for field, value in update_data.items():
        if field in api_key_dict:
            api_key_dict[field] = value
    
    # Update in database
    await db.execute(
        """
        UPDATE api_keys 
        SET name = :name, is_active = :is_active, updated_at = NOW()
        WHERE id = :id
        """,
        {
            "id": key_id,
            "name": api_key_dict["name"],
            "is_active": api_key_dict["is_active"]
        }
    )
    await db.commit()
    
    # Get the updated record
    result = await db.execute(
        "SELECT * FROM api_keys WHERE id = :key_id",
        {"key_id": key_id}
    )
    
    updated_key = result.first()
    return APIKeyInDB(**dict(updated_key))

@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API key",
    description="Delete an existing API key. This action cannot be undone.",
    responses={
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"},
        "404": {"description": "API key not found"}
    }
        **ErrorResponses.unauthorized(),
        **ErrorResponses.forbidden(),
        **ErrorResponses.not_found("API key")
    }
)
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an API key.
    """
    # Verify the key exists and belongs to the current user
    result = await db.execute(
        """
        SELECT id FROM api_keys 
        WHERE id = :key_id AND created_by = :created_by
        """,
        {"key_id": key_id, "created_by": current_user["api_key_id"]}
    )
    
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Delete the key
    await db.execute(
        "DELETE FROM api_keys WHERE id = :key_id",
        {"key_id": key_id}
    )
    await db.commit()
    
    return None
