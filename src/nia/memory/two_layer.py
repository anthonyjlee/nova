"""Two-layer memory system implementation for NIA."""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from nia.memory.vector_store import VectorStore, serialize_for_vector_store
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.neo4j.concept_store import ConceptStore
from nia.memory.embeddings import EmbeddingService
from nia.memory.memory_types import Memory, MemoryType

logger = logging.getLogger(__name__)

class EpisodicLayer:
    """Handles short-term episodic memories using vector storage."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        if vector_store is None:
            # Use default configuration
            embedding_service = EmbeddingService()
            self.store = VectorStore(embedding_service)
        else:
            self.store = vector_store
        self.pending_consolidation = set()
        
    async def store(self, memory: Memory) -> str:
        """Store a new episodic memory."""
        try:
            # Create embedding and store
            memory_id = await self.store.store_vector(
                content=memory.dict(),
                metadata={
                    "type": MemoryType.EPISODIC.value,
                    "timestamp": datetime.now().isoformat(),
                    "consolidated": False
                }
            )
            
            # Track for consolidation
            self.pending_consolidation.add(memory_id)
            
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store episodic memory: {str(e)}")
            raise
            
    async def get_consolidation_candidates(self) -> List[Memory]:
        """Get memories ready for consolidation."""
        try:
            # Get all pending memories
            memories = []
            for memory_id in self.pending_consolidation:
                memory = await self.store.get_vector(memory_id)
                if memory:
                    memories.append(Memory(**memory))
            return memories
        except Exception as e:
            logger.error(f"Failed to get consolidation candidates: {str(e)}")
            return []
            
    async def archive_memories(self, memory_ids: List[str]):
        """Archive memories after consolidation."""
        try:
            for memory_id in memory_ids:
                # Update metadata to mark as consolidated
                await self.store.update_metadata(
                    memory_id,
                    {"consolidated": True}
                )
                self.pending_consolidation.remove(memory_id)
        except Exception as e:
            logger.error(f"Failed to archive memories: {str(e)}")

class SemanticLayer(ConceptStore):
    """Handles long-term semantic knowledge using Neo4j.
    
    Inherits from ConceptStore to leverage existing Neo4j functionality.
    """
    
    def __init__(self, uri: str = "bolt://0.0.0.0:7687", 
                 user: str = "neo4j", 
                 password: str = "password"):
        super().__init__(uri, user, password)
        self.knowledge_patterns = {
            "concepts": self._create_concept_pattern(),
            "relationships": self._create_relationship_pattern(),
            "beliefs": self._create_belief_pattern()
        }
        
    def _create_concept_pattern(self) -> Dict:
        """Create pattern for concept extraction."""
        return {
            "type": "concept",
            "properties": ["name", "category", "attributes"]
        }
        
    def _create_relationship_pattern(self) -> Dict:
        """Create pattern for relationship extraction."""
        return {
            "type": "relationship",
            "properties": ["from", "to", "type", "attributes"]
        }
        
    def _create_belief_pattern(self) -> Dict:
        """Create pattern for belief extraction."""
        return {
            "type": "belief",
            "properties": ["subject", "predicate", "object", "confidence"]
        }
        
    async def store_knowledge(self, knowledge: Dict):
        """Store extracted semantic knowledge."""
        try:
            # Create concept nodes
            for concept in knowledge.get("concepts", []):
                await self.store.create_concept_node(
                    label=concept["type"],
                    properties=concept["properties"]
                )
                
            # Create relationships
            for rel in knowledge.get("relationships", []):
                await self.store.create_relationship(
                    start_node=rel["from"],
                    end_node=rel["to"],
                    type=rel["type"],
                    properties=rel.get("properties", {})
                )
                
            # Store beliefs
            for belief in knowledge.get("beliefs", []):
                await self.store.create_belief(
                    subject=belief["subject"],
                    predicate=belief["predicate"],
                    object=belief["object"],
                    confidence=belief.get("confidence", 1.0)
                )
        except Exception as e:
            logger.error(f"Failed to store semantic knowledge: {str(e)}")
            raise
            
    async def query_knowledge(self, query: Dict) -> List[Dict]:
        """Query semantic knowledge."""
        try:
            # Convert query to Cypher
            cypher = self._build_cypher_query(query)
            
            # Execute query
            results = await self.store.run_query(cypher)
            
            # Process and return results
            return self._process_query_results(results)
        except Exception as e:
            logger.error(f"Failed to query knowledge: {str(e)}")
            return []
            
    def _build_cypher_query(self, query: Dict) -> str:
        """Build Cypher query from query dict."""
        # Basic query building - extend based on needs
        if query.get("type") == "concept":
            return f"""
            MATCH (n:{query['label']})
            RETURN n
            """
        elif query.get("pattern"):
            return f"""
            MATCH p = {query['pattern']}
            RETURN p
            """
        return ""
        
    def _process_query_results(self, results: List[Dict]) -> List[Dict]:
        """Process Neo4j results into standard format."""
        processed = []
        for result in results:
            if "n" in result:  # Single node
                processed.append(result["n"])
            elif "p" in result:  # Path
                processed.append(self._process_path(result["p"]))
        return processed
        
    def _process_path(self, path: Dict) -> Dict:
        """Process Neo4j path into standard format."""
        return {
            "nodes": path.nodes,
            "relationships": path.relationships
        }

class TwoLayerMemorySystem:
    """Implements episodic and semantic memory layers."""
    
    def __init__(self, neo4j_store: Optional[Neo4jMemoryStore] = None, 
                 vector_store: Optional[VectorStore] = None):
        self.episodic = EpisodicLayer(vector_store)
        self.semantic = SemanticLayer(neo4j_store)
        self.consolidation_manager = None  # Will be set by ConsolidationManager
        
    async def store_experience(self, experience: Memory):
        """Store new experience in episodic memory."""
        # Store in episodic memory first
        await self.episodic.store(experience)
        
        # Check for consolidation if manager exists
        if self.consolidation_manager and await self.consolidation_manager.should_consolidate():
            await self.consolidate_memories()
            
    async def consolidate_memories(self):
        """Convert episodic memories to semantic knowledge."""
        if not self.consolidation_manager:
            logger.warning("No consolidation manager set")
            return
            
        # Get memories ready for consolidation
        memories = await self.episodic.get_consolidation_candidates()
        
        if not memories:
            return
            
        # Extract patterns and relationships
        knowledge = await self.consolidation_manager.extract_knowledge(memories)
        
        # Store in semantic layer
        await self.semantic.store_knowledge(knowledge)
        
        # Archive processed memories
        memory_ids = [m.id for m in memories]
        await self.episodic.archive_memories(memory_ids)
        
    async def query_episodic(self, query: Dict) -> List[Memory]:
        """Query episodic memories."""
        try:
            results = await self.episodic.store.search_vectors(
                content=query.get("content", ""),
                filter=query.get("filter", {})
            )
            return [Memory(**r) for r in results]
        except Exception as e:
            logger.error(f"Failed to query episodic memories: {str(e)}")
            return []
            
    async def query_semantic(self, query: Dict) -> List[Dict]:
        """Query semantic knowledge."""
        return await self.semantic.query_knowledge(query)
