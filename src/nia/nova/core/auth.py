"""Authentication and rate limiting configuration."""

from datetime import datetime, timedelta
from typing import Dict, Set
import asyncio
from urllib.parse import urlparse
from fastapi import Request, WebSocket, HTTPException

# Default development API key
API_KEYS = {'development'}

# Rate limiting configuration
RATE_LIMIT_WINDOW = timedelta(minutes=1)
RATE_LIMIT_MAX_REQUESTS = 100

# Store for rate limiting
_rate_limit_store: Dict[str, list] = {}
_rate_limit_lock = asyncio.Lock()

# Allowed domains for CORS
ALLOWED_DOMAINS = {'localhost', '127.0.0.1'}

def add_api_key(key: str) -> None:
    """Add a new API key."""
    API_KEYS.add(key)

def remove_api_key(key: str) -> None:
    """Remove an API key."""
    API_KEYS.discard(key)

def validate_api_key(key: str) -> bool:
    """Validate an API key."""
    return key in API_KEYS

async def check_rate_limit(key: str) -> bool:
    """Check if the request is within rate limits."""
    async with _rate_limit_lock:
        now = datetime.now()
        if key not in _rate_limit_store:
            _rate_limit_store[key] = []
        
        # Remove old timestamps
        _rate_limit_store[key] = [
            ts for ts in _rate_limit_store[key]
            if now - ts < RATE_LIMIT_WINDOW
        ]
        
        # Check if under limit
        if len(_rate_limit_store[key]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # Add new timestamp
        _rate_limit_store[key].append(now)
        return True

def check_domain_access(origin: str) -> bool:
    """Check if the origin domain is allowed."""
    if not origin:
        return False
    
    try:
        domain = urlparse(origin).netloc.split(':')[0]
        return domain in ALLOWED_DOMAINS
    except:
        return False

def get_api_key(request: Request) -> str:
    """Get API key from request headers."""
    api_key = request.headers.get("X-API-Key")
    if not api_key or not validate_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key

def get_ws_api_key(websocket: WebSocket) -> str:
    """Get API key from WebSocket query parameters."""
    api_key = websocket.query_params.get("api_key")
    if not api_key or not validate_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key

def get_permission(required_permission: str):
    """Get permission dependency."""
    async def permission_dependency(request: Request) -> None:
        api_key = request.headers.get("X-API-Key")
        if not api_key or not validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
        
        # For now, all valid API keys have all permissions
        return None
    
    return permission_dependency

async def ws_auth(websocket: WebSocket) -> None:
    """Authenticate WebSocket connection."""
    api_key = websocket.query_params.get("api_key")
    if not api_key or not validate_api_key(api_key):
        await websocket.close(code=4001)
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
