"""Authentication and authorization for Nova's FastAPI server."""

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from typing import Optional, Dict
import time
from datetime import datetime, timedelta

# API Key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting settings
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS = 100  # requests per window

# In-memory storage for rate limiting
# {api_key: [(timestamp, endpoint), ...]}
request_history: Dict[str, list] = {}

# In-memory API key storage (replace with database in production)
API_KEYS = {
    "test-key": {
        "client": "test",
        "permissions": ["read", "write"],
        "domains": ["professional"]
    }
}

def get_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Validate API key."""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
        
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
        
    return api_key

def check_rate_limit(
    api_key: str = Depends(get_api_key),
    endpoint: Optional[str] = None
) -> None:
    """Check rate limiting for API key."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Initialize or clean old requests
    if api_key not in request_history:
        request_history[api_key] = []
    else:
        request_history[api_key] = [
            (ts, ep) for ts, ep in request_history[api_key]
            if ts > window_start
        ]
    
    # Check rate limit
    if len(request_history[api_key]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
        
    # Record request
    request_history[api_key].append((now, endpoint))

def check_domain_access(
    domain: str,
    api_key: str = Depends(get_api_key)
) -> None:
    """Check if API key has access to domain."""
    allowed_domains = API_KEYS[api_key]["domains"]
    if domain not in allowed_domains:
        raise HTTPException(
            status_code=403,
            detail=f"Access to domain '{domain}' not allowed"
        )

def get_permission(permission: str):
    """Create a permission check dependency."""
    def check_permission(api_key: str = Depends(get_api_key)) -> None:
        """Check if API key has required permission."""
        permissions = API_KEYS[api_key]["permissions"]
        if permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
    return check_permission
    """Check if API key has required permission."""
    permissions = API_KEYS[api_key]["permissions"]
    if permission not in permissions:
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{permission}' required"
        )
