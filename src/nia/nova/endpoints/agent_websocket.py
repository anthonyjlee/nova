"""WebSocket endpoint for direct agent communication."""

from fastapi import WebSocket, Depends
from typing import Dict, Any, Optional
import logging
import json
import uuid
from datetime import datetime

from ..core.websocket_manager import websocket_manager
from ..core.auth import get_ws_api_key
from ..core.dependencies import get_agent_store

logger = logging.getLogger(__name__)

async def handle_agent_message(
    websocket: WebSocket,
    client_id: str,
    agent_id: str,
    message: Dict[str, Any],
    agent_store: Any
):
    """Handle messages between client and agent."""
    try:
        # Get agent from store
        agent = await agent_store.get_agent(agent_id)
        if not agent:
            await websocket_manager.broadcast_to_client(
                client_id,
                {
                    "type": "error",
                    "error": f"Agent {agent_id} not found",
                    "timestamp": datetime.now().isoformat()
                }
            )
            return

        # Process message based on type
        if message["type"] == "chat":
            # Get agent response
            response = await agent.process_message(message["content"])
            
            # Send response back to client
            await websocket_manager.broadcast_to_client(
                client_id,
                {
                    "type": "chat",
                    "content": response,
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        elif message["type"] == "command":
            # Handle agent commands
            result = await agent.execute_command(message["command"], message.get("args", {}))
            
            # Send result back to client
            await websocket_manager.broadcast_to_client(
                client_id,
                {
                    "type": "command_result",
                    "result": result,
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            )

    except Exception as e:
        logger.error(f"Error handling agent message: {str(e)}")
        await websocket_manager.broadcast_to_client(
            client_id,
            {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

async def agent_websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    api_key: str = Depends(get_ws_api_key),
    agent_store: Any = Depends(get_agent_store)
):
    """WebSocket endpoint for direct agent communication."""
    client_id = str(uuid.uuid4())
    
    try:
        # Accept connection
        await websocket.accept()
        
        # Add to connection manager
        await websocket_manager.connect(websocket, client_id)
        
        # Send connected message
        await websocket_manager.broadcast_to_client(
            client_id,
            {
                "type": "connected",
                "agent_id": agent_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Message loop
        try:
            while True:
                # Receive message
                message = await websocket.receive_json()
                
                # Handle message
                await handle_agent_message(websocket, client_id, agent_id, message, agent_store)
                
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            
    finally:
        # Clean up connection
        await websocket_manager.disconnect(client_id)
