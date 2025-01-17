"""Authentication utilities for Nova API."""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyQuery

# API key query parameter
api_key_query = APIKeyQuery(name="key", auto_error=False)

def validate_api_key(key: str = Security(api_key_query)) -> str:
    """Validate API key."""
    # For development, accept 'development' as API key
    if key == "development":
        return key
        
    raise HTTPException(
        status_code=403,
        detail="Invalid API key"
    )
