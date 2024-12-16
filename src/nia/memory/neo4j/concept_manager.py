"""
Neo4j concept extraction and relationship management.
"""

import logging
from neo4j import Session
from typing import Dict, List, Any, Optional
from ..llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class Neo4jConceptManager:
    """Manages concept extraction and relationships in Neo4j."""
    
    def __init__(self, session: Session, llm: LLMInterface):
        """Initialize concept manager."""
        self.session = session
        self.llm = llm
    
    async def extract_concepts(self, content: str) -> List[Dict[str, Any]]:
        """Extract concepts from content using LLM."""
        prompt = """Extract key concepts from the following content. For each concept include:
        1. Name of the concept
        2. Type (e.g., technology, capability, system, idea)
        3. Description
        4. Related concepts
        
        Content: {content}
        
        Respond in JSON format with a list of concepts."""
        
        try:
            response = await self.llm.get_structured_completion(prompt.format(content=content))
            # Extract concepts from key_points which contain the concept objects
            concepts = []
            for point in response.analysis["key_points"]:
                if isinstance(point, dict) and "concept_name" in point:
                    concepts.append({
                        "name": point["concept_name"],
                        "type": point.get("concept_type", "concept"),
                        "description": point.get("concept_description", ""),
                        "related": point.get("related_concepts", [])
                    })
            return concepts
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            return []
    
    def create_concept(self, concept: Dict[str, Any]) -> None:
        """Create a concept node and its relationships."""
        try:
            # Create concept
            concept_query = """
            MERGE (c:Concept {
                id: $concept_name,
                type: $concept_type
            })
            ON CREATE SET c.description = $concept_desc
            """
            
            self.session.run(
                concept_query,
                concept_name=concept["name"],
                concept_type=concept["type"],
                concept_desc=concept["description"]
            )
            
            # Create relationships between concepts
            if concept.get("related"):
                for related in concept["related"]:
                    relationship_query = """
                    MATCH (c:Concept {id: $concept_name})
                    MERGE (r:Concept {id: $related_name})
                    MERGE (c)-[:RELATED_TO {
                        created_at: datetime()
                    }]->(r)
                    """
                    
                    self.session.run(
                        relationship_query,
                        concept_name=concept["name"],
                        related_name=related
                    )
        except Exception as e:
            logger.warning(f"Error creating concept {concept['name']}: {str(e)}")
    
    def search_concepts(
        self,
        pattern: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search concepts by pattern."""
        try:
            query = """
            MATCH (c:Concept)
            WHERE c.description CONTAINS $pattern
            WITH c
            OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
            WITH c, collect(r.id) as related
            RETURN {
                id: c.id,
                type: c.type,
                description: c.description,
                related: related
            } as concept
            LIMIT $limit
            """
            
            result = self.session.run(
                query,
                pattern=pattern,
                limit=limit
            )
            
            return [dict(record["concept"]) for record in result]
            
        except Exception as e:
            logger.error(f"Error searching concepts: {str(e)}")
            return []
    
    def cleanup_concepts(self) -> None:
        """Remove all concept nodes and relationships."""
        try:
            self.session.run("MATCH (c:Concept) DETACH DELETE c")
            logger.info("Cleaned up concept nodes and relationships")
        except Exception as e:
            logger.error(f"Error cleaning up concepts: {str(e)}")
            raise
