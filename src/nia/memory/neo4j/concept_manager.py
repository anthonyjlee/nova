"""
Neo4j concept extraction and relationship management.
"""

import logging
from neo4j import Session
from typing import Dict, List, Any, Optional
from ..llm_interface import LLMInterface
from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

class Neo4jConceptManager:
    """Manages concept extraction and relationships in Neo4j."""
    
    def __init__(
        self,
        session: Session,
        llm: LLMInterface,
        vector_store: VectorStore,
        similarity_threshold: float = 0.85
    ):
        """Initialize concept manager."""
        self.session = session
        self.llm = llm
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold
    
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
    
    async def find_similar_concept(self, concept: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find similar existing concept using vector similarity."""
        try:
            # Create search text combining name and description
            search_text = f"{concept['name']} {concept['description']}"
            
            # Search for similar concepts in vector store
            similar_concepts = await self.vector_store.search_vectors(
                content=search_text,
                filter={"type": "concept"},
                limit=1
            )
            
            # Check if any concept is similar enough
            if similar_concepts and similar_concepts[0].get("score", 0) >= self.similarity_threshold:
                return similar_concepts[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding similar concept: {str(e)}")
            return None
    
    async def merge_concepts(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two similar concepts."""
        try:
            # Keep existing name but combine descriptions
            merged = {
                "name": existing["name"],
                "type": existing["type"],
                "description": existing["description"],
                "related": list(set(existing.get("related", []) + new.get("related", [])))
            }
            
            # Update the concept in Neo4j
            self.update_concept(merged)
            
            # Update vector store
            await self.vector_store.store_vector(
                content={
                    "name": merged["name"],
                    "type": "concept",
                    "description": merged["description"]
                },
                metadata={
                    "id": merged["name"],
                    "type": "concept"
                }
            )
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging concepts: {str(e)}")
            return existing
    
    async def create_concept(self, concept: Dict[str, Any]) -> None:
        """Create a concept node and its relationships."""
        try:
            # Check for similar existing concepts
            similar = await self.find_similar_concept(concept)
            
            if similar:
                # Merge with existing concept
                concept = await self.merge_concepts(similar, concept)
            else:
                # Create new concept in Neo4j
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
                
                # Store in vector store
                await self.vector_store.store_vector(
                    content={
                        "name": concept["name"],
                        "type": "concept",
                        "description": concept["description"]
                    },
                    metadata={
                        "id": concept["name"],
                        "type": "concept"
                    }
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
    
    def update_concept(self, concept: Dict[str, Any]) -> None:
        """Update an existing concept."""
        try:
            query = """
            MATCH (c:Concept {id: $concept_name})
            SET c.type = $concept_type,
                c.description = $concept_desc
            """
            
            self.session.run(
                query,
                concept_name=concept["name"],
                concept_type=concept["type"],
                concept_desc=concept["description"]
            )
            
        except Exception as e:
            logger.error(f"Error updating concept: {str(e)}")
    
    async def search_concepts(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search concepts using vector similarity."""
        try:
            # Search using vector store
            similar_concepts = await self.vector_store.search_vectors(
                content=query,
                filter={"type": "concept"},
                limit=limit
            )
            
            # Get full concept details from Neo4j
            concept_details = []
            for concept in similar_concepts:
                neo4j_query = """
                MATCH (c:Concept {id: $concept_id})
                WITH c
                OPTIONAL MATCH (c)-[:RELATED_TO]->(r:Concept)
                WITH c, collect(r.id) as related
                RETURN {
                    id: c.id,
                    type: c.type,
                    description: c.description,
                    related: related,
                    score: $score
                } as concept
                """
                
                result = self.session.run(
                    neo4j_query,
                    concept_id=concept["metadata"]["id"],
                    score=concept["score"]
                )
                
                for record in result:
                    concept_details.append(dict(record["concept"]))
            
            return concept_details
            
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
