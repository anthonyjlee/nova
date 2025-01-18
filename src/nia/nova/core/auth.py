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

# Test API keys with metadata
TEST_API_KEYS = {
    "valid-test-key": {
        "type": "test",
        "expires": None,  # Never expires
        "permissions": ["read", "write", "admin"]
    },
    "test-key": {
        "type": "test",
        "expires": None,  # Never expires
        "permissions": ["read", "write"]
    },
    "expired-key": {
        "type": "test",
        "expires": datetime(2024, 1, 1),  # Already expired
        "permissions": ["read"]
    }
}

# Production keys would be loaded from environment/config
API_KEYS = list(TEST_API_KEYS.keys())

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

def _normalize_and_validate_key(api_key: str) -> tuple[str, str]:
    """
    Normalize and validate an API key, returning both normalized and original keys.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        tuple[str, str]: A tuple of (normalized_key, original_key)
        
    Raises:
        HTTPException: If the key is invalid or expired
    """
    logger.debug(f"Normalizing and validating key: {api_key}")
    if not api_key:
        logger.error("API key is missing")
        raise HTTPException(
            status_code=401,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Normalize key
    normalized_key = str(api_key).strip()
    logger.debug(f"Normalized key: {normalized_key}")
    valid_keys = {str(k).strip(): k for k in TEST_API_KEYS}
    logger.debug(f"Valid keys: {valid_keys}")
    
    if normalized_key not in valid_keys:
        logger.error(f"Invalid API key: {normalized_key}")
        logger.debug(f"Available keys: {list(valid_keys.keys())}")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Get original key for lookup
    original_key = valid_keys[normalized_key]
    
    # Check expiration
    key_info = TEST_API_KEYS[original_key]
    if key_info["expires"] and datetime.now() > key_info["expires"]:
        raise HTTPException(
            status_code=403,
            detail="Token expired",
            headers={"WWW-Authenticate": "ApiKey"},
        )
        
    return normalized_key, original_key

def validate_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """Validate the API key."""
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    normalized_key, _ = _normalize_and_validate_key(api_key)
    return normalized_key

def get_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Get the API key for dependency injection."""
    return validate_api_key(api_key)

def get_api_key_dependency():
    """Get the API key dependency."""
    return Depends(get_api_key)

def ws_auth(api_key: str) -> str:
    """Authenticate WebSocket connection."""
    logger.debug(f"Validating API key: {api_key}")
    logger.debug(f"Valid API keys: {API_KEYS}")
    logger.debug(f"TEST_API_KEYS: {TEST_API_KEYS}")
    logger.debug(f"API key type: {type(api_key)}")
    logger.debug(f"TEST_API_KEYS key types: {[(k, type(k)) for k in TEST_API_KEYS.keys()]}")
    
    normalized_key, _ = _normalize_and_validate_key(api_key)
    return normalized_key

def get_key_permissions(api_key: str) -> list[str]:
    """Get permissions for an API key."""
    _, original_key = _normalize_and_validate_key(api_key)
    return TEST_API_KEYS[original_key]["permissions"]

def check_rate_limit(api_key: str = Depends(get_api_key)) -> None:
    """Check rate limiting."""
    _, original_key = _normalize_and_validate_key(api_key)
    
    now = int(time.time())
    window_start = now - RATE_LIMIT_WINDOW
    
    # Initialize or clean up rate limit store
    if original_key not in rate_limit_store:
        rate_limit_store[original_key] = {}
    rate_limit_store[original_key] = {
        ts: count for ts, count in rate_limit_store[original_key].items()
        if int(ts) > window_start
    }
    
    # Count requests in current window
    current_requests = sum(rate_limit_store[original_key].values())
    
    if current_requests >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )
    
    # Record request
    timestamp = str(now)
    if timestamp in rate_limit_store[original_key]:
        rate_limit_store[original_key][timestamp] += 1
    else:
        rate_limit_store[original_key][timestamp] = 1

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
            
        # Get key permissions using normalized key lookup
        _, original_key = _normalize_and_validate_key(api_key)
        key_permissions = TEST_API_KEYS[original_key]["permissions"]
        required_permissions = PERMISSIONS[required_permission]
        
        # Check if key has all required permissions
        if not all(perm in key_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
            
    return check_permission

def check_domain_access(domain: str):
    """Check domain access permission."""
    def check_access(api_key: str = Depends(get_api_key)) -> None:
        # Get key permissions using normalized key lookup
        _, original_key = _normalize_and_validate_key(api_key)
        key_permissions = TEST_API_KEYS[original_key]["permissions"]
        
        # For testing, keys with admin permission have access to all domains
        if "admin" in key_permissions:
            return None
            
        # In production, would check domain access from a database
        return None
            
    return check_access
