"""Thread management functionality for CoordinationAgent."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import Memory

class ThreadManagement:
    """Mixin class for thread management capabilities."""
    
    async def create_thread(
        self,
        thread_id: str,
        task_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new thread."""
        # Store thread in memory system
        thread_data = {
            "thread_id": thread_id,
            "task_id": task_id,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "sub_threads": [],
            "domain": domain or self.domain,
            "metadata": metadata or {}
        }
        
        await self.memory_system.episodic.store_memory(
            Memory(
                content=thread_data,
                type="thread",
                importance=0.8,
                context={
                    "domain": domain or self.domain,
                    "thread_id": thread_id,
                    "task_id": task_id
                }
            )
        )
        
        return thread_data
        
    async def get_thread(
        self,
        thread_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Get thread details."""
        # Search for thread in memory system
        results = await self.memory_system.query_episodic({
            "content": {
                "thread_id": thread_id,
                "type": "thread"
            },
            "filter": {
                "domain": domain or self.domain
            }
        })
        
        if not results:
            raise ValueError(f"Thread {thread_id} not found")
            
        return results[0].dict()
        
    async def get_messages(
        self,
        thread_id: str,
        start: int = 0,
        limit: int = 100,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Get messages from a thread with pagination."""
        # Search for messages in memory system
        results = await self.memory_system.query_episodic({
            "content": {
                "thread_id": thread_id,
                "type": "message"
            },
            "filter": {
                "domain": domain or self.domain
            }
        })
        
        # Sort by timestamp and apply pagination
        messages = sorted(
            [r.dict() for r in results],
            key=lambda x: x["created_at"]
        )
        
        return messages[start:start + limit]
        
    async def get_sub_threads(
        self,
        thread_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Get sub-threads of a thread."""
        # Search for sub-threads in memory system
        results = await self.memory_system.query_episodic({
            "content": {
                "parent_thread_id": thread_id,
                "type": "thread"
            },
            "filter": {
                "domain": domain or self.domain
            }
        })
        
        return [r.dict() for r in results]
        
    async def get_thread_summary(
        self,
        thread_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Get aggregated summary of a thread."""
        # Get thread messages
        messages = await self.get_messages(
            thread_id=thread_id,
            domain=domain,
            metadata=metadata
        )
        
        # Get sub-threads
        sub_threads = await self.get_sub_threads(
            thread_id=thread_id,
            domain=domain,
            metadata=metadata
        )
        
        # Generate summary using LLM if available
        summary_text = "Thread summary not available"
        if hasattr(self, 'llm') and self.llm:
            try:
                # Prepare messages for summarization
                message_texts = [
                    f"{msg['created_at']}: {msg['content']}"
                    for msg in messages
                ]
                
                # Get summary from LLM
                summary_text = await self.llm.summarize(
                    "\n".join(message_texts),
                    max_length=200
                )
            except Exception as e:
                summary_text = f"Error generating summary: {str(e)}"
        
        return {
            "thread_id": thread_id,
            "message_count": len(messages),
            "sub_thread_count": len(sub_threads),
            "summary": summary_text,
            "last_updated": datetime.now().isoformat()
        }
        
    async def post_message(
        self,
        thread_id: str,
        message_id: str,
        content: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Post a message to a thread."""
        # Create message data
        message_data = {
            "message_id": message_id,
            "thread_id": thread_id,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "domain": domain or self.domain,
            "metadata": metadata or {}
        }
        
        # Store message in memory system
        await self.memory_system.episodic.store_memory(
            Memory(
                content=message_data,
                type="message",
                importance=0.6,
                context={
                    "domain": domain or self.domain,
                    "thread_id": thread_id,
                    "message_id": message_id
                }
            )
        )
        
        # Update thread message count
        thread = await self.get_thread(thread_id, domain)
        thread["message_count"] += 1
        
        # Store updated thread
        await self.memory_system.episodic.store_memory(
            Memory(
                content=thread,
                type="thread",
                importance=0.8,
                context={
                    "domain": domain or self.domain,
                    "thread_id": thread_id
                }
            )
        )
        
        return message_data
