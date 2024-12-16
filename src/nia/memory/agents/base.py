"""
Base agent implementation.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse, Analysis

logger = logging.getLogger(__name__)

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
    
    async def process(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through agent lens."""
        try:
            # Get LLM response first
            llm_response = await self.llm.get_structured_completion(
                self._format_prompt(content)
            )
            
            # Convert LLM response to AgentResponse
            response = AgentResponse(
                response=llm_response.response,
                analysis=Analysis(
                    key_points=llm_response.analysis["key_points"],
                    confidence=llm_response.analysis["confidence"],
                    state_update=llm_response.analysis["state_update"]
                )
            )
            
            # Then enrich content with knowledge graph information
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
                
                # Get related memories from vector store
                similar_memories = await self.vector_store.search_vectors(
                    content=str(content),
                    limit=5
                )
                if similar_memories:
                    content["similar_memories"] = similar_memories
                
                # Store agent's response in vector store
                await self.vector_store.store_vector(
                    content={
                        'original_content': content,
                        'agent_response': response.dict(),
                        'agent_type': self.agent_type
                    },
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to enrich/store {self.agent_type} memory: {str(e)}")
                # Continue even if enrichment/storage fails
            
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
