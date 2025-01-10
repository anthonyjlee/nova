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
        # Create a new thread for the conversation
        thread_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Create Nova's response
        message = Message(
            id=str(uuid.uuid4()),
            content=f"I understand you're asking about: {request['content']}. Let me help with that.",
            sender_type="agent",
            sender_id="nova",
            timestamp=now,
            metadata={}
        )
        
        # Create thread with the message
        thread = {
            "id": thread_id,
            "title": "Nova Chat",
            "domain": "general",
            "messages": [message.dict()],
            "created_at": now,
            "updated_at": now,
            "metadata": {}
        }
        
        # Store thread in memory system
        memory = Memory(
            content={
                "data": thread,
                "metadata": {
                    "type": "thread",
                    "domain": "general",
                    "thread_id": thread_id,
                    "timestamp": now,
                    "id": thread_id
                }
            },
            type=MemoryType.EPISODIC,
            importance=0.8,
            context={
                "domain": "general",
                "thread_id": thread_id,
                "source": "nova"
            }
        )
        await memory_system.store_experience(memory)
        
        return {
            "threadId": thread_id,
            "message": message
        }
    except Exception as e:
        raise ServiceError(str(e))
