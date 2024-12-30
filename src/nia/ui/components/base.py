"""Base UI class with common functionality for NIA chat interface."""

import logging
import os
import platform
from datetime import datetime
from typing import Optional, Dict, Any

from ..handlers.handlers import System2Handler, MemoryHandler
from ..state import UIState

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BaseUI:
    """Base UI class with common functionality."""
    
    def __init__(self, state_dir: str = None):
        """Initialize base UI.
        
        Args:
            state_dir: Optional directory for state persistence
        """
        logger.info("Initializing base UI...")
        
        # Set up state directory
        self.state_dir = state_dir or os.path.expanduser("~/.nia/state")
        os.makedirs(self.state_dir, exist_ok=True)
        
        self.title = "NIA Chat"
        self.description = """
        # NIA Chat Interface
        
        **Nova (Main)**: Synthesized responses and key insights
        **Nova Orchestration**: View agent interactions and task coordination
        """
        
        # Initialize state with persistence
        self.state = UIState(load_existing=True, state_dir=self.state_dir)
        
        # Initialize handlers with state
        logger.info("Initializing handlers...")
        try:
            self.memory = MemoryHandler(state=self.state)
            self.system2 = System2Handler(state=self.state)
            
            # Store handler references in state
            self.state.set('handlers', {
                'memory': True,
                'system2': True,
                'initialized_at': datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to initialize handlers: {e}")
            self.memory = None
            self.system2 = None
            self.state.set('handlers', {
                'memory': False,
                'system2': False,
                'error': str(e),
                'initialized_at': datetime.now().isoformat()
            })
        
        # Initialize debug output and add to state
        self.debug_output = []
        self.state.set('debug_output', self.debug_output)
        
        # Restore UI state from persistence
        self._restore_ui_state()
        
        logger.info("Base UI initialization complete")
    
    def log_system_info(self):
        """Log system information."""
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
    
    def get_handler_status(self) -> Dict[str, Any]:
        """Get detailed status of handlers."""
        status = self.state.get('handlers', {})
        status.update({
            'memory': {
                'available': self.memory is not None,
                'last_error': None if self.memory else status.get('error')
            },
            'system2': {
                'available': self.system2 is not None,
                'last_error': None if self.system2 else status.get('error')
            },
            'last_checked': datetime.now().isoformat()
        })
        self.state.set('handlers', status)
        return status
    
    def _restore_ui_state(self):
        """Restore UI state from persistence."""
        try:
            # Restore debug output
            saved_debug = self.state.get('debug_output', [])
            if saved_debug:
                self.debug_output = saved_debug
            
            # Restore UI preferences
            ui_prefs = self.state.get('ui_preferences', {})
            if ui_prefs:
                self.title = ui_prefs.get('title', self.title)
                self.description = ui_prefs.get('description', self.description)
            
            # Log restoration
            logger.info("UI state restored successfully")
            self.add_debug_line("UI state restored")
            
        except Exception as e:
            logger.error(f"Error restoring UI state: {e}")
            self.add_debug_line(f"Error restoring state: {e}")
    
    def add_debug_line(self, line: str):
        """Add a line to debug output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        debug_line = f"[{timestamp}] {line}"
        self.debug_output.append(debug_line)
        self.state.set('debug_output', self.debug_output)
    
    def clear_debug_output(self):
        """Clear debug output."""
        self.debug_output = []
        self.state.set('debug_output', self.debug_output)
    
    def get_debug_output(self) -> str:
        """Get debug output as string."""
        return "\n".join(self.debug_output)
    
    def sync_gradio_state(self, gradio_state: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Gradio state with UI state.
        
        Args:
            gradio_state: Current Gradio state
            
        Returns:
            Updated Gradio state
        """
        # Ensure Gradio state exists
        if gradio_state is None:
            gradio_state = {}
        
        # Copy UI state to Gradio state
        for key, value in self.state.state.items():
            gradio_state[key] = value
        
        return gradio_state

    def save_ui_state(self):
        """Save current UI state and trigger persistence."""
        try:
            # Save UI preferences
            ui_prefs = {
                'title': self.title,
                'description': self.description,
                'last_saved': datetime.now().isoformat()
            }
            self.state.set('ui_preferences', ui_prefs)
            
            # Save debug output
            self.state.set('debug_output', self.debug_output)
            
            logger.info("UI state saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving UI state: {e}")
    
    async def launch(
        self,
        share: bool = True,
        server_name: str = "127.0.0.1",
        server_port: int = None,
        state_dir: str = None
    ):
        """Launch the UI. Must be implemented by subclasses."""
        try:
            # Save state before launch
            self.save_ui_state()
            
            # Subclasses must implement actual launch
            raise NotImplementedError("Subclasses must implement launch()")
            
        except Exception as e:
            logger.error(f"Error launching UI: {e}")
            self.add_debug_line(f"Launch error: {e}")
            raise
