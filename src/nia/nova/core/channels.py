"""Channel management for Nova's real-time communication."""

from typing import Dict, Set, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChannelManager:
    """Manages channel subscriptions and message routing."""
    
    def __init__(self):
        """Initialize channel manager."""
        self.channels: Dict[str, Set[str]] = {
            "NovaTeam": set(),      # Core agents channel
            "NovaSupport": set()    # Support agents channel
        }
        self.channel_metadata: Dict[str, Dict[str, Any]] = {
            "NovaTeam": {
                "description": "Core agent operations and coordination",
                "type": "core",
                "capabilities": [
                    "task_detection",
                    "cognitive_processing",
                    "team_coordination"
                ]
            },
            "NovaSupport": {
                "description": "System operations and maintenance",
                "type": "support",
                "capabilities": [
                    "resource_allocation",
                    "memory_consolidation",
                    "system_health"
                ]
            }
        }
        
    async def join_channel(self, client_id: str, channel: str) -> bool:
        """Join a specific channel."""
        if channel in self.channels:
            self.channels[channel].add(client_id)
            logger.info(f"Client {client_id} joined channel {channel}")
            return True
        return False
            
    async def leave_channel(self, client_id: str, channel: str) -> bool:
        """Leave a specific channel."""
        if channel in self.channels:
            self.channels[channel].discard(client_id)
            logger.info(f"Client {client_id} left channel {channel}")
            return True
        return False
            
    async def get_channel_members(self, channel: str) -> Optional[Set[str]]:
        """Get all members of a channel."""
        return self.channels.get(channel)
            
    async def get_client_channels(self, client_id: str) -> Set[str]:
        """Get all channels a client is subscribed to."""
        return {
            channel
            for channel, members in self.channels.items()
            if client_id in members
        }
            
    async def get_channel_metadata(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific channel."""
        return self.channel_metadata.get(channel)
    
    async def validate_message(self, channel: str, message_type: str) -> bool:
        """Validate if a message type is allowed in a channel."""
        if channel not in self.channel_metadata:
            return False
            
        # Define allowed message types per channel
        allowed_types = {
            "NovaTeam": {
                "task_update",
                "agent_status",
                "cognitive_state",
                "team_coordination"
            },
            "NovaSupport": {
                "system_status",
                "resource_update",
                "memory_operation",
                "health_check"
            }
        }
        
        return message_type in allowed_types.get(channel, set())
    
    async def format_channel_message(
        self,
        channel: str,
        message_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format a message for channel broadcast."""
        return {
            "type": message_type,
            "channel": channel,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "channel_type": self.channel_metadata[channel]["type"],
                "capabilities": self.channel_metadata[channel]["capabilities"]
            }
        }
    
    async def cleanup_client(self, client_id: str):
        """Remove client from all channels."""
        for channel in self.channels:
            await self.leave_channel(client_id, channel)
            
    def get_channels(self) -> Dict[str, Dict[str, Any]]:
        """Get all available channels with metadata."""
        return {
            channel: {
                "members": len(members),
                **self.channel_metadata[channel]
            }
            for channel, members in self.channels.items()
        }

# Global channel manager instance
channel_manager = ChannelManager()
