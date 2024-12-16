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
                # Load recent memories using semantic search
                # Use a more meaningful query to find important memories
                query = "important core memories about identity goals and relationships"
                query_vector = await self.embedding_service.get_embedding(query)
                
                recent_memories = await self.vector_store.search_vectors(
                    query_vector=query_vector,
                    k=self.short_term_limit * 2  # Get more memories initially
                )
                
                # Also get recent interactions specifically
                interaction_query = "recent interactions and conversations"
                interaction_vector = await self.embedding_service.get_embedding(interaction_query)
                
                interaction_memories = await self.vector_store.search_vectors(
                    query_vector=interaction_vector,
                    k=self.short_term_limit,
                    filter_dict={'memory_type': 'interaction'}
                )
                
                # Combine and deduplicate memories
                all_memories = []
                seen_ids = set()
                
                for memory in recent_memories + interaction_memories:
                    memory_id = memory.get('id')
                    if memory_id not in seen_ids:
                        seen_ids.add(memory_id)
                        all_memories.append(memory)
                
                # Sort memories by type
                for memory in all_memories:
                    metadata = memory.get('metadata', {})
                    memory_type = metadata.get('memory_type', '')
                    if memory_type in ['interaction', 'experience']:
                        self.short_term_memory['episodic'].append(metadata)
                    else:
                        self.short_term_memory['semantic'].append(metadata)
                
                # Sort memories by timestamp
                for category in ['episodic', 'semantic']:
                    self.short_term_memory[category] = self._sort_memories_by_time(
                        self.short_term_memory[category]
                    )[:self.short_term_limit]
                
                # Build initial context from memories
                self._update_context_from_memories(all_memories)
                
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
                        if isinstance(beliefs, dict):
                            if 'core_belief' in beliefs:
                                context.setdefault('beliefs', []).append(str(beliefs['core_belief']))
                            if 'supporting_evidence' in beliefs:
                                evidence = beliefs['supporting_evidence']
                                if isinstance(evidence, list):
                                    context.setdefault('evidence', []).extend(str(e) for e in evidence)
                    
                    # Store key insights
                    if 'reflections' in content:
                        reflections = content['reflections']
                        if isinstance(reflections, dict):
                            if 'key_insights' in reflections:
                                insights = reflections['key_insights']
                                if isinstance(insights, list):
                                    context.setdefault('insights', []).extend(str(i) for i in insights)
                    
                    # Store research findings
                    if 'research' in content:
                        research = content['research']
                        if isinstance(research, dict):
                            if 'recent_developments' in research:
                                findings = research['recent_developments']
                                if isinstance(findings, list):
                                    context.setdefault('findings', []).extend(str(f) for f in findings)
                    
                    # Store interaction content
                    if 'input' in content:
                        interaction = {
                            'input': str(content['input']),
                            'timestamp': str(metadata.get('timestamp', '')),
                            'type': str(metadata.get('memory_type', ''))
                        }
                        context.setdefault('interactions', []).append(interaction)
            
            # Sort and deduplicate lists
            for key in context:
                if isinstance(context[key], list):
                    if key == 'interactions':
                        # Sort interactions by timestamp
                        context[key].sort(key=lambda x: x['timestamp'], reverse=True)
                        # Keep only unique interactions based on input
                        seen = set()
                        unique = []
                        for item in context[key]:
                            if item['input'] not in seen:
                                seen.add(item['input'])
                                unique.append(item)
                        context[key] = unique[:5]  # Keep last 5 unique interactions
                    else:
                        # For other lists, convert to strings for deduplication
                        unique = []
                        seen = set()
                        for item in context[key]:
                            item_str = str(item)
                            if item_str not in seen:
                                seen.add(item_str)
                                unique.append(item)
                        context[key] = unique[-5:]  # Keep last 5 unique items
            
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
                # Use semantic search to find interactions
                query = "most recent interaction or conversation"
                query_vector = await self.embedding_service.get_embedding(query)
                
                long_term_results = await self.vector_store.search_vectors(
                    query_vector=query_vector,
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
                
                # Use semantic search to find relevant memories
                query = f"important {memory_type if memory_type else 'memories'}"
                if agent_name:
                    query += f" from {agent_name}"
                query_vector = await self.embedding_service.get_embedding(query)
                
                # Search vector store
                long_term_results = await self.vector_store.search_vectors(
                    query_vector=query_vector,
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
                    
                    # Add importance boost if present
                    if memory.get('importance', 0.5) > 0.5:
                        similarity *= 1.2
                    
                    short_term_results.append({
                        'memory': memory,
                        'similarity': similarity
                    })
            
            # Sort short-term results by similarity
            short_term_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Get results from long-term storage with increased limit
            long_term_results = await self.vector_store.search_vectors(
                query_vector=embedding,
                k=limit * 2,  # Get more results to account for filtering
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
                if len(all_results) >= limit * 2:  # Allow more results initially
                    break
                metadata = result['metadata']
                
                # Apply importance boost if present
                similarity = result['score']
                if metadata.get('importance', 0.5) > 0.5:
                    similarity *= 1.2
                
                all_results.append({
                    'id': result['id'],
                    'content': metadata['content'],
                    'agent_name': metadata['agent_name'],
                    'memory_type': metadata['memory_type'],
                    'timestamp': metadata['timestamp'],
                    'time_ago': self._format_time_difference(metadata['timestamp']),
                    'similarity': similarity
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
