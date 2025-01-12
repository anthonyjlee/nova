"""Simplified TinyPerson implementation."""

from typing import Dict, List, Optional

class TinyPerson:
    """Base class for tiny person implementation."""
    
    def __init__(self, name: str):
        """Initialize tiny person.
        
        Args:
            name: Name of the person
        """
        self.name = name
        self._state = {
            "emotions": {},
            "goals": [],
            "memories": []
        }
        
    def get_state(self) -> Dict:
        """Get current state."""
        return self._state
        
    def update_state(self, state_update: Dict):
        """Update state with new values."""
        for key, value in state_update.items():
            if key in self._state:
                if isinstance(value, dict):
                    self._state[key].update(value)
                elif isinstance(value, list):
                    self._state[key].extend(value)
                else:
                    self._state[key] = value
