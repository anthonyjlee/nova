"""
Memory system integration with clean separation between memories and concepts.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid

from .llm_interface import LLMInterface
from .neo4j_store import Neo4jMemoryStore
from .vector_store import VectorStore
from .memory_types import AgentResponse, Memory
from .agents import (
    BeliefAgent,
    DesireAgent,
    EmotionAgent,
    ReflectionAgent,
    ResearchAgent,
    MetaAgent
)

logger = logging.getLogger(__name__)

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in item]
    return obj

class MemorySystem:
    """Integrated memory system with clean concept separation."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: Optional[VectorStore] = None,
        consolidation_interval: timedelta = timedelta(hours=1)
    ):
        """Initialize memory system."""
        self.llm = llm
        self.store = store  # Neo4j for concepts only
        self.vector_store = vector_store or VectorStore()  # Qdrant for all memories
        self.consolidation_interval = consolidation_interval
        self.last_consolidation = datetime.now()
        
        # Initialize agents
        self.belief_agent = BeliefAgent(llm, store, self.vector_store)
        self.desire_agent = DesireAgent(llm, store, self.vector_store)
        self.emotion_agent = EmotionAgent(llm, store, self.vector_store)
        self.reflection_agent = ReflectionAgent(llm, store, self.vector_store)
        self.research_agent = ResearchAgent(llm, store, self.vector_store)
        self.meta_agent = MetaAgent(llm, store, self.vector_store)
    
    async def process_interaction(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process an interaction through the memory system."""
        try:
            # Check for memory consolidation
            await self._check_consolidation()
            
            # Generate UUID for memory ID
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Store in episodic memory (raw interaction)
            await self.vector_store.store_vector(
                content=serialize_datetime({
                    'content': content,
                    'timestamp': timestamp
                }),
                metadata=serialize_datetime({
                    'id': memory_id,
                    'type': 'interaction',
                    'layer': 'episodic',
                    **(metadata or {})
                }),
                layer="episodic"
            )
            
            # Find relevant memories from both layers
            similar_memories = await self._find_relevant_memories(content)
            
            # Process through agent system
            content_dict = {
                'content': content,
                'similar_memories': similar_memories
            }
            
            # Get agent responses
            responses = {}
            for agent_type, agent in [
                ('belief', self.belief_agent),
                ('desire', self.desire_agent),
                ('emotion', self.emotion_agent),
                ('reflection', self.reflection_agent),
                ('research', self.research_agent)
            ]:
                responses[agent_type] = await agent.process(content_dict, metadata)
                logger.info(f"{agent_type.capitalize()}Agent processed interaction")
            
            # Synthesize responses
            response = await self.meta_agent.synthesize_responses(
                responses=responses,
                context=serialize_datetime({
                    'original_content': content_dict,
                    'metadata': metadata,
                    'memory_id': memory_id,
                    'similar_memories': similar_memories
                })
            )
            
            # Store processed memory in semantic layer
            await self.vector_store.store_vector(
                content=serialize_datetime({
                    'content': content,
                    'memory_id': memory_id,
                    'similar_memories': similar_memories,
                    'response': response.dict(),
                    'timestamp': datetime.now()
                }),
                metadata=serialize_datetime({
                    'id': str(uuid.uuid4()),
                    'type': 'processed_memory',
                    'original_memory_id': memory_id,
                    **(metadata or {})
                }),
                layer="semantic"
            )
            
            # Store extracted concepts in knowledge graph
            for concept in response.concepts:
                # Store concept
                await self.store.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"]
                )
                
                # Store concept relationships
                for related in concept.get("related", []):
                    await self.store.store_concept_relationship(
                        concept["name"],
                        related,
                        "RELATED_TO"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            raise
    
    async def _check_consolidation(self):
        """Check and perform memory consolidation if needed."""
        now = datetime.now()
        if now - self.last_consolidation >= self.consolidation_interval:
            await self._consolidate_memories()
            self.last_consolidation = now
    
    async def _consolidate_memories(self):
        """Consolidate memories and extract concepts."""
        try:
            # Get recent memories
            recent_memories = await self.vector_store.search_vectors(
                content={'type': 'interaction'},
                start_time=self.last_consolidation,
                limit=100
            )
            
            if not recent_memories:
                return
            
            # Extract patterns and concepts
            consolidation_content = {
                'content': json.dumps(recent_memories),
                'type': 'consolidation'
            }
            
            # Process through reflection agent
            reflection = await self.reflection_agent.process(consolidation_content)
            
            # Store consolidated insights in semantic layer
            await self.vector_store.store_vector(
                content=serialize_datetime({
                    'type': 'consolidation',
                    'timestamp': datetime.now(),
                    'memories': [m.get('id') for m in recent_memories],
                    'insights': reflection.dict()
                }),
                metadata={'type': 'consolidation'},
                layer="semantic"
            )
            
            # Store extracted concepts
            for concept in reflection.concepts:
                await self.store.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"]
                )
                
                # Store concept relationships
                for related in concept.get("related", []):
                    await self.store.store_concept_relationship(
                        concept["name"],
                        related,
                        "RELATED_TO"
                    )
            
            logger.info(f"Consolidated {len(recent_memories)} memories")
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {str(e)}")
    
    async def _find_relevant_memories(
        self,
        content: str
    ) -> List[Dict[str, Any]]:
        """Find relevant memories from both layers."""
        # Search episodic memories
        episodic = await self.vector_store.search_vectors(
            content=serialize_datetime({'content': content}),
            layer="episodic",
            limit=3
        )
        
        # Search semantic memories
        semantic = await self.vector_store.search_vectors(
            content=serialize_datetime({'content': content}),
            layer="semantic",
            limit=3
        )
        
        # Combine and sort by relevance
        memories = episodic + semantic
        memories.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return memories[:5]  # Return top 5 most relevant
    
    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        include_episodic: bool = True,
        include_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Search memories across layers."""
        try:
            results = []
            
            # Search episodic memories if requested
            if include_episodic:
                episodic = await self.vector_store.search_vectors(
                    content=serialize_datetime({'content': query}),
                    layer="episodic",
                    limit=limit
                )
                results.extend([{**m, 'layer': 'episodic'} for m in episodic])
            
            # Search semantic memories if requested
            if include_semantic:
                semantic = await self.vector_store.search_vectors(
                    content=serialize_datetime({'content': query}),
                    layer="semantic",
                    limit=limit
                )
                results.extend([{**m, 'layer': 'semantic'} for m in semantic])
            
            # Sort by relevance and recency
            results.sort(
                key=lambda x: (
                    x.get('score', 0),
                    x.get('timestamp', datetime.min.isoformat())
                ),
                reverse=True
            )
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        try:
            # Get vector store status
            vector_status = await self.vector_store.get_status()
            
            # Get Neo4j status
            neo4j_status = {
                "connected": True,
                "error": None
            }
            try:
                await self.store.get_system_info("Nova")
            except Exception as e:
                neo4j_status = {
                    "connected": False,
                    "error": str(e)
                }
            
            # Get statistics
            stats = {
                "last_consolidation": self.last_consolidation.isoformat(),
                "episodic_count": await self.vector_store.count_vectors(layer="episodic"),
                "semantic_count": await self.vector_store.count_vectors(layer="semantic"),
                "concept_count": await self.store.count_concepts()
            }
            
            return {
                "vector_store": vector_status,
                "neo4j": neo4j_status,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Clean up memory system."""
        try:
            # Consolidate memories one last time
            await self._consolidate_memories()
            
            # Clean up stores
            await self.vector_store.cleanup()
            await self.store.cleanup()
            
            logger.info("Cleaned up memory system")
            
        except Exception as e:
            logger.error(f"Error cleaning up memory system: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close memory system."""
        try:
            self.vector_store.close()
            self.store.close()
            logger.info("Closed memory system")
        except Exception as e:
            logger.error(f"Error closing memory system: {str(e)}")
            raise
