"""
Memory system integration.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .llm_interface import LLMInterface
from .neo4j_store import Neo4jMemoryStore
from .vector_store import VectorStore
from .agents import (
    BeliefAgent,
    DesireAgent,
    EmotionAgent,
    ReflectionAgent,
    ResearchAgent,
    MetaAgent
)

logger = logging.getLogger(__name__)

class MemorySystem:
    """Integrated memory system."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: Optional[VectorStore] = None
    ):
        """Initialize memory system."""
        self.llm = llm
        self.store = store  # Neo4j for concepts/knowledge
        self.vector_store = vector_store or VectorStore()  # Qdrant for memories
        
        # Initialize agents with both stores
        self.belief_agent = BeliefAgent(llm, store, self.vector_store)
        self.desire_agent = DesireAgent(llm, store, self.vector_store)
        self.emotion_agent = EmotionAgent(llm, store, self.vector_store)
        self.reflection_agent = ReflectionAgent(llm, store, self.vector_store)
        self.research_agent = ResearchAgent(llm, store, self.vector_store)
        self.meta_agent = MetaAgent(llm, store, self.vector_store)
    
    async def process_interaction(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Any:
        """Process an interaction through the memory system."""
        try:
            # Store in episodic memory (raw interaction)
            episodic_id = await self.vector_store.store_vector(
                content=content,
                metadata=metadata,
                layer="episodic"
            )
            
            # Find similar memories from both layers
            similar_memories = await self.vector_store.search_vectors(
                content=content,
                limit=5
            )
            
            # Add similar memories to content
            if similar_memories:
                content['similar_memories'] = similar_memories
            
            # Extract concepts to knowledge graph
            await self.store.store_memory(
                memory_type="concept",
                content=content,
                metadata=metadata
            )
            
            # Process through belief system
            belief_response = await self.belief_agent.process(content, metadata)
            logger.info("BeliefAgent processed interaction")
            
            # Process through desire system
            desire_response = await self.desire_agent.process(content, metadata)
            logger.info("DesireAgent processed interaction")
            
            # Process through emotion system
            emotion_response = await self.emotion_agent.process(content, metadata)
            logger.info("EmotionAgent processed interaction")
            
            # Process through reflection system
            reflection_response = await self.reflection_agent.process(content, metadata)
            logger.info("ReflectionAgent processed interaction")
            
            # Process through research system
            research_response = await self.research_agent.process(content, metadata)
            logger.info("ResearchAgent processed interaction")
            
            # Synthesize responses
            response = await self.meta_agent.synthesize_responses(
                responses={
                    'belief': belief_response,
                    'desire': desire_response,
                    'emotion': emotion_response,
                    'reflection': reflection_response,
                    'research': research_response
                },
                context={
                    'original_content': content,
                    'metadata': metadata,
                    'episodic_id': episodic_id,
                    'similar_memories': similar_memories
                }
            )
            
            # Store synthesized response in semantic memory
            await self.vector_store.store_vector(
                content={
                    'original_content': str(content),
                    'metadata': str(metadata) if metadata else "",
                    'episodic_id': str(episodic_id),
                    'similar_memories': str(similar_memories),
                    'final_response': str(response.dict()),
                    'agent_responses': {
                        'belief': belief_response.dict(),
                        'desire': desire_response.dict(),
                        'emotion': emotion_response.dict(),
                        'reflection': reflection_response.dict(),
                        'research': research_response.dict()
                    }
                },
                metadata={'type': 'synthesized_response'},
                layer="semantic"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Get memory system status."""
        try:
            # Get vector store status
            vector_status = await self.vector_store.get_status()
            
            # Get Neo4j status
            neo4j_status = {
                "connected": True,
                "error": None
            }
            try:
                # Try to get system info as connection test
                await self.store.get_system_info("Nova")
            except Exception as e:
                neo4j_status = {
                    "connected": False,
                    "error": str(e)
                }
            
            return {
                "vector_store": vector_status,
                "neo4j": neo4j_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_memories(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories in vector store."""
        try:
            # Search both memory layers
            vector_results = await self.vector_store.search_vectors(
                content=query,
                limit=limit
            )
            
            # Add source and score
            results = []
            for result in vector_results:
                results.append({
                    'source': 'vector',
                    'layer': result.get('layer', 'unknown'),
                    'score': result.get('score', 0.0),
                    **result
                })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    async def cleanup(self) -> None:
        """Clean up memory system."""
        try:
            # Clean up vector store
            await self.vector_store.cleanup()
            logger.info("Cleaned up vector store")
            
            # Clean up graph store
            await self.store.cleanup()
            logger.info("Cleaned up graph store")
            
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
