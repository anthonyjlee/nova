"""State management for the NIA chat interface."""

import os
import json
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UIState:
    """Manages UI state and persistence."""
    
    def __init__(self, load_existing: bool = True, state_dir: str = None):
        """Initialize UI state.
        
        Args:
            load_existing: Whether to load existing state from file
            state_dir: Optional directory for state persistence
        """
        # Set up state persistence
        self.state_dir = state_dir or os.path.expanduser("~/.nia/state")
        self.state_file = os.path.join(self.state_dir, "ui_state.json")
        os.makedirs(self.state_dir, exist_ok=True)
        # Default state structure
        self.default_state = {
            # UI State - Core components that must persist
            'active_agents': [],
            'concepts': [],
            'memory_stats': {},
            'agent_interactions': [],
            'orchestration_history': [],  # Critical for orchestration view
            'nova_history': [],          # Critical for main chat view
            
            # Episodic Memory - Must persist between sessions
            'conversation_history': [],  # Full conversation context
            'interaction_patterns': {},  # User patterns
            'ui_preferences': {          # User preferences with defaults
                'theme': 'default',
                'chat_height': 400,
                'show_whispers': True,
                'show_debug': False
            },
            
            # Semantic Memory - Critical for context preservation
            'concept_network': {},      # Concept relationships
            'concept_context': {},      # Enriched concepts
            'concept_visuals': [],      # Visual elements
            
            # Neo4j Integration - Persistent visualization state
            'graph_layout': 'cose',
            'saved_queries': [],
            'node_styles': {},
            'view_state': {
                'active_tab': 'nova_main',
                'open_accordions': ['Active Agents', 'Key Concepts'],
                'graph_filters': [],
                'last_query': None
            },
            
            # System state
            'initialized': False,
            'last_update': None,
            'refresh_count': 0,
            'errors': []
        }
        
        # Initialize with default or load existing
        self.state = self.default_state.copy()
        if load_existing:
            self._load_state()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state."""
        return self.state.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a value in state and save."""
        self.state[key] = value
        self.state['last_update'] = datetime.now().isoformat()
        self.state['refresh_count'] += 1
        self.save_state()  # Auto-save on update
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple state values and save."""
        self.state.update(updates)
        self.state['last_update'] = datetime.now().isoformat()
        self.state['refresh_count'] += 1
        self.save_state()  # Auto-save on update
    
    def _load_state(self):
        """Load existing state from file or initialize defaults."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    loaded_state = json.load(f)
                    # Update with loaded state while preserving defaults
                    for key in self.default_state:
                        if key not in loaded_state:
                            loaded_state[key] = self.default_state[key]
                    self.state = loaded_state
            else:
                # Initialize with defaults if no file exists
                for key in self.default_state:
                    if key not in self.state:
                        self.state[key] = self.default_state[key]
            
            # Mark as initialized
            self.state['initialized'] = True
            self.state['last_update'] = datetime.now().isoformat()
            
            # Save initial state
            self.save_state()
            
        except Exception as e:
            self.state['errors'].append(f"Error loading state: {str(e)}")
            self.state.update(self.default_state)
            # Try to save default state
            self.save_state()
    
    def save_state(self):
        """Save current state to file."""
        try:
            # Create temp file for atomic write
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            # Atomic replace
            os.replace(temp_file, self.state_file)
            logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            error_msg = f"Error saving state: {str(e)}"
            logger.error(error_msg)
            self.state['errors'].append(error_msg)

    def clear(self):
        """Clear state while preserving critical data and saving."""
        # Preserve some critical data
        preserved = {
            'ui_preferences': self.state.get('ui_preferences', {}),
            'concept_network': self.state.get('concept_network', {}),
            'saved_queries': self.state.get('saved_queries', [])
        }
        
        # Reset to defaults
        self.state = self.default_state.copy()
        
        # Restore preserved data
        self.state.update(preserved)
        
        # Update metadata and save
        self.state['initialized'] = True
        self.state['last_update'] = datetime.now().isoformat()
        self.state['refresh_count'] = 0
        self.save_state()
