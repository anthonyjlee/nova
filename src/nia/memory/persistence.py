"""
Memory persistence and retrieval using Qdrant.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
from dateutil import parser
from dateutil.relativedelta import relativedelta

from .vector_store import VectorStore
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class MemoryStore:
    """Handles memory persistence and retrieval using Qdrant."""
    
    def __init__(self, collection_name: str = "memory_vectors"):
        """Initialize store with Qdrant connection."""
        # Short-term memory (episodic and semantic)
        self.short_term_memory: Dict[str, List[Dict]] = {
            'episodic': [],  # Recent experiences and interactions
            'semantic': []   # Processed knowledge and understanding
        }
        self.short_term_limit = 10  # Keep last 10 memories in short-term
        
        # Long-term memory (Qdrant vector store)
        self.vector_store = VectorStore(collection_name=collection_name)
        self.embedding_service = EmbeddingService()
        
        # Load existing memories into short-term memory
        self.initialized = False
        
        # Track current context
        self.current_context: Dict[str, Any] = {}
    
    async def initialize(self):
        """Initialize vector store and load existing memories."""
        try:
            # Initialize vector store
            await self.vector_store.init_collection()
            
            if not self.initialized:
                # Load recent memories into short-term memory
                recent_memories = await self.vector_store.search_vectors(
                    query_vector=np.zeros(1024),  # Dummy vector for initial search
                    k=self.short_term_limit
                )
                
                # Sort memories by type
                for memory in recent_memories:
                    metadata = memory.get('metadata', {})
                    memory_type = metadata.get('memory_type', '')
                    if memory_type in ['interaction', 'experience']:
                        self.short_term_memory['episodic'].append(metadata)
                    else:
                        self.short_term_memory['semantic'].append(metadata)
                
                # Build initial context from memories
                self._update_context_from_memories(recent_memories)
                
                self.initialized = True
                logger.info("Loaded existing memories into short-term memory")
            
        except Exception as e:
            logger.error(f"Error initializing memory store: {str(e)}")
            raise
    
    def _update_context_from_memories(self, memories: List[Dict]) -> None:
        """Update current context from memories."""
        try:
            context = {}
            
            # Extract key information from memories
            for memory in memories:
                metadata = memory.get('metadata', {})
                content = metadata.get('content', {})
                
                # Track important information
                if isinstance(content, dict):
                    # Store beliefs
                    if 'beliefs' in content:
                        beliefs = content['beliefs']
                        if 'core_belief' in beliefs:
                            context.setdefault('beliefs', []).append(beliefs['core_belief'])
                    
                    # Store key insights
                    if 'reflections' in content:
                        reflections = content['reflections']
                        if 'key_insights' in reflections:
                            context.setdefault('insights', []).extend(reflections['key_insights'])
                    
                    # Store research findings
                    if 'research' in content:
                        research = content['research']
                        if 'recent_developments' in research:
                            context.setdefault('findings', []).extend(research['recent_developments'])
            
            # Update current context
            self.current_context.update(context)
            
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
    
    def _format_time_difference(self, timestamp: str) -> str:
        """Format time difference between now and timestamp."""
        try:
            past_time = parser.parse(timestamp)
            now = datetime.now()
            diff = relativedelta(now, past_time)
            
            if diff.years > 0:
                return f"{diff.years} years"
            elif diff.months > 0:
                return f"{diff.months} months"
            elif diff.days > 0:
                return f"{diff.days} days"
            elif diff.hours > 0:
                return f"{diff.hours} hours"
            elif diff.minutes > 0:
                return f"{diff.minutes} minutes"
            else:
                return "just now"
        except Exception as e:
            logger.error(f"Error formatting time difference: {str(e)}")
            return "unknown time"
    
    async def store_memory(self, agent_name: str, memory_type: str,
                          content: Dict[str, Any], metadata: Optional[Dict] = None) -> None:
        """Store a memory in both short-term and long-term storage."""
        try:
            # Create memory object with flattened metadata
            memory = {
                'content': content,
                'agent_name': agent_name,
                'memory_type': memory_type,
                'timestamp': datetime.now().isoformat()
            }
            if metadata:
                memory.update(metadata)
            
            # Store in short-term memory
            memory_category = 'episodic' if memory_type in ['interaction', 'experience'] else 'semantic'
            self.short_term_memory[memory_category].append(memory)
            
            # Trim short-term memory if needed
            if len(self.short_term_memory[memory_category]) > self.short_term_limit:
                # Move oldest memory to long-term storage
                oldest_memory = self.short_term_memory[memory_category].pop(0)
                await self._store_in_long_term(oldest_memory)
            
            # Also store current memory in long-term storage
            await self._store_in_long_term(memory)
            
            # Update context with new memory
            self._update_context_from_memories([{'metadata': memory}])
            
            logger.info(f"Stored {memory_type} memory for {agent_name}")
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
    
    async def _store_in_long_term(self, memory: Dict) -> None:
        """Store memory in long-term storage (Qdrant)."""
        try:
            # Get embedding for content
            content_str = json.dumps(memory['content'])  # Convert content to string for embedding
            embedding = await self.embedding_service.get_embedding(content_str)
            
            # Store in vector store
            await self.vector_store.add_vectors(
                vectors=[embedding],
                metadata_list=[memory]
            )
            
        except Exception as e:
            logger.error(f"Error storing in long-term memory: {str(e)}")
            raise
    
    def _sort_memories_by_time(self, memories: List[Dict], reverse: bool = True) -> List[Dict]:
        """Sort memories by timestamp."""
        try:
            return sorted(memories, 
                         key=lambda x: parser.parse(x.get('timestamp', '1970-01-01T00:00:00')),
                         reverse=reverse)
        except Exception as e:
            logger.error(f"Error sorting memories: {str(e)}")
            return memories
    
    async def get_last_interaction_time(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the timestamp and formatted time difference of the last interaction."""
        try:
            # Check short-term memory first
            recent_memories = []
            for memory in self.short_term_memory['episodic']:
                if memory.get('memory_type') == 'interaction':
                    recent_memories.append(memory)
            
            # Check long-term memory if needed
            if not recent_memories:
                long_term_results = await self.vector_store.search_vectors(
                    query_vector=await self.embedding_service.get_embedding("last interaction"),
                    k=1,
                    filter_dict={'memory_type': 'interaction'}
                )
                if long_term_results:
                    recent_memories.append(long_term_results[0]['metadata'])
            
            if recent_memories:
                sorted_memories = self._sort_memories_by_time(recent_memories)
                if sorted_memories:
                    timestamp = sorted_memories[0].get('timestamp')
                    if timestamp:
                        return timestamp, self._format_time_difference(timestamp)
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting last interaction time: {str(e)}")
            return None, None
    
    async def get_recent_memories(self, agent_name: Optional[str] = None,
                                memory_type: Optional[str] = None,
                                limit: int = 5) -> List[Dict]:
        """Get recent memories from both short-term and long-term storage."""
        try:
            # Get memories from short-term storage
            memories = []
            for category in ['episodic', 'semantic']:
                for memory in reversed(self.short_term_memory[category]):
                    if len(memories) >= limit:
                        break
                    if (not agent_name or memory['agent_name'] == agent_name) and \
                       (not memory_type or memory['memory_type'] == memory_type):
                        memories.append(memory)
            
            # If we need more memories, get them from long-term storage
            if len(memories) < limit:
                remaining_limit = limit - len(memories)
                # Build filter
                filter_dict = {}
                if agent_name:
                    filter_dict['agent_name'] = agent_name
                if memory_type:
                    filter_dict['memory_type'] = memory_type
                
                # Get current time for recency search
                current_time = datetime.now().isoformat()
                dummy_vector = await self.embedding_service.get_embedding(current_time)
                
                # Search vector store
                long_term_results = await self.vector_store.search_vectors(
                    query_vector=dummy_vector,
                    k=remaining_limit,
                    filter_dict=filter_dict if filter_dict else None
                )
                
                # Add long-term memories
                for result in long_term_results:
                    if result['metadata'] not in memories:  # Avoid duplicates
                        memories.append(result['metadata'])
            
            # Sort by timestamp
            memories = self._sort_memories_by_time(memories)
            
            # Add time_ago field
            for memory in memories:
                memory['time_ago'] = self._format_time_difference(memory.get('timestamp', ''))
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    async def search_similar_memories(self, content: str, limit: int = 5,
                                    filter_dict: Optional[Dict] = None,
                                    prioritize_temporal: bool = False) -> List[Dict]:
        """Search for semantically similar memories in both storages."""
        try:
            # Get embedding for content
            embedding = await self.embedding_service.get_embedding(content)
            
            # First, search in short-term memory
            short_term_results = []
            for category in ['episodic', 'semantic']:
                for memory in self.short_term_memory[category]:
                    if filter_dict:
                        # Apply filters
                        matches = all(memory.get(k) == v for k, v in filter_dict.items())
                        if not matches:
                            continue
                    
                    # Get embedding for memory content
                    memory_content = json.dumps(memory['content'])
                    memory_embedding = await self.embedding_service.get_embedding(memory_content)
                    
                    # Calculate similarity
                    similarity = float(np.dot(embedding, memory_embedding) / 
                                    (np.linalg.norm(embedding) * np.linalg.norm(memory_embedding)))
                    
                    # Add temporal boost if needed
                    if prioritize_temporal:
                        try:
                            time_diff = datetime.now() - parser.parse(memory.get('timestamp', ''))
                            # Boost recent memories (within last hour)
                            if time_diff <= timedelta(hours=1):
                                similarity *= 1.5
                        except Exception:
                            pass
                    
                    short_term_results.append({
                        'memory': memory,
                        'similarity': similarity
                    })
            
            # Sort short-term results by similarity
            short_term_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Get results from long-term storage
            long_term_results = await self.vector_store.search_vectors(
                query_vector=embedding,
                k=limit,
                filter_dict=filter_dict
            )
            
            # Combine and sort results
            all_results = []
            
            # Add short-term results
            for result in short_term_results[:limit]:
                memory = result['memory']
                all_results.append({
                    'id': 'short_term',
                    'content': memory['content'],
                    'agent_name': memory['agent_name'],
                    'memory_type': memory['memory_type'],
                    'timestamp': memory['timestamp'],
                    'time_ago': self._format_time_difference(memory['timestamp']),
                    'similarity': result['similarity']
                })
            
            # Add long-term results
            for result in long_term_results:
                if len(all_results) >= limit:
                    break
                metadata = result['metadata']
                all_results.append({
                    'id': result['id'],
                    'content': metadata['content'],
                    'agent_name': metadata['agent_name'],
                    'memory_type': metadata['memory_type'],
                    'timestamp': metadata['timestamp'],
                    'time_ago': self._format_time_difference(metadata['timestamp']),
                    'similarity': result['score']
                })
            
            # Sort results
            if prioritize_temporal:
                # Sort by recency first, then similarity
                all_results.sort(key=lambda x: (
                    parser.parse(x['timestamp']),
                    x['similarity']
                ), reverse=True)
            else:
                # Sort by similarity only
                all_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current context built from memories."""
        return self.current_context
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            # Clear short-term memory
            self.short_term_memory = {
                'episodic': [],
                'semantic': []
            }
            
            # Clear long-term storage
            await self.vector_store.clear_collection()
            
            # Reset context
            self.current_context = {}
            
            # Reset initialization flag
            self.initialized = False
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise
