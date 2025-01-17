"""Nova API endpoints."""

from fastapi import APIRouter, WebSocket, Depends, HTTPException, WebSocketDisconnect
from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime, timezone

from ...core.types.memory_types import EpisodicMemory
from .auth import validate_api_key

from .websocket import websocket_manager
from .dependencies import (
    get_memory_system,
    get_meta_agent,
    get_tiny_factory
)

logger = logging.getLogger(__name__)
nova_router = APIRouter(prefix="/api/nova")

@nova_router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    memory_system = Depends(get_memory_system),
    meta_agent = Depends(get_meta_agent),
    tiny_factory = Depends(get_tiny_factory)
):
    """WebSocket endpoint for real-time updates."""
    connection_timeout = 60  # 60 second timeout
    cleanup_timeout = 5  # 5 second cleanup timeout
    
    try:
        # Get and validate API key from header
        headers = dict(websocket.headers)
        api_key = headers.get("x-api-key")
        
        if not api_key or not validate_api_key(api_key):
            logger.warning(f"Invalid API key for client {client_id}")
            await websocket.close(code=4001, reason="Invalid API key")
            return
        
        # Connect with auth
        connected = await websocket_manager.connect(websocket, client_id, api_key)
        if not connected:
            return
            
        # Send initial state
        if meta_agent:
            await websocket_manager.broadcast_agent_status(
                client_id,
                {
                    "agent_id": "nova", 
                    "status": meta_agent.status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Listen for messages with timeout
        try:
            while True:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=connection_timeout
                    )
                    
                    # Handle channel subscriptions
                    if data.get("type") == "subscribe":
                        channel = data.get("channel")
                        if channel:
                            success = await websocket_manager.join_channel(client_id, channel)
                            if not success:
                                await websocket.send_json({
                                    "type": "error",
                                    "data": {
                                        "message": "Failed to join channel",
                                        "channel": channel
                                    }
                                })
                            continue
                            
                    # Handle channel unsubscriptions
                    if data.get("type") == "unsubscribe":
                        channel = data.get("channel")
                        if channel:
                            success = await websocket_manager.leave_channel(client_id, channel)
                            if not success:
                                await websocket.send_json({
                                    "type": "error",
                                    "data": {
                                        "message": "Failed to leave channel",
                                        "channel": channel
                                    }
                                })
                            continue
                
                    # Handle other message types
                    message_type = data.get("type")
                    if message_type in ["chat_message", "task_update", "agent_status", "graph_update", "llm_stream"]:
                        try:
                            # Process message based on type
                            await process_message(
                                message_type,
                                data,
                                client_id,
                                memory_system,
                                meta_agent,
                                tiny_factory
                            )
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "data": {
                                    "message": f"Error processing {message_type}",
                                    "error": str(e)
                                }
                            })
                except asyncio.TimeoutError:
                    logger.warning(f"Connection timeout for client {client_id}")
                    await websocket.send_json({
                        "type": "warning",
                        "data": {
                            "message": "Connection timeout - closing"
                        }
                    })
                    break
                    
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        if not isinstance(e, WebSocketDisconnect):
            # Only send error message for non-disconnect errors
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": "WebSocket error occurred",
                        "error": str(e)
                    }
                })
            except Exception:
                pass  # Ignore send errors during disconnect
    finally:
        try:
            # Attempt cleanup with timeout
            async with asyncio.timeout(cleanup_timeout):
                await websocket_manager.disconnect(websocket, client_id)
        except asyncio.TimeoutError:
            logger.error(f"Cleanup timeout for client {client_id}")
        except Exception as e:
            logger.error(f"Cleanup error for client {client_id}: {e}")

async def process_message(
    message_type: str,
    data: Dict[str, Any],
    client_id: str,
    memory_system: Any,
    meta_agent: Any,
    tiny_factory: Any
) -> None:
    """Process incoming WebSocket messages."""
    try:
        if message_type == "chat_message":
            # Store message in memory system
            if memory_system:
                content = data.get("content")
                if content is not None:
                    now = datetime.now(timezone.utc)
                    await memory_system.episodic.store_memory(EpisodicMemory(
                        type="chat_message",
                        content=str(content),
                        timestamp=now,  # Pass datetime with timezone
                        metadata={
                            "sender_id": data.get("sender_id"),
                            "timestamp": now.isoformat()
                        }
                    ))
            
            # Process with meta agent if needed
            if meta_agent and data.get("requires_processing"):
                response = await meta_agent.process_interaction(data)
                await websocket_manager.broadcast_chat_message(
                    client_id,
                    response,
                    channel=data.get("channel")
                )
                
        elif message_type == "task_update":
            # Update task state
            if meta_agent:
                response = await meta_agent.update_task(data)
                await websocket_manager.broadcast_task_update(
                    client_id,
                    response,
                    channel=data.get("channel")
                )
                
        elif message_type == "agent_status":
            # Update agent status
            if tiny_factory:
                response = await tiny_factory.update_agent_status(data)
                await websocket_manager.broadcast_agent_status(
                    client_id,
                    response,
                    channel=data.get("channel")
                )
                
        elif message_type == "graph_update":
            # Update knowledge graph
            if memory_system:
                response = await memory_system.update_graph(data)
                await websocket_manager.broadcast_graph_update(
                    client_id,
                    response,
                    channel=data.get("channel")
                )
                
        elif message_type == "llm_stream":
            # Handle LLM stream
            if meta_agent:
                stream_data = {
                    "stream_id": data.get("stream_id"),
                    "chunk": data.get("chunk", ""),
                    "is_final": data.get("is_final", False),
                    "template_id": data.get("template_id")
                }
                await websocket_manager.broadcast_llm_stream(client_id, stream_data)
                
                # Store final response in memory if needed
                if stream_data["is_final"] and memory_system:
                    chunk = stream_data.get("chunk", "")
                    if chunk:
                        now = datetime.now(timezone.utc)
                        await memory_system.episodic.store_memory(EpisodicMemory(
                            type="llm_response",
                            content=str(chunk),
                            timestamp=now,  # Pass datetime with timezone
                            metadata={
                                "template_id": stream_data["template_id"],
                                "timestamp": now.isoformat()
                            }
                        ))
                
    except Exception as e:
        logger.error(f"Error processing {message_type} message: {e}")
        # Send error message back to client
        await websocket_manager.broadcast_to_client(
            client_id,
            {
                "type": "error",
                "data": {
                    "message": str(e),
                    "message_type": message_type
                }
            }
        )
