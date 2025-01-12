"""WebSocket server for real-time updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from qdrant_client.http import models
from nia.core.types.memory_types import Memory, MemoryType

class ConnectionManager:
    """Manage WebSocket connections."""
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {
            "chat": {},      # Chat/channel connections
            "tasks": {},     # Task board connections
            "agents": {},    # Agent status connections
            "graph": {}      # Knowledge graph connections
        }
        
    async def connect(self, websocket: WebSocket, client_id: str, connection_type: str):
        """Connect a client to a specific type of updates."""
        try:
            if connection_type not in self.active_connections:
                raise ValueError(f"Invalid connection type: {connection_type}")
                
            # Accept connection if not already accepted
            if websocket.client_state.DISCONNECTED:
                await websocket.accept()
                
            # Store connection
            self.active_connections[connection_type][client_id] = websocket
            
            # Send initial connection success message
            await websocket.send_json({
                "type": "connection_success",
                "connection_type": connection_type,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error connecting client {client_id}: {str(e)}")
            try:
                await websocket.close(code=1011, reason=str(e))
            except:
                pass
            raise
            
    def disconnect(self, client_id: str, connection_type: str):
        """Disconnect a client."""
        if connection_type in self.active_connections:
            self.active_connections[connection_type].pop(client_id, None)
            
    async def broadcast(self, message: Dict[str, Any], connection_type: str):
        """Broadcast message to all connections of a specific type."""
        if connection_type not in self.active_connections:
            return
            
        # Add timestamp to message
        message["timestamp"] = datetime.now().isoformat()
        
        # Broadcast to all connected clients
        for connection in self.active_connections[connection_type].values():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting message: {str(e)}")

class WebSocketServer:
    """WebSocket server for real-time updates."""
    def __init__(self, memory_system_provider: Any):
        """Initialize WebSocket server.
        
        Args:
            memory_system_provider: Memory system provider function or instance
        """
        self.manager = ConnectionManager()
        self.memory_system_provider = memory_system_provider
        self.memory_system = None
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._init_task = None

    @classmethod
    async def create(cls, memory_system_provider: Any) -> 'WebSocketServer':
        """Create and initialize a WebSocket server instance.
        
        Args:
            memory_system_provider: Memory system provider function or instance
            
        Returns:
            Initialized WebSocketServer instance
        """
        server = cls(memory_system_provider)
        await server.initialize()
        return server

    async def initialize(self):
        """Initialize the WebSocket server asynchronously."""
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:  # Double-check inside lock
                return

            # Get memory system
            if callable(self.memory_system_provider):
                self.memory_system = await self.memory_system_provider()
            else:
                self.memory_system = self.memory_system_provider
            
            # Initialize memory system if needed
            if not getattr(self.memory_system, '_initialized', False):
                await self.memory_system.initialize()
            
            self._initialized = True

    async def ensure_initialized(self):
        """Ensure the WebSocket server is initialized."""
        if not self._initialized:
            if not self._init_task:
                self._init_task = asyncio.create_task(self.initialize())
            await self._init_task

        
    async def handle_chat_connection(self, websocket: WebSocket, client_id: str):
        """Handle chat/channel WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "chat")
        try:
            while True:
                data = await websocket.receive_json()
                
                # Store message in memory system
                await self.memory_system.store_experience(Memory(
                    content=data,
                    type=MemoryType.EPISODIC,
                    importance=0.5,
                    context={
                        "type": "chat_message",
                        "timestamp": datetime.now().isoformat()
                    }
                ))
                
                # Broadcast to other clients
                await self.manager.broadcast(
                    {"type": "message", "data": data},
                    "chat"
                )
        except WebSocketDisconnect:
            self.manager.disconnect(client_id, "chat")
            
    async def handle_task_connection(self, websocket: WebSocket, client_id: str):
        """Handle task board WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "tasks")
        try:
            while True:
                data = await websocket.receive_json()
                
                # Store task update in memory system
                await self.memory_system.store_experience(Memory(
                    content=data,
                    type=MemoryType.EPISODIC,
                    importance=0.7,
                    context={
                        "type": "task_update",
                        "timestamp": datetime.now().isoformat()
                    }
                ))
                
                # Update task in semantic layer if needed
                if data.get("type") == "state_change":
                    await self.memory_system.semantic.run_query(
                        """
                        MATCH (t:Task {id: $task_id})
                        SET t.status = $new_status,
                            t.updated_at = datetime()
                        """,
                        {
                            "task_id": data["task_id"],
                            "new_status": data["new_status"]
                        }
                    )
                
                # Broadcast to other clients
                await self.manager.broadcast(
                    {"type": "task_update", "data": data},
                    "tasks"
                )
        except WebSocketDisconnect:
            self.manager.disconnect(client_id, "tasks")
            
    async def handle_agent_connection(self, websocket: WebSocket, client_id: str):
        """Handle agent status WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "agents")
        try:
            while True:
                data = await websocket.receive_json()
                
                # Store agent status in memory system
                await self.memory_system.store_experience(Memory(
                    content=data,
                    type=MemoryType.EPISODIC,
                    importance=0.6,
                    context={
                        "type": "agent_status",
                        "timestamp": datetime.now().isoformat()
                    }
                ))
                
                # Update agent status in semantic layer
                if data.get("type") == "status_change":
                    await self.memory_system.semantic.run_query(
                        """
                        MATCH (a:Agent {id: $agent_id})
                        SET a.status = $new_status,
                            a.updated_at = datetime()
                        """,
                        {
                            "agent_id": data["agent_id"],
                            "new_status": data["new_status"]
                        }
                    )
                
                # Broadcast to other clients
                await self.manager.broadcast(
                    {"type": "agent_status", "data": data},
                    "agents"
                )
        except WebSocketDisconnect:
            self.manager.disconnect(client_id, "agents")
            
    async def handle_graph_connection(self, websocket: WebSocket, client_id: str):
        """Handle knowledge graph WebSocket connections."""
        await self.ensure_initialized()
        await self.manager.connect(websocket, client_id, "graph")
        try:
            while True:
                data = await websocket.receive_json()
                
                # Store graph update in memory system
                await self.memory_system.store_experience(Memory(
                    content=data,
                    type=MemoryType.EPISODIC,
                    importance=0.8,
                    context={
                        "type": "graph_update",
                        "timestamp": datetime.now().isoformat()
                    }
                ))
                
                # Update graph in semantic layer
                if data.get("type") == "node_update":
                    await self.memory_system.semantic.run_query(
                        """
                        MATCH (n {id: $node_id})
                        SET n += $properties,
                            n.updated_at = datetime()
                        """,
                        {
                            "node_id": data["node_id"],
                            "properties": data["properties"]
                        }
                    )
                elif data.get("type") == "edge_update":
                    await self.memory_system.semantic.run_query(
                        """
                        MATCH (s {id: $source_id})-[r]-(t {id: $target_id})
                        SET r += $properties,
                            r.updated_at = datetime()
                        """,
                        {
                            "source_id": data["source_id"],
                            "target_id": data["target_id"],
                            "properties": data["properties"]
                        }
                    )
                
                # Broadcast to other clients
                await self.manager.broadcast(
                    {"type": "graph_update", "data": data},
                    "graph"
                )
        except WebSocketDisconnect:
            self.manager.disconnect(client_id, "graph")
            
    async def broadcast_memory_updates(self):
        """Background task to broadcast memory system updates."""
        # Initialize update buffer
        pending_updates = []
        
        while True:
            try:
                # Ensure memory system is properly initialized
                await self.ensure_initialized()
                
                # Verify memory system is ready
                if not hasattr(self.memory_system, 'episodic') or not hasattr(self.memory_system.episodic, 'store'):
                    print("Memory system not properly initialized, retrying...")
                    await asyncio.sleep(5)
                    continue
                
                # Get recent updates from memory system
                try:
                    new_updates = await self.memory_system.episodic.store.search_vectors(
                        content={},
                        filter_conditions=[
                            models.FieldCondition(
                                key="metadata_type",
                                match=models.MatchAny(any=["chat_message", "task_update", "agent_status", "graph_update"])
                            )
                        ]
                    )
                except Exception as e:
                    print(f"Error searching vectors: {str(e)}")
                    await asyncio.sleep(5)
                    continue

                # Add new updates to pending buffer
                pending_updates.extend(new_updates)
                
                # Process all pending updates
                if pending_updates:
                    # Group updates by type
                    grouped_updates = {
                        "chat": [],
                        "tasks": [],
                        "agents": [],
                        "graph": []
                    }
                    
                    for update in pending_updates:
                        if update["type"] == "chat_message":
                            grouped_updates["chat"].append(update)
                        elif update["type"] == "task_update":
                            grouped_updates["tasks"].append(update)
                        elif update["type"] == "agent_status":
                            grouped_updates["agents"].append(update)
                        elif update["type"] == "graph_update":
                            grouped_updates["graph"].append(update)
                    
                    # Broadcast updates to respective clients
                    broadcast_success = True
                    for update_type, updates in grouped_updates.items():
                        if updates:
                            try:
                                await self.manager.broadcast(
                                    {
                                        "type": f"{update_type}_updates",
                                        "data": updates
                                    },
                                    update_type
                                )
                            except Exception as e:
                                print(f"Error broadcasting {update_type} updates: {str(e)}")
                                broadcast_success = False
                                break
                    
                    # Clear pending updates only if broadcast was successful
                    if broadcast_success:
                        pending_updates.clear()
                
                # Sleep for a short interval
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in memory update broadcast: {str(e)}")
                await asyncio.sleep(5)  # Sleep longer on error
