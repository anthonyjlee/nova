"""NIA UI Package.

This package provides both mobile and desktop interfaces for the NIA system:

1. Mobile Interface (Remote Control):
   - Simplified command interface
   - Basic chat functionality
   - Essential memory queries
   - Touch-optimized design
   - Remote computer control

2. Desktop Interface (Full Dashboard):
   - System-1 (Real-time):
     * Direct computer interaction
     * Real-time responses and actions
     * API key management
     * Multi-display support
   
   - System-2 (Nova/Agents):
     * WhatsApp-style messenger
     * Pinned Nova group chat
     * Individual agent chats
     * Session data visualization
     * Debugging information
   
   - Memory System:
     * Neo4j graph visualization
     * Advanced query interface
     * Memory browsing
     * Concept relationships
     * Real-time statistics
   
   - Settings & Configuration:
     * API key management
     * Neo4j connection settings
     * UI preferences
     * System monitoring
"""

from .mobile import MobileUI
from .desktop import DesktopUI
from .handlers import System1Handler, System2Handler, MemoryHandler

__all__ = [
    'MobileUI',
    'DesktopUI',
    'System1Handler',
    'System2Handler',
    'MemoryHandler'
]
