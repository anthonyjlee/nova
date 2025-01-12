"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, Depends
from typing import Dict, Any, Optional
import uuid

from .dependencies import get_memory_system
from .websocket_server import WebSocketServer
from nia.memory.two_layer import TwoLayerMemorySystem

ws_router = APIRouter(prefix="/api/ws", tags=["WebSocket"])

# Initialize WebSocket server and memory system
_websocket_server: Optional[WebSocketServer] = None
_memory_system: Optional[TwoLayerMemorySystem] = None

async def initialize_memory_system() -> TwoLayerMemorySystem:
    """Initialize and verify memory system."""
    global _memory_system
    if _memory_system is None:
        _memory_system = await get_memory_system()
        if _memory_system is None:
            raise ValueError("Failed to initialize memory system")
    return _memory_system

async def get_websocket_server() -> WebSocketServer:
    """Get or create WebSocket server instance."""
    global _websocket_server, _memory_system
    if _websocket_server is None:
        try:
            # Initialize memory system if needed
            memory_system = await initialize_memory_system()
            
            # Create WebSocket server with initialized memory system
            _websocket_server = await WebSocketServer(memory_system)
                
        except Exception as e:
            print(f"Error initializing WebSocket server: {str(e)}")
            _websocket_server = None
            raise
            
    return _websocket_server

# Start background task for memory updates
@ws_router.on_event("startup")
async def start_memory_updates():
    """Start background task for broadcasting memory updates."""
    import asyncio
    try:
        # Get or create WebSocket server
        server = await get_websocket_server()
        asyncio.create_task(server.broadcast_memory_updates())
    except Exception as e:
        print(f"Error starting memory updates: {str(e)}")

@ws_router.websocket("/chat/{client_id}")
async def chat_websocket(
    websocket: WebSocket,
    client_id: str
):
    """WebSocket endpoint for chat/channel updates."""
    server = await get_websocket_server()
    await server.handle_chat_connection(websocket, client_id)

@ws_router.websocket("/tasks/{client_id}")
async def tasks_websocket(
    websocket: WebSocket,
    client_id: str
):
    """WebSocket endpoint for task board updates."""
    server = await get_websocket_server()
    await server.handle_task_connection(websocket, client_id)

@ws_router.websocket("/agents/{client_id}")
async def agents_websocket(
    websocket: WebSocket,
    client_id: str
):
    """WebSocket endpoint for agent status updates."""
    server = await get_websocket_server()
    await server.handle_agent_connection(websocket, client_id)

@ws_router.websocket("/graph/{client_id}")
async def graph_websocket(
    websocket: WebSocket,
    client_id: str
):
    """WebSocket endpoint for knowledge graph updates."""
    server = await get_websocket_server()
    await server.handle_graph_connection(websocket, client_id)
