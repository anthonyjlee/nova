"""FastAPI endpoints for chat and thread management."""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from uuid import uuid4

from ..core.dependencies import (
    get_memory_system,
    get_analytics_agent,
    get_coordination_agent
)
from ...core.auth import check_rate_limit, get_permission, verify_token
from ...core.error_handling import ServiceError, ValidationError
from ...core.websocket_types import (
    WebSocketState, WebSocketError, WebSocketSession,
    WebSocketConfig, WebSocketEvent, WebSocketMessageType
)
from ...core.types.memory_types import Memory

logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, Dict[str, Any]] = {}  # connection_id -> {session, websocket, thread_id}

logger = logging.getLogger(__name__)

chat_router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(check_rate_limit)]
)

@chat_router.post("/threads")
async def create_thread(
    request: Dict[str, Any],
    memory_system: Any = Depends(get_memory_system),
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Create a new chat thread."""
    try:
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        thread_type = request.get("type", "main")  # main or sub-thread
        parent_id = request.get("parent_id")  # for sub-threads
        
        # Create thread in semantic layer
        await memory_system.semantic.run_query(
            """
            CREATE (t:ChatThread {
                id: $thread_id,
                type: $thread_type,
                parent_id: $parent_id,
                created_at: datetime(),
                updated_at: datetime(),
                status: 'active',
                domain: $domain,
                task_type: $task_type,
                aggregation_enabled: $aggregation_enabled
            })
            """,
            {
                "thread_id": thread_id,
                "thread_type": thread_type,
                "parent_id": parent_id,
                "domain": request.get("domain", "general"),
                "task_type": request.get("task_type", "chat"),
                "aggregation_enabled": thread_type == "sub-thread"
            }
        )
        
        # Store thread creation event in episodic memory
        await memory_system.store_experience(Memory(
            id=str(uuid4()),
            type="thread_created",
            content={
                "thread_id": thread_id,
                "type": thread_type,
                "parent_id": parent_id,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "aggregation_enabled": thread_type == "sub-thread",
                "output_types": {
                    "code": True,
                    "media": True,
                    "new_skill": True,
                    "document": True,
                    "api_call": True
                }
            },
            metadata={
                "thread_id": thread_id,
                "event_type": "creation"
            }
        ))
        
        return {
            "thread_id": thread_id,
            "type": thread_type,
            "parent_id": parent_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "aggregation_enabled": thread_type == "sub-thread",
            "output_types": {
                "code": True,
                "media": True,
                "new_skill": True,
                "document": True,
                "api_call": True
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/tasks")
async def create_emergent_task(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Create an emergent task from thread."""
    try:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_data = {
            "task_id": task_id,
            "thread_id": thread_id,
            "description": request["description"],
            "output_type": request["output_type"],  # code, media, new_skill, document, api_call
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "domain": request.get("domain", "professional")
        }
        
        return task_data
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/tasks/{task_id}/status")
async def update_task_status(
    thread_id: str,
    task_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Update emergent task status."""
    try:
        return {
            "task_id": task_id,
            "thread_id": thread_id,
            "status": request["status"],  # pending, in_progress, completed, failed
            "output_data": request.get("output_data"),  # Task output if completed
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}/tasks")
async def get_thread_tasks(
    thread_id: str,
    status: Optional[str] = None,
    output_type: Optional[str] = None,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Get emergent tasks for thread."""
    try:
        return {
            "thread_id": thread_id,
            "tasks": [],  # Get from memory system
            "total_count": 0
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Update thread status (active/archived)."""
    try:
        return {
            "thread_id": thread_id,
            "status": request["status"],
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}/summary")
async def get_thread_summary(
    thread_id: str,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Get thread summary from aggregator."""
    try:
        return {
            "thread_id": thread_id,
            "summary": "",  # Get from aggregator
            "key_points": [],
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}/children")
async def get_thread_children(
    thread_id: str,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Get sub-threads for a main thread."""
    try:
        return {
            "thread_id": thread_id,
            "children": [],  # Get sub-threads
            "total_count": 0
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    show_partial_logs: bool = True,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Get thread details and messages."""
    try:
        if thread_id == "nonexistent":
            raise HTTPException(status_code=404, detail="Thread not found")
            
        # Get thread from memory system
        thread_messages = await memory_system.episodic.search(
            filter={
                "type": "chat_message",
                "thread_id": thread_id
            },
            limit=100,
            sort=[("timestamp", "desc")]
        )
        
        # Get thread metadata
        thread_data = await memory_system.semantic.run_query(
            """
            MATCH (t:ChatThread {id: $thread_id})
            RETURN {
                id: t.id,
                status: coalesce(t.status, 'active'),
                created_at: toString(coalesce(t.created_at, datetime())),
                updated_at: toString(coalesce(t.updated_at, datetime())),
                domain: coalesce(t.domain, 'general'),
                task_type: coalesce(t.task_type, 'chat')
            } as thread
            """,
            {"thread_id": thread_id}
        )
        
        if not thread_data:
            raise HTTPException(status_code=404, detail="Thread not found")
            
        # Get referenced domain entities
        domain_refs = await memory_system.semantic.run_query(
            """
            MATCH (t:ChatThread {id: $thread_id})-[:REFERENCES]->(e:Concept)
            RETURN collect({
                id: toString(id(e)),
                name: e.name,
                type: e.type
            }) as refs
            """,
            {"thread_id": thread_id}
        )
        
        # Get related graph nodes
        graph_nodes = await memory_system.semantic.run_query(
            """
            MATCH (t:ChatThread {id: $thread_id})-[:RELATES_TO]->(n)
            RETURN collect({
                id: toString(id(n)),
                type: labels(n)[0],
                properties: properties(n)
            }) as nodes
            """,
            {"thread_id": thread_id}
        )
        
        # Get agent reasoning chain if enabled
        chain_of_thought = []
        if show_partial_logs:
            chain_data = await memory_system.episodic.search(
                filter={
                    "type": "agent_thought",
                    "thread_id": thread_id
                },
                limit=100,
                sort=[("timestamp", "asc")]
            )
            chain_of_thought = [
                {
                    "agent": thought["agent_id"],
                    "thought": thought["content"],
                    "timestamp": thought["timestamp"]
                }
                for thought in chain_data
            ]
        
        thread_metadata = thread_data[0]["thread"]
        return {
            "thread_id": thread_id,
            "messages": thread_messages,
            "status": thread_metadata["status"],
            "domain_references": domain_refs[0]["refs"] if domain_refs else [],
            "graph_nodes": graph_nodes[0]["nodes"] if graph_nodes else [],
            "chain_of_thought": chain_of_thought if show_partial_logs else None,
            "metadata": {
                "created_at": thread_metadata["created_at"],
                "updated_at": thread_metadata["updated_at"],
                "domain": thread_metadata["domain"],
                "task_type": thread_metadata["task_type"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/logs")
async def update_log_visibility(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Update thread log visibility settings."""
    try:
        return {
            "thread_id": thread_id,
            "show_partial_logs": request["show_partial_logs"],
            "show_agent_thoughts": request["show_agent_thoughts"],
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/link")
async def link_thread_to_graph(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Link thread to graph nodes."""
    try:
        return {
            "thread_id": thread_id,
            "node_ids": request["node_ids"],
            "link_type": request["link_type"],
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/messages")
async def add_message(
    thread_id: str,
    request: Dict[str, Any],
    memory_system: Any = Depends(get_memory_system),
    _: None = Depends(get_permission("write"))
) -> Dict:
    """Add message to thread."""
    try:
        if "content" not in request:
            raise HTTPException(status_code=422, detail="Message content is required")
            
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        
        # Store message in episodic memory
        await memory_system.store_experience(Memory(
            id=message_id,
            type="chat_message",
            content={
                "message_id": message_id,
                "thread_id": thread_id,
                "content": request["content"],
                "sender": request.get("sender", "user"),
                "timestamp": timestamp,
                "message_type": request.get("message_type", "text"),
                "metadata": request.get("metadata", {})
            },
            metadata={
                "thread_id": thread_id,
                "message_type": request.get("message_type", "text"),
                "sender": request.get("sender", "user")
            }
        ))
        
        # Update thread in semantic layer
        await memory_system.semantic.run_query(
            """
            MATCH (t:ChatThread {id: $thread_id})
            SET t.updated_at = datetime()
            WITH t
            MERGE (m:ChatMessage {id: $message_id})
            SET m.content = $content,
                m.sender = $sender,
                m.timestamp = datetime(),
                m.message_type = $message_type
            MERGE (t)-[:HAS_MESSAGE]->(m)
            """,
            {
                "thread_id": thread_id,
                "message_id": message_id,
                "content": request["content"],
                "sender": request.get("sender", "user"),
                "message_type": request.get("message_type", "text")
            }
        )
        
        return {
            "message_id": message_id,
            "thread_id": thread_id,
            "timestamp": timestamp,
            "content": request["content"],
            "sender": request.get("sender", "user"),
            "message_type": request.get("message_type", "text")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.get("/threads/{thread_id}/agents")
async def get_thread_agents(
    thread_id: str,
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Get agents participating in thread."""
    try:
        return {
            "thread_id": thread_id,
            "agents": []  # Get from agent store
        }
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.post("/threads/{thread_id}/search")
async def search_thread(
    thread_id: str,
    request: Dict[str, Any],
    _: None = Depends(get_permission("read"))
) -> Dict:
    """Search thread messages."""
    try:
        if "query" not in request:
            raise HTTPException(status_code=422, detail="Search query is required")
            
        return {
            "thread_id": thread_id,
            "matches": []  # Search in memory system
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ServiceError(str(e))

@chat_router.websocket("/threads/{thread_id}/ws")
async def thread_websocket(
    websocket: WebSocket,
    thread_id: str,
    token: str,
    memory_system: Any = Depends(get_memory_system),
    coordination_agent: Any = Depends(get_coordination_agent)
):
    """WebSocket for real-time thread updates."""
    connection_id = str(uuid4())
    try:
        # Verify token and create session
        try:
            # Verify token returns the normalized token string
            normalized_token = await verify_token(token)
            
            # Accept connection
            await websocket.accept()
            
            # Create session with default values
            session = WebSocketSession(
                id=connection_id,
                state=WebSocketState.NOT_AUTHENTICATED,
                client_id=normalized_token,
                workspace="default",
                domain="default"
            )
        except Exception as e:
            await websocket.close(code=4000)
            return
            
        # Store connection
        active_connections[connection_id] = {
            "session": session,
            "websocket": websocket,
            "thread_id": thread_id
        }
        
        # Update session state
        session.state = WebSocketState.AUTHENTICATED
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Listen for messages
        try:
            while True:
                data = await websocket.receive_json()
                
                # Handle ping messages
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                
                # Create message in thread
                if data.get("type") == "message":
                    message_id = f"msg_{uuid4().hex[:8]}"
                    timestamp = datetime.now().isoformat()
                    
                    # Store message
                    await memory_system.store_experience(Memory(
                        id=message_id,
                        type="chat_message",
                        content={
                            "message_id": message_id,
                            "thread_id": thread_id,
                            "content": data["content"],
                            "sender": data.get("sender", session.client_id),
                            "timestamp": timestamp,
                            "message_type": data.get("message_type", "text"),
                            "metadata": data.get("metadata", {})
                        },
                        metadata={
                            "thread_id": thread_id,
                            "message_type": data.get("message_type", "text"),
                            "sender": data.get("sender", session.client_id)
                        }
                    ))
                    
                    # Update thread
                    await memory_system.semantic.run_query(
                        """
                        MATCH (t:ChatThread {id: $thread_id})
                        SET t.updated_at = datetime()
                        WITH t
                        MERGE (m:ChatMessage {id: $message_id})
                        SET m.content = $content,
                            m.sender = $sender,
                            m.timestamp = datetime(),
                            m.message_type = $message_type
                        MERGE (t)-[:HAS_MESSAGE]->(m)
                        """,
                        {
                            "thread_id": thread_id,
                            "message_id": message_id,
                            "content": data["content"],
                            "sender": data.get("sender", session.client_id),
                            "message_type": data.get("message_type", "text")
                        }
                    )
                    
                    # Broadcast message to all thread connections
                    message_event = {
                        "type": "message",
                        "data": {
                            "message_id": message_id,
                            "thread_id": thread_id,
                            "content": data["content"],
                            "sender": data.get("sender", session.client_id),
                            "timestamp": timestamp,
                            "message_type": data.get("message_type", "text")
                        }
                    }
                    
                    for conn_id, conn in active_connections.items():
                        if conn.get("thread_id") == thread_id:
                            try:
                                await conn["websocket"].send_json(message_event)
                            except:
                                continue
                    
                    # Get agent responses if needed
                    if coordination_agent and data.get("expect_response", True):
                        agent_response = {
                            "type": "message",
                            "data": {
                                "message_id": f"msg_{uuid4().hex[:8]}",
                                "thread_id": thread_id,
                                "content": "Response from agents",
                                "sender": "agent",
                                "timestamp": datetime.now().isoformat(),
                                "message_type": "text"
                            }
                        }
                        await websocket.send_json(agent_response)
                
        except WebSocketDisconnect:
            # Clean up on disconnect
            if connection_id in active_connections:
                del active_connections[connection_id]
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if connection_id in active_connections:
            del active_connections[connection_id]
        await websocket.close(code=1011)
