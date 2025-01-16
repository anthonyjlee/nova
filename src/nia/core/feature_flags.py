from typing import Optional
import redis.asyncio as redis

class FeatureFlags:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.prefix = "debug:"
        
    async def enable_debug(self, flag_name: str):
        """Enable debug flag."""
        key = f"{self.prefix}{flag_name}"
        await self.redis.set(key, "true")
        
    async def disable_debug(self, flag_name: str):
        """Disable debug flag."""
        key = f"{self.prefix}{flag_name}"
        await self.redis.set(key, "false")
        
    async def is_debug_enabled(self, flag_name: str) -> bool:
        """Check if debug flag is enabled."""
        key = f"{self.prefix}{flag_name}"
        value = await self.redis.get(key)
        return value == b"true"

# Debug flags
DEBUG_FLAGS = {
    'log_validation': 'debug:log_validation',     # Log all validation attempts
    'log_websocket': 'debug:log_websocket',       # Log WebSocket messages
    'log_storage': 'debug:log_storage',           # Log storage operations
    'strict_mode': 'debug:strict_mode'            # Throw on any validation error
}
