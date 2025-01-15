"""Thread management functionality for CoordinationAgent."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import Memory

logger = logging.getLogger(__name__)

class ThreadManagement:
    """Mixin class for thread management capabilities."""
    
    async def _check_thread_exists(
        self,
        thread_id: str,
        domain: Optional[str] = None
    ) -> tuple[Optional[Dict], str]:
        """Check if a thread exists in either memory layer.
        
        Returns:
            Tuple of (thread_data, location) where location is:
            - "both" if found in both layers
            - "semantic" if only in semantic layer
            - "episodic" if only in episodic layer
            - "none" if not found
        """
        semantic_thread = None
        episodic_thread = None
        
        try:
            # Check semantic layer first
            if self.memory_system.semantic:
                try:
                    result = await self.memory_system.semantic.run_query(
                        """
                        MATCH (t:Thread {id: $id})
                        RETURN t
                        """,
                        {"id": thread_id}
                    )
                    if result and result[0]:
                        semantic_thread = result[0]["t"]
                        logger.debug(f"Thread {thread_id} found in semantic layer")
                except Exception as e:
                    logger.warning(f"Error checking semantic layer: {str(e)}")
            
            # Check episodic layer
            try:
                results = await self.memory_system.query_episodic({
                    "content": {
                        "thread_id": thread_id,
                        "type": "thread"
                    },
                    "filter": {
                        "domain": domain or self.domain
                    },
                    "limit": 1
                })
                if results:
                    episodic_thread = results[0].content
                    logger.debug(f"Thread {thread_id} found in episodic layer")
            except Exception as e:
                logger.warning(f"Error checking episodic layer: {str(e)}")
            
            # Determine location and return appropriate data
            if semantic_thread and episodic_thread:
                return semantic_thread, "both"
            elif semantic_thread:
                return semantic_thread, "semantic"
            elif episodic_thread:
                return episodic_thread, "episodic"
            else:
                return None, "none"
                
        except Exception as e:
            logger.error(f"Error in _check_thread_exists: {str(e)}")
            return None, "error"

    async def _store_thread(
        self,
        thread_data: Dict,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None,
        skip_semantic: bool = False,
        is_sync: bool = False  # Flag to indicate if this is a sync operation
    ) -> bool:
        """Store thread data in memory layers."""
        try:
            thread_id = thread_data["thread_id"]
            
            # Only store in episodic if not syncing or explicitly requested
            if not is_sync or not skip_semantic:
                # Create memory object with minimal metadata to avoid recursion
                memory = Memory(
                    id=thread_id,
                    content=thread_data,
                    type="thread",
                    importance=0.8,
                    context={
                        "domain": domain or self.domain,
                        "thread_id": thread_id,
                        "task_id": thread_data.get("task_id")
                    },
                    metadata={
                        "type": "thread",
                        **(metadata or {})
                    }
                )
                
                success = await self.memory_system.store_experience(memory)
                if not success:
                    logger.error(f"Failed to store thread {thread_id} in episodic layer")
                    return False
            
            # Store in semantic layer if available and not skipped
            if self.memory_system.semantic and not skip_semantic:
                try:
                    # Store minimal data in Neo4j to avoid recursion
                    await self.memory_system.semantic.run_query(
                        """
                        MERGE (t:Thread {id: $id})
                        SET t.thread_id = $thread_id,
                            t.task_id = $task_id,
                            t.status = $status,
                            t.created_at = $created_at,
                            t.message_count = $message_count,
                            t.domain = $domain
                        """,
                        {
                            "id": thread_id,
                            "thread_id": thread_id,
                            "task_id": thread_data.get("task_id"),
                            "status": thread_data.get("status", "active"),
                            "created_at": thread_data.get("created_at"),
                            "message_count": thread_data.get("message_count", 0),
                            "domain": domain or self.domain
                        }
                    )
                    logger.debug(f"Stored thread {thread_id} in semantic layer")
                except Exception as e:
                    logger.error(f"Failed to store thread {thread_id} in semantic layer: {str(e)}")
                    if not is_sync:  # Only return False if this is not a sync operation
                        return False
                    
            return True
        except Exception as e:
            logger.error(f"Error in _store_thread: {str(e)}")
            return False

    async def create_thread(
        self,
        thread_id: str,
        task_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict:
        """Create a new thread."""
        # Check if thread exists
        existing_thread, location = await self._check_thread_exists(thread_id, domain)
        
        if existing_thread:
            logger.info(f"Thread {thread_id} already exists in {location} layer(s)")
            if location in ["semantic", "episodic"]:
                # Sync to missing layer if needed
                try:
                    await self._store_thread(
                        existing_thread,
                        domain=domain,
                        metadata=metadata,
                        skip_semantic=(location == "episodic"),
                        is_sync=True  # Mark as sync operation
                    )
                except Exception as e:
                    logger.warning(f"Failed to sync thread {thread_id}: {str(e)}")
            return existing_thread
            
            # Create minimal thread data
            thread_data = {
                "thread_id": thread_id,
                "task_id": task_id,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "domain": domain or self.domain
            }
            
            # Store thread with progressive fallback
            logger.info(f"Creating new thread {thread_id}")
            success = False
            last_error = None
            
            # Try storing with retries
            for attempt in range(max_retries):
                try:
                    success = await self._store_thread(
                        thread_data,
                        domain=domain,
                        metadata=metadata,
                        skip_semantic=(attempt > 0)  # Only try semantic on first attempt
                    )
                    if success:
                        return thread_data
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Error storing thread on attempt {attempt + 1}: {last_error}")
                    if attempt < max_retries - 1:
                        continue
                    
        error_msg = f"Failed to store thread {thread_id} after {max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        raise ValueError(error_msg)

    async def get_thread(
        self,
        thread_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None,
        max_retries: int = 3,
        sync_layers: bool = True
    ) -> Dict:
        """Get thread details."""
        # Check thread existence
        thread_data, location = await self._check_thread_exists(thread_id, domain)
        
        if not thread_data:
            logger.error(f"Thread {thread_id} not found in any layer")
            raise ValueError(f"Thread {thread_id} not found")
            
        # Only attempt sync if explicitly requested and we have semantic layer
        if sync_layers and location != "both" and self.memory_system.semantic:
            logger.warning(f"Thread {thread_id} found only in {location} layer")
            try:
                # Use optimized store with sync flag
                await self._store_thread(
                    thread_data,
                    domain=domain,
                    metadata=metadata,
                    skip_semantic=(location == "episodic"),
                    is_sync=True  # Mark as sync operation
                )
                logger.info(f"Synced thread {thread_id} to {'episodic' if location == 'semantic' else 'semantic'} layer")
            except Exception as e:
                logger.warning(f"Failed to sync thread {thread_id}: {str(e)}")
                
        return thread_data
        
    async def get_messages(
        self,
        thread_id: str,
        start: int = 0,
        limit: int = 100,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Get messages from a thread with pagination."""
        # First verify thread exists
        thread_data, location = await self._check_thread_exists(thread_id, domain)
        if not thread_data:
            logger.error(f"Thread {thread_id} not found in any layer")
            raise ValueError(f"Thread {thread_id} not found")
            
        # Query messages from episodic layer
        results = await self.memory_system.query_episodic({
            "content": {
                "thread_id": thread_id,
                "type": "message"
            },
            "filter": {
                "domain": domain or self.domain
            },
            "limit": limit,
            "score_threshold": 0.7
        })
        
        # Sort by timestamp and apply pagination
        messages = sorted(
            [r.content for r in results],
            key=lambda x: x["created_at"]
        )
        
        logger.debug(f"Retrieved {len(messages)} messages for thread {thread_id}")
        return messages[start:start + limit]
        
    async def get_sub_threads(
        self,
        thread_id: str,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None,
        max_retries: int = 3
    ) -> List[Dict]:
        """Get sub-threads of a thread."""
        # First verify parent thread exists
        parent_thread, location = await self._check_thread_exists(thread_id, domain)
        if not parent_thread:
            logger.error(f"Parent thread {thread_id} not found in any layer")
            raise ValueError(f"Parent thread {thread_id} not found")
            
        # Search for sub-threads in both layers
        sub_threads = []
        
        # Check semantic layer first
        if self.memory_system.semantic:
            try:
                result = await self.memory_system.semantic.run_query(
                    """
                    MATCH (p:Thread {id: $parent_id})<-[:SUB_THREAD]-(t:Thread)
                    RETURN t
                    """,
                    {"parent_id": thread_id}
                )
                if result:
                    sub_threads.extend([r["t"] for r in result])
                    logger.debug(f"Found {len(result)} sub-threads in semantic layer")
            except Exception as e:
                logger.warning(f"Error querying semantic layer for sub-threads: {str(e)}")
        
        # Query episodic layer
        try:
            results = await self.memory_system.query_episodic({
                "content": {
                    "parent_thread_id": thread_id,
                    "type": "thread"
                },
                "filter": {
                    "domain": domain or self.domain
                }
            })
            
            # Add any sub-threads not already found in semantic layer
            for r in results:
                thread_data = r.content
                if not any(st["thread_id"] == thread_data["thread_id"] for st in sub_threads):
                    sub_threads.append(thread_data)
                    
            logger.debug(f"Found {len(results)} sub-threads in episodic layer")
        except Exception as e:
            logger.warning(f"Error querying episodic layer for sub-threads: {str(e)}")
            
        # Sync sub-threads using optimized store
        if self.memory_system.semantic:
            for sub_thread in sub_threads:
                _, location = await self._check_thread_exists(sub_thread["thread_id"], domain)
                if location != "both":
                    try:
                        await self._store_thread(
                            sub_thread,
                            domain=domain,
                            metadata=metadata,
                            skip_semantic=(location == "episodic"),
                            is_sync=True  # Mark as sync operation
                        )
                        logger.info(f"Synced sub-thread {sub_thread['thread_id']} to {'episodic' if location == 'semantic' else 'semantic'} layer")
                    except Exception as e:
                        logger.warning(f"Failed to sync sub-thread {sub_thread['thread_id']}: {str(e)}")
                
        return sub_threads
        
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
        metadata: Optional[Dict] = None,
        max_retries: int = 3
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
        
        # Store message with retry logic
        for attempt in range(max_retries):
            success = await self.memory_system.store_experience(
                Memory(
                    id=message_id,
                    content=message_data,
                    type="message",
                    importance=0.6,
                    context={
                        "domain": domain or self.domain,
                        "thread_id": thread_id,
                        "message_id": message_id
                    },
                    metadata=metadata or {}
                )
            )
            if success:
                break
            if attempt < max_retries - 1:
                logger.warning(f"Message storage attempt {attempt + 1} failed, retrying...")
        else:
            raise ValueError(f"Failed to store message {message_id} after {max_retries} attempts")
        
        # Update thread message count with single attempt
        try:
            # Get thread state without syncing layers
            thread, location = await self._check_thread_exists(thread_id, domain)
            if thread:
                thread["message_count"] += 1
                
                # Update thread using optimized store
                await self._store_thread(
                    thread,
                    domain=domain,
                    metadata=metadata,
                    is_sync=True  # Mark as sync operation to avoid recursion
                )
                logger.info(f"Updated message count for thread {thread_id} to {thread['message_count']}")
        except Exception as e:
            logger.error(f"Failed to update thread message count: {str(e)}")
            
        return message_data
