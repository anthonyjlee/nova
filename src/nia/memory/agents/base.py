"""
Base agent implementation.
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

class BaseAgent(ABC):
    """Base agent class."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore,
        agent_type: str = "base"
    ):
        """Initialize agent."""
        self.llm = llm
        self.store = store  # Neo4j for concepts/knowledge
        self.vector_store = vector_store  # Qdrant for memories
        self.agent_type = agent_type
    
    def _format_concept_text(self, concept: Dict[str, Any]) -> str:
        """Format concept into readable text."""
        try:
            # Get concept fields
            name = concept.get('name', 'Unknown concept')
            type_str = concept.get('type', '')
            desc = concept.get('description', '')
            related = concept.get('related', [])
            
            # Format text
            text_parts = []
            text_parts.append(name)
            
            if type_str:
                text_parts.append(f"({type_str})")
            
            if desc:
                text_parts.append(f": {desc}")
            
            if related:
                text_parts.append(f"[Related: {', '.join(related)}]")
            
            text = ' '.join(text_parts)
            logger.debug(f"Formatted concept: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Error formatting concept: {str(e)}")
            return str(concept)
    
    async def process(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through agent lens."""
        try:
            # Get LLM response
            llm_response = await self.llm.get_structured_completion(
                self._format_prompt(content)
            )
            logger.debug(f"Got LLM response: {llm_response.dict()}")
            
            # Create agent response
            response = AgentResponse(
                response=f"I've identified {len(llm_response.concepts)} key concepts in your message.",
                concepts=llm_response.concepts
            )
            
            # Enrich with knowledge graph info
            try:
                # Get system info if mentioned
                systems_info = []
                for system in ["Nova", "Nia", "Echo"]:
                    if system.lower() in str(content).lower():
                        system_info = await self.get_system_info(system)
                        if system_info:
                            relationships = await self.get_system_relationships(system)
                            systems_info.append({
                                "system": system_info,
                                "relationships": relationships
                            })
                
                if systems_info:
                    content["systems_info"] = systems_info
                
                # Get capabilities if mentioned
                if "capability" in str(content).lower():
                    capabilities = await self.get_capabilities()
                    if capabilities:
                        content["capabilities_info"] = capabilities
                
                # Get related memories
                similar_memories = await self.vector_store.search_vectors(
                    content=serialize_datetime(content),
                    limit=5
                )
                if similar_memories:
                    content["similar_memories"] = similar_memories
                
                # Store in vector store with serialized datetime objects
                await self.vector_store.store_vector(
                    content=serialize_datetime({
                        'original_content': content,
                        'agent_response': serialize_datetime(response.dict()),
                        'agent_type': self.agent_type,
                        'concepts': llm_response.concepts,
                        'timestamp': metadata.get('timestamp') if metadata else None
                    }),
                    metadata=serialize_datetime(metadata),
                    layer="semantic"
                )
            except Exception as e:
                logger.error(f"Failed to enrich/store memory: {str(e)}")
                # Continue even if enrichment fails
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}")
            raise
    
    async def get_system_info(self, name: str) -> Optional[Dict]:
        """Get information about an AI system."""
        try:
            return await self.store.get_system_info(name)
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return None
    
    async def get_system_relationships(self, name: str) -> List[Dict]:
        """Get relationships for an AI system."""
        try:
            return await self.store.get_system_relationships(name)
        except Exception as e:
            logger.error(f"Error getting system relationships: {str(e)}")
            return []
    
    async def get_capabilities(self) -> List[Dict]:
        """Get all capabilities in the system."""
        try:
            return await self.store.get_capabilities()
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            return []
    
    @abstractmethod
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        pass
