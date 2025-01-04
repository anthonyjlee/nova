"""Authentication and authorization for Nova's FastAPI server."""

from fastapi import HTTPException, Security, Depends, Request, WebSocket
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from typing import Dict, Optional, Union, List, Tuple
import time

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory storage for API keys and their permissions
# In production, this should be replaced with a database
API_KEYS: Dict[str, Dict] = {
    "test-key": {
        "permissions": ["read", "write"],
        "rate_limit": {
            "requests": 100,
            "window": 60  # seconds
        }
    }
}

# In-memory storage for rate limiting
# In production, this should be replaced with Redis or similar
RATE_LIMITS: Dict[str, Dict] = {}

def reset_rate_limits():
    """Reset all rate limits. Used for testing."""
    RATE_LIMITS.clear()

async def get_api_key(api_key_header: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """Dependency for getting API key from request."""
    if not api_key_header:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "AUTHENTICATION_ERROR",
                "message": "API key is required"
            }
        )
    
    if api_key_header not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "AUTHENTICATION_ERROR",
                "message": "Invalid API key"
            }
        )
    
    return api_key_header

from typing import Any

async def validate_request_format(request: Any) -> None:
    """Validate request format."""
    if not isinstance(request, dict):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Invalid request format"
            }
        )

def get_api_key_dependency():
    """Get API key dependency that includes request."""
    async def dependency(request: Request, api_key: str = Depends(API_KEY_HEADER)):
        if not api_key:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTHENTICATION_ERROR",
                    "message": "API key is required"
                }
            )
        
        if api_key not in API_KEYS:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTHENTICATION_ERROR",
                    "message": "Invalid API key"
                }
            )
        
        return api_key
    return dependency

def extract_api_key_from_headers(headers: List[Tuple[bytes, bytes]]) -> Optional[str]:
    """Extract API key from raw headers."""
    for key, value in headers:
        if key.decode().lower() == "x-api-key":
            return value.decode()
    return None

async def get_ws_api_key(websocket: WebSocket) -> str:
    """Get API key from WebSocket headers."""
    # Extract API key from headers
    headers = dict(websocket.headers)
    api_key = headers.get("x-api-key")
    
    if not api_key:
        await websocket.close(code=4000, reason="API key is required")
        return None
    
    if api_key not in API_KEYS:
        await websocket.close(code=4000, reason="Invalid API key")
        return None
    
    # Check rate limit for WebSocket connections
    now = time.time()
    rate_limit = API_KEYS[api_key]["rate_limit"]
    window = rate_limit["window"]
    max_requests = rate_limit["requests"]
    
    # Initialize or clean up rate limit tracking
    if api_key not in RATE_LIMITS:
        RATE_LIMITS[api_key] = {
            "requests": [],
            "window_start": now
        }
    elif now - RATE_LIMITS[api_key]["window_start"] > window:
        # Reset window if expired
        RATE_LIMITS[api_key] = {
            "requests": [],
            "window_start": now
        }
    
    # Remove old requests outside current window
    RATE_LIMITS[api_key]["requests"] = [
        req_time for req_time in RATE_LIMITS[api_key]["requests"]
        if now - req_time <= window
    ]
    
    # Check if limit exceeded
    if len(RATE_LIMITS[api_key]["requests"]) >= max_requests:
        await websocket.close(code=4000, reason="Rate limit exceeded")
        return None
    
    # Add current request
    RATE_LIMITS[api_key]["requests"].append(now)
    
    return api_key

async def check_rate_limit(request: Request, api_key: str = Depends(get_api_key)) -> None:
    """Check if request is within rate limits."""
    now = time.time()
    rate_limit = API_KEYS[api_key]["rate_limit"]
    window = rate_limit["window"]
    max_requests = rate_limit["requests"]
    
    # Initialize or clean up rate limit tracking
    if api_key not in RATE_LIMITS:
        RATE_LIMITS[api_key] = {
            "requests": [],
            "window_start": now
        }
    
    # Remove old requests outside current window
    RATE_LIMITS[api_key]["requests"] = [
        req_time for req_time in RATE_LIMITS[api_key]["requests"]
        if now - req_time <= window
    ]
    
    # Check if limit exceeded
    current_requests = len(RATE_LIMITS[api_key]["requests"])
    if current_requests >= max_requests:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit of {max_requests} requests per {window} seconds exceeded. Current requests: {current_requests}"
            }
        )
    
    # Add current request
    RATE_LIMITS[api_key]["requests"].append(now)

def get_permission(required_permission: str):
    """Dependency to check if API key has required permission."""
    async def check_permission(api_key: str = Depends(get_api_key)) -> None:
        if not api_key:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTHENTICATION_ERROR",
                    "message": "API key is required"
                }
            )
        if required_permission not in API_KEYS[api_key]["permissions"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": f"Missing required permission: {required_permission}"
                }
            )
    return check_permission

def check_domain_access(domain: Optional[str] = None, api_key: str = Depends(get_api_key)) -> None:
    """Check if API key has access to specified domain."""
    # For now, all API keys have access to all domains
    # In production, implement domain-specific access control
    pass

# WebSocket endpoint dependencies
def get_ws_dependencies():
    """Get dependencies for WebSocket endpoint."""
    return []

def validate_api_key(api_key: str) -> bool:
    """Validate API key."""
    return api_key in API_KEYS

# Custom WebSocket dependency
async def ws_auth(websocket: Union[WebSocket, Request]) -> str:
    """Custom WebSocket authentication dependency."""
    # Extract API key from headers
    if isinstance(websocket, WebSocket):
        headers = dict(websocket.headers)
        api_key = headers.get("x-api-key")
        
        if not api_key:
            await websocket.close(code=4000, reason="API key is required")
            return None
        
        if api_key not in API_KEYS:
            await websocket.close(code=4000, reason="Invalid API key")
            return None
    else:
        # Handle Request object
        api_key = websocket.headers.get("x-api-key")
        
        if not api_key:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTHENTICATION_ERROR",
                    "message": "API key is required"
                }
            )
        
        if api_key not in API_KEYS:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "AUTHENTICATION_ERROR",
                    "message": "Invalid API key"
                }
            )
    
    return api_key
