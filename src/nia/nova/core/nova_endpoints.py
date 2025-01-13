"""Nova-specific endpoints."""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import uuid

from .dependencies import get_memory_system
from .auth import get_permission
from .error_handling import ServiceError
from .models import Message, MessageResponse
from nia.core.types.memory_types import Memory, MemoryType

nova_router = APIRouter(
    prefix="/api/nova",
    tags=["Nova"],
    dependencies=[Depends(get_permission("write"))]
)

@nova_router.post("/ask", response_model=Dict[str, Any])
async def ask_nova(
    request: Dict[str, str],
    _: None = Depends(get_permission("write")),
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Ask Nova a question."""
    try:
        # Check if Nova thread exists
        result = await memory_system.query_episodic({
            "content": {},
            "filter": {
                "metadata.thread_id": "nova",
                "metadata.type": "thread"
            },
            "layer": "episodic"
        })
        
        if not result:
            # Create Nova thread if it doesn't exist
            now = datetime.now().isoformat()
            thread = {
                "id": "nova",
                "title": "Nova Chat",
                "domain": "general",
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "workspace": "personal",
                "metadata": {
                    "type": "agent-team",
                    "system": True,
                    "pinned": True,
                    "description": "Chat with Nova"
                }
            }
            
            # Store thread in memory system
            memory = Memory(
                content={
                    "data": thread,
                    "metadata": {
                        "type": "thread",
                        "domain": "general",
                        "thread_id": "nova",
                        "timestamp": now,
                        "id": "nova"
                    }
                },
                type=MemoryType.EPISODIC,
                importance=0.8,
                context={
                    "domain": "general",
                    "thread_id": "nova",
                    "source": "nova"
                }
            )
            await memory_system.episodic.store_memory(memory)
            
            # Verify thread was stored
            result = await memory_system.query_episodic({
                "content": {},
                "filter": {
                    "metadata.thread_id": "nova",
                    "metadata.type": "thread"
                },
                "layer": "episodic"
            })
            
            if not result:
                raise ServiceError("Failed to store Nova thread")
        
        thread = result[0]["content"]["data"] if result else thread
        
        # Create Nova's response
        message = Message(
            id=str(uuid.uuid4()),
            content=f"I understand you're asking about: {request['content']}. Let me help with that.",
            sender_type="agent",
            sender_id="nova",
            timestamp=datetime.now().isoformat(),
            metadata={}
        )
        
        # Add message to thread
        thread["messages"].append(message.dict())
        thread["updated_at"] = datetime.now().isoformat()
        
        # Update thread in memory system
        memory = Memory(
            content={
                "data": thread,
                "metadata": {
                    "type": "thread",
                    "domain": "general",
                    "thread_id": "nova",
                    "timestamp": datetime.now().isoformat(),
                    "id": "nova"
                }
            },
            type=MemoryType.EPISODIC,
            importance=0.8,
            context={
                "domain": "general",
                "thread_id": "nova",
                "source": "nova"
            }
        )
        await memory_system.episodic.store_memory(memory)
        
        return {
            "threadId": "nova",
            "message": message
        }
    except Exception as e:
        raise ServiceError(str(e))
