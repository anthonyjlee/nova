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
    
    def create_concept(
        self,
        memory_id: str,
        concept: Dict[str, Any]
    ) -> None:
        """Create a concept node and link it to memory."""
        try:
            # Create concept and link to memory
            concept_query = """
            MATCH (m:Memory {id: $memory_id})
            MERGE (c:Concept {
                id: $concept_name,
                type: $concept_type
            })
            ON CREATE SET c.description = $concept_desc
            WITH m, c
            MERGE (m)-[:HAS_CONCEPT {
                created_at: datetime()
            }]->(c)
            """
            
            self.session.run(
                concept_query,
                memory_id=memory_id,
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
    
    def get_memory_concepts(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get all concepts linked to a memory."""
        try:
            query = """
            MATCH (m:Memory {id: $memory_id})-[:HAS_CONCEPT]->(c:Concept)
            OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
            WITH c, collect(r.id) as related
            RETURN {
                id: c.id,
                type: c.type,
                description: c.description,
                related: related
            } as concept
            """
            
            result = self.session.run(query, memory_id=memory_id)
            return [dict(record["concept"]) for record in result]
        except Exception as e:
            logger.error(f"Error getting memory concepts: {str(e)}")
            return []
    
    def create_similarity_relationships(self, memory_id: str) -> None:
        """Create similarity relationships between memories."""
        try:
            similarity_query = """
            MATCH (m:Memory {id: $memory_id})
            MATCH (prev:Memory)
            WHERE prev.id <> m.id
            WITH m, prev,
                 reduce(s = 0.0,
                       w in split(toLower(m.content), ' ') |
                       s + case when toLower(prev.content) contains w then 1.0 else 0.0 end
                 ) / size(split(toLower(m.content), ' ')) as similarity
            WHERE similarity > 0.3
            CREATE (m)-[:SIMILAR_TO {
                score: similarity,
                created_at: datetime()
            }]->(prev)
            """
            
            self.session.run(similarity_query, memory_id=memory_id)
        except Exception as e:
            logger.warning(f"Error creating similarity relationships: {str(e)}")
    
    def cleanup_concepts(self) -> None:
        """Remove all concept nodes and relationships."""
        try:
            self.session.run("MATCH (c:Concept) DETACH DELETE c")
            logger.info("Cleaned up concept nodes and relationships")
        except Exception as e:
            logger.error(f"Error cleaning up concepts: {str(e)}")
            raise
