"""NIA UI Package.

This package provides a WhatsApp-style chat interface for the NIA system:

1. Chat Features:
   - Multi-agent chat system
   - Group and individual agent conversations
   - Chat history tracking
   - Message handling with error management
   - Memory integration

2. Available Agents:
   - Nova (Main): Primary chat interface
   - Meta Agent: Coordinates and synthesizes interactions
   - Belief Agent: Handles knowledge validation
   - Desire Agent: Manages goals and aspirations
   - Emotion Agent: Processes emotional context
   - Reflection Agent: Analyzes patterns and insights

3. Memory Integration:
   - Chat history persistence
   - Memory retrieval and storage
   - Context management
"""

from .mobile import MobileUI
from .desktop import DesktopUI
from .handlers import System2Handler, MemoryHandler

__all__ = [
    'MobileUI',
    'DesktopUI',
    'System2Handler',
    'MemoryHandler'
]
