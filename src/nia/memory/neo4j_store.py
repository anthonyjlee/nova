"""
Neo4j-based memory store implementation using structured types.
"""

import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from .llm_interface import LLMInterface
from .neo4j import (
    Neo4jSchemaManager,
    Neo4jConceptManager,
    Neo4jSystemManager,
    Neo4jMemoryManager
)

logger = logging.getLogger(__name__)

class Neo4jMemoryStore:
    """Neo4j-based memory store with structured types."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        llm: Optional[LLMInterface] = None
    ):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.llm = llm or LLMInterface()
        
        # Initialize database
        self.initialize_database()
    
    def initialize_database(self) -> None:
        """Initialize Neo4j database schema and core nodes."""
        with self.driver.session() as session:
            # Initialize schema
            schema_manager = Neo4jSchemaManager(session)
            schema_manager.initialize_schema()
            
            # Initialize core nodes
            system_manager = Neo4jSystemManager(session)
            system_manager.initialize_systems()
            
            # Verify initialization
            schema_manager.verify_initialization()
    
    async def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a memory with all related nodes and relationships."""
        with self.driver.session() as session:
            try:
                # Create memory node
                memory_manager = Neo4jMemoryManager(session)
                memory_id = memory_manager.create_memory(
                    memory_type=memory_type,
                    content=content,
                    metadata=metadata
                )
                
                # Extract and create concepts
                concept_manager = Neo4jConceptManager(session, self.llm)
                concepts = await concept_manager.extract_concepts(str(content))
                for concept in concepts:
                    concept_manager.create_concept(memory_id, concept)
                
                # Create similarity relationships
                concept_manager.create_similarity_relationships(memory_id)
                
                # Create topic relationships if present
                if metadata and metadata.get('topics'):
                    memory_manager.create_topic_relationships(
                        memory_id=memory_id,
                        topics=metadata['topics']
                    )
                
                return memory_id
                
            except Exception as e:
                logger.error(f"Error storing memory: {str(e)}")
                raise
    
    async def search_memories(
        self,
        content_pattern: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories in the graph."""
        with self.driver.session() as session:
            memory_manager = Neo4jMemoryManager(session)
            return memory_manager.search_memories(
                content_pattern=content_pattern,
                memory_type=memory_type,
                limit=limit
            )
    
    async def get_capabilities(self) -> List[Dict[str, Any]]:
        """Get all capabilities in the system."""
        with self.driver.session() as session:
            system_manager = Neo4jSystemManager(session)
            return system_manager.get_capabilities()
    
    async def cleanup(self) -> None:
        """Clean up database."""
        with self.driver.session() as session:
            try:
                # Drop schema
                schema_manager = Neo4jSchemaManager(session)
                schema_manager.cleanup_schema()
                
                # Clean up nodes
                memory_manager = Neo4jMemoryManager(session)
                concept_manager = Neo4jConceptManager(session, self.llm)
                system_manager = Neo4jSystemManager(session)
                
                memory_manager.cleanup_memories()
                concept_manager.cleanup_concepts()
                system_manager.cleanup_systems()
                
                # Re-initialize
                self.initialize_database()
                
            except Exception as e:
                logger.error(f"Error cleaning up database: {str(e)}")
                raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        try:
            self.driver.close()
            logger.info("Closed Neo4j connection")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")
            raise
