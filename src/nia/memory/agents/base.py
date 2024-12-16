"""
Base agent implementation.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..memory_types import AgentResponse, Analysis, RelationshipTypes as RT

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base agent class."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        agent_type: str = "base"
    ):
        """Initialize agent."""
        self.llm = llm
        self.store = store
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
            
            # Then enrich content with graph information
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
                memories = await self.search_memories(
                    content_pattern=str(content),
                    limit=5
                )
                if memories:
                    content["related_memories"] = memories
                
                # Store agent's response with enriched content
                await self.store.store_memory(
                    memory_type=f"{self.agent_type}_response",
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
            query = f"""
            MATCH (s:AISystem {{name: $name}})
            OPTIONAL MATCH (s)-[:{RT.HAS_CAPABILITY}]->(c:Capability)
            WITH s, collect(c) as capabilities
            RETURN {{
                id: s.id,
                name: s.name,
                type: s.type,
                created_at: s.created_at,
                capabilities: [cap in capabilities | {{
                    id: cap.id,
                    type: cap.type,
                    description: cap.description,
                    confidence: cap.confidence
                }}]
            }} as system
            """
            
            result = await self.store.query_graph(query, {"name": name})
            return result[0]["system"] if result else None
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return None
    
    async def get_system_relationships(self, name: str) -> List[Dict]:
        """Get relationships for an AI system."""
        try:
            query = f"""
            MATCH (s:AISystem {{name: $name}})
            OPTIONAL MATCH (s)-[r]->(other)
            RETURN {{
                relationship_type: type(r),
                target_type: labels(other)[0],
                target_name: other.name,
                target_id: other.id,
                properties: properties(r)
            }} as relationship
            """
            
            result = await self.store.query_graph(query, {"name": name})
            return [r["relationship"] for r in result]
            
        except Exception as e:
            logger.error(f"Error getting system relationships: {str(e)}")
            return []
    
    async def get_capabilities(self) -> List[Dict]:
        """Get all capabilities in the system."""
        try:
            query = """
            MATCH (c:Capability)
            OPTIONAL MATCH (s:AISystem)-[r:HAS_CAPABILITY]->(c)
            WITH c, collect({
                name: s.name,
                type: s.type,
                confidence: coalesce(r.confidence, 0.0)
            }) as systems
            RETURN {
                id: c.id,
                type: c.type,
                description: c.description,
                confidence: c.confidence,
                systems: systems
            } as capability
            """
            
            result = await self.store.query_graph(query)
            return [r["capability"] for r in result]
            
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            return []
    
    async def search_memories(
        self,
        content_pattern: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search memories in the graph."""
        try:
            conditions = []
            params = {"limit": limit}
            
            if content_pattern:
                conditions.append("m.content CONTAINS $content")
                params["content"] = content_pattern
            
            if memory_type:
                conditions.append("m.type = $type")
                params["type"] = memory_type
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            query = f"""
            MATCH (m:Memory)
            WHERE {where_clause}
            WITH m
            ORDER BY m.created_at DESC
            LIMIT $limit
            OPTIONAL MATCH (m)-[r]->(n)
            WITH m, collect({{
                type: type(r),
                target_type: labels(n)[0],
                target_id: n.id,
                properties: properties(r)
            }}) as rels
            RETURN {{
                id: m.id,
                type: m.type,
                content: m.content,
                metadata: m.metadata,
                created_at: toString(m.created_at),
                relationships: rels
            }} as memory
            """
            
            result = await self.store.query_graph(query, params)
            return [r["memory"] for r in result]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    @abstractmethod
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        pass
