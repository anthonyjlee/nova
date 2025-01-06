"""Two-layer memory system implementation for NIA."""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from nia.memory.vector.vector_store import VectorStore, serialize_for_vector_store
from nia.memory.neo4j.neo4j_store import Neo4jMemoryStore
from nia.memory.neo4j.concept_store import ConceptStore
from nia.memory.vector.embeddings import EmbeddingService
from nia.memory.types.memory_types import Memory, MemoryType, EpisodicMemory

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
        
    async def store_memory(self, memory: Memory) -> str:
        """Store a new episodic memory."""
        try:
            # Create embedding and store
            memory_dict = memory.dict()
            memory_dict["consolidated"] = False  # Ensure consolidated field is set
            memory_id = await self.store.store_vector(
                content=memory_dict,
                metadata={
                    "type": MemoryType.EPISODIC.value,
                    "timestamp": datetime.now().isoformat(),
                    "context": memory.context if hasattr(memory, "context") else {}
                }
            )
            
            # Track for consolidation
            self.pending_consolidation.add(memory_id)
            
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store episodic memory: {str(e)}")
            raise
            
    async def get_consolidation_candidates(self) -> List[Dict]:
        """Get memories ready for consolidation."""
        try:
            # Get all memories
            return await self.store.search_vectors()
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
    
    async def _execute_with_retry(self, operation):
        """Execute an operation with retry logic."""
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                return await operation()
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise e
                await asyncio.sleep(1)  # Wait before retrying

    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        await self.store_concept(
            name=f"reflection_{datetime.now().isoformat()}",
            type="reflection",
            description=content
        )
    
    def __init__(self, store: Optional[Neo4jMemoryStore] = None):
        if store is None:
            super().__init__(
                uri="bolt://0.0.0.0:7687",
                user="neo4j",
                password="password",
                max_retry_time=30,
                retry_interval=1
            )
        else:
            # Initialize ConceptStore with store's connection details
            super().__init__(
                uri=store.uri,
                user=store.user,
                password=store.password,
                max_retry_time=30,
                retry_interval=1
            )
            # Use the provided store's driver
            self.driver = store.driver if hasattr(store, 'driver') else store
            
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
        
    async def _create_belief(self, subject: str, predicate: str, object: str, confidence: float = 1.0):
        """Create a belief in the knowledge graph."""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (s:Concept {name: $subject})
                MATCH (o:Concept {name: $object})
                MERGE (s)-[r:BELIEVES {predicate: $predicate, confidence: $confidence}]->(o)
                """,
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object": object,
                    "confidence": confidence
                }
            )

    async def store_knowledge(self, knowledge: Dict):
        """Store extracted semantic knowledge."""
        try:
            # Create concept nodes
            for concept in knowledge.get("concepts", []):
                await self.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"],
                    validation=concept.get("validation"),
                    is_consolidation=concept.get("is_consolidation", False)
                )
                
            # Create relationships
            async with self.driver.session() as session:
                for rel in knowledge.get("relationships", []):
                    # Create source concept if it doesn't exist
                    await session.run(
                        """
                        MERGE (c1:Concept {name: $from})
                        ON CREATE SET c1.type = 'concept', c1.description = ''
                        WITH c1
                        MERGE (c2:Concept {name: $to})
                        ON CREATE SET c2.type = 'concept', c2.description = ''
                        MERGE (c1)-[:RELATED_TO {type: $type}]->(c2)
                        """,
                        {
                            "from": rel["from"],
                            "to": rel["to"],
                            "type": rel["type"]
                        }
                    )
                    
            # Store beliefs
            for belief in knowledge.get("beliefs", []):
                await self._create_belief(
                    belief["subject"],
                    belief["predicate"],
                    belief["object"],
                    belief.get("confidence", 1.0)
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
            async with self.driver.session() as session:
                result = await session.run(cypher)
                records = await result.data()  # Get all records
                
                # Process and return results
                return self._process_query_results(records)
        except Exception as e:
            logger.error(f"Failed to query knowledge: {str(e)}")
            return []
            
    def _build_cypher_query(self, query: Dict) -> str:
        """Build Cypher query from query dict."""
        # Basic query building - extend based on needs
        if query.get("type") == "concept":
            # Handle both type and label matching
            conditions = []
            if "type" in query:
                conditions.append(f"n.type = '{query['type']}'")
            if "label" in query:
                conditions.append(f"n.type = '{query['label']}'")
            
            where_clause = " OR ".join(conditions) if conditions else "true"
            
            return f"""
            MATCH (n:Concept)
            WHERE {where_clause}
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
                if isinstance(result["n"], dict) and "properties" in result["n"]:
                    processed.append(result["n"]["properties"])
                else:
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
    
    def __init__(self, neo4j_uri: str = "bolt://0.0.0.0:7687", 
                 vector_store: Optional[VectorStore] = None,
                 llm = None):
        self.episodic = EpisodicLayer(vector_store)
        self.semantic = SemanticLayer()
        self.semantic.store = self.semantic
        self.consolidation_manager = None  # Will be set by ConsolidationManager
        self._initialized = False
        self.llm = llm  # Store LLM interface
        
    async def initialize(self):
        """Initialize connections to Neo4j and vector store."""
        if not self._initialized:
            # Initialize Neo4j connection
            if hasattr(self.semantic, 'connect'):
                await self.semantic.connect()
            
            # Initialize vector store if needed
            if hasattr(self.episodic.store, 'connect'):
                await self.episodic.store.connect()
                
            self._initialized = True
            
    async def cleanup(self):
        """Clean up connections."""
        if self._initialized:
            # Close Neo4j connection
            if hasattr(self.semantic, 'close'):
                await self.semantic.close()
                
            # Close vector store connection if needed
            if hasattr(self.episodic.store, 'close'):
                await self.episodic.store.close()
                
            self._initialized = False
            
    async def prune(
        self,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, int]:
        """Prune old memories and unused nodes."""
        pruned_nodes = 0
        pruned_relationships = 0
        pruned_memories = 0
        
        try:
            # Prune episodic memories
            if hasattr(self.episodic.store, 'delete_vectors'):
                # Get old consolidated memories
                old_memories = await self.episodic.store.search_vectors(
                    filter={
                        "consolidated": True,
                        "domain": domain
                    } if domain else {"consolidated": True}
                )
                
                # Delete old memories
                if old_memories:
                    memory_ids = [m.id for m in old_memories if hasattr(m, 'id')]
                    await self.episodic.store.delete_vectors(memory_ids)
                    pruned_memories = len(memory_ids)
            
            # Prune semantic nodes
            if hasattr(self.semantic, 'run_query'):
                # Find unused nodes (no relationships)
                unused_query = """
                MATCH (n)
                WHERE NOT (n)--()
                AND (n.domain = $domain OR $domain IS NULL)
                WITH n
                LIMIT 1000
                DETACH DELETE n
                RETURN count(n) as deleted
                """
                
                result = await self.semantic.run_query(
                    unused_query,
                    {"domain": domain}
                )
                pruned_nodes = result[0]["deleted"] if result else 0
                
                # Find and remove dangling relationships
                dangling_query = """
                MATCH ()-[r]->()
                WHERE (r.domain = $domain OR $domain IS NULL)
                AND r.last_accessed < datetime() - duration('P30D')
                WITH r
                LIMIT 1000
                DELETE r
                RETURN count(r) as deleted
                """
                
                result = await self.semantic.run_query(
                    dangling_query,
                    {"domain": domain}
                )
                pruned_relationships = result[0]["deleted"] if result else 0
                
            return {
                "pruned_nodes": pruned_nodes,
                "pruned_relationships": pruned_relationships,
                "pruned_memories": pruned_memories,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to prune memory system: {str(e)}")
            raise
        
    async def store_experience(self, experience: Memory):
        """Store new experience in episodic memory."""
        # Store in episodic memory first
        await self.episodic.store_memory(experience)
        
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
        memory_ids = [m.id for m in memories if hasattr(m, 'id')]
        await self.episodic.archive_memories(memory_ids)
        
    async def query_episodic(self, query: Dict) -> List[EpisodicMemory]:
        """Query episodic memories."""
        try:
            results = await self.episodic.store.search_vectors(
                content=query.get("content", ""),
                filter=query.get("filter", {})
            )
            return [EpisodicMemory(**r) for r in results]
        except Exception as e:
            logger.error(f"Failed to query episodic memories: {str(e)}")
            return []
            
    async def query_semantic(self, query: Dict) -> List[Dict]:
        """Query semantic knowledge."""
        return await self.semantic.query_knowledge(query)
        
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by its ID."""
        try:
            # Search for memory in episodic store
            # Convert memory_id to content for searching
            results = await self.episodic.store.search_vectors(
                content={"id": memory_id},
                limit=1,
                score_threshold=0.99  # High threshold for exact match
            )
            if results and len(results) > 0:
                # Convert first result to Memory object
                memory_data = results[0]
                return Memory(**memory_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {str(e)}")
            return None
