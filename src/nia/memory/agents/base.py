"""
Base agent implementation.
"""

import logging
from typing import Dict, List, Any, Optional
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
    
    def _extract_concept_text(self, concept: Dict[str, Any]) -> str:
        """Extract concept text from a dictionary."""
        # Get main concept fields
        name = concept.get('name', 'Unknown concept')
        type_str = concept.get('type', '')
        desc = concept.get('description', '')
        
        # Get related concepts if any
        related = concept.get('related_concepts', [])
        related_names = []
        if isinstance(related, list):
            for rel in related:
                if isinstance(rel, dict):
                    related_names.append(rel.get('name', ''))
                elif isinstance(rel, str):
                    related_names.append(rel)
        
        # Format the concept text
        text = f"{name}"
        if type_str:
            text += f" ({type_str})"
        if desc:
            text += f": {desc}"
        if related_names:
            text += f" [Related: {', '.join(related_names)}]"
        
        return text
    
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
            
            # Extract key points from both concepts and analysis
            key_points = []
            
            # Handle concepts if present
            if hasattr(llm_response, 'concepts'):
                concepts = llm_response.concepts
                if isinstance(concepts, list):
                    for concept in concepts:
                        if isinstance(concept, dict):
                            key_points.append(self._extract_concept_text(concept))
            
            # Handle analysis.key_points if present
            if hasattr(llm_response, 'analysis'):
                analysis_points = llm_response.analysis.get("key_points", [])
                if isinstance(analysis_points, list):
                    for point in analysis_points:
                        if isinstance(point, str):
                            key_points.append(point)
                        elif isinstance(point, dict):
                            key_points.append(self._extract_concept_text(point))
            
            # Create agent response
            response = AgentResponse(
                response=llm_response.response,
                analysis=Analysis(
                    key_points=key_points or ["No key points found"],
                    confidence=float(getattr(llm_response, 'analysis', {}).get("confidence", 0.8)),
                    state_update=str(getattr(llm_response, 'analysis', {}).get("state_update", "Processed content"))
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
                        'agent_type': self.agent_type,
                        'key_points': key_points,
                        'timestamp': metadata.get('timestamp') if metadata else None
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
