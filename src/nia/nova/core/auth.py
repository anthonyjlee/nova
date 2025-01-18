"""Authentication and authorization for Nova API."""

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Set
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# API key settings
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEYS = ["valid-test-key"]  # For testing only

# Rate limiting settings
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100
rate_limit_store: Dict[str, Dict[str, int]] = {}  # api_key -> {timestamp: count}

# Permission settings
PERMISSIONS = {
    "read": {"read"},
    "write": {"read", "write"},
    "admin": {"read", "write", "admin"}
}

def validate_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """Validate the API key."""
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key

def get_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Get the API key for dependency injection."""
    return validate_api_key(api_key)

def get_api_key_dependency():
    """Get the API key dependency."""
    return Depends(get_api_key)

def get_ws_api_key(api_key: Optional[str] = None) -> str:
    """Get and validate WebSocket API key."""
    return validate_api_key(api_key)

def check_rate_limit(api_key: str = Depends(get_api_key)) -> None:
    """Check rate limiting."""
    now = int(time.time())
    window_start = now - RATE_LIMIT_WINDOW
    
    # Initialize or clean up rate limit store
    if api_key not in rate_limit_store:
        rate_limit_store[api_key] = {}
    rate_limit_store[api_key] = {
        ts: count for ts, count in rate_limit_store[api_key].items()
        if int(ts) > window_start
    }
    
    # Count requests in current window
    current_requests = sum(rate_limit_store[api_key].values())
    
    if current_requests >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )
    
    # Record request
    timestamp = str(now)
    if timestamp in rate_limit_store[api_key]:
        rate_limit_store[api_key][timestamp] += 1
    else:
        rate_limit_store[api_key][timestamp] = 1

def reset_rate_limits():
    """Reset all rate limits. Used for testing."""
    rate_limit_store.clear()

def get_permission(required_permission: str):
    """Get permission dependency."""
    def check_permission(api_key: str = Depends(get_api_key)) -> None:
        # Check if permission exists
        if required_permission not in PERMISSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid permission: {required_permission}"
            )
            
        # For testing, valid-test-key has all permissions
        if api_key == "valid-test-key":
            return None
            
        user_permissions = PERMISSIONS.get(required_permission, set())
        if not user_permissions:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
            
    return check_permission

def check_domain_access(domain: str):
    """Check domain access permission."""
    def check_access(api_key: str = Depends(get_api_key)) -> None:
        # For testing, valid-test-key has access to all domains
        if api_key == "valid-test-key":
            return None
            
        # In production, would check domain access from a database
        return None
            
    return check_access

def ws_auth(api_key: Optional[str] = None) -> str:
    """Authenticate WebSocket connection."""
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # Log the API key and valid keys for debugging
    logger.debug(f"Validating API key: {api_key}")
    logger.debug(f"Valid API keys: {API_KEYS}")
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid API key: {api_key}",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
