"""Simplified TinyWorld implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime

class TinyWorld:
    """Base class for tiny world implementation."""
    
    def __init__(self, name: str):
        """Initialize tiny world.
        
        Args:
            name: Name of the world
        """
        self.name = name
        self._agents = {}
        self._state = {
            "resources": {},
            "events": [],
            "active": True
        }
        
    def add_agent(self, agent_id: str, agent: Any):
        """Add an agent to the world."""
        self._agents[agent_id] = agent
        
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
        
    def get_state(self) -> Dict:
        """Get current world state."""
        return self._state
        
    def update_state(self, state_update: Dict):
        """Update world state."""
        for key, value in state_update.items():
            if key in self._state:
                if isinstance(value, dict):
                    self._state[key].update(value)
                elif isinstance(value, list):
                    self._state[key].extend(value)
                else:
                    self._state[key] = value
