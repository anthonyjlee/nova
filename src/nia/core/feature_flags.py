"""Feature flags implementation."""

from typing import Optional
from redis.asyncio import Redis

# Debug flags
DEBUG_FLAGS = {
    'log_validation': 'debug:log_validation',     # Log all validation attempts
    'log_websocket': 'debug:log_websocket',       # Log WebSocket messages
    'log_storage': 'debug:log_storage',           # Log storage operations
    'strict_mode': 'debug:strict_mode'            # Throw on any validation error
}

class FeatureFlags:
    """Feature flags manager using Redis."""
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "debug:"
        
    async def enable_debug(self, flag_name: str):
        """Enable debug flag."""
        key = f"{self.prefix}{flag_name}"
        await self.redis.set(key, "true")
        
    async def is_debug_enabled(self, flag_name: str) -> bool:
        """Check if debug flag is enabled."""
        key = f"{self.prefix}{flag_name}"
        return await self.redis.get(key) == b"true"

_feature_flags: Optional[FeatureFlags] = None

async def get_feature_flags() -> FeatureFlags:
    """Get or create feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        redis_client = Redis(host='localhost', port=6379, db=0)
        _feature_flags = FeatureFlags(redis_client)
    return _feature_flags
