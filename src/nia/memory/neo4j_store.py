"""
Neo4j-based knowledge graph implementation.
"""

import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from .llm_interface import LLMInterface
from .vector_store import VectorStore
from .neo4j import (
    Neo4jSchemaManager,
    Neo4jConceptManager,
    Neo4jSystemManager
)

logger = logging.getLogger(__name__)

class Neo4jMemoryStore:
    """Neo4j-based knowledge graph store."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        llm: Optional[LLMInterface] = None,
        vector_store: Optional[VectorStore] = None,
        similarity_threshold: float = 0.85
    ):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.llm = llm or LLMInterface()
        self.vector_store = vector_store or VectorStore()
        self.similarity_threshold = similarity_threshold
        
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
    ) -> None:
        """Extract concepts from memory and store in knowledge graph."""
        with self.driver.session() as session:
            try:
                # Extract and store concepts
                concept_manager = Neo4jConceptManager(
                    session,
                    self.llm,
                    self.vector_store,
                    self.similarity_threshold
                )
                concepts = await concept_manager.extract_concepts(str(content))
                for concept in concepts:
                    await concept_manager.create_concept(concept)
                
            except Exception as e:
                logger.error(f"Error storing concepts: {str(e)}")
                raise
    
    async def search_concepts(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search concepts using vector similarity."""
        with self.driver.session() as session:
            try:
                concept_manager = Neo4jConceptManager(
                    session,
                    self.llm,
                    self.vector_store,
                    self.similarity_threshold
                )
                return await concept_manager.search_concepts(query, limit)
            except Exception as e:
                logger.error(f"Error searching concepts: {str(e)}")
                return []
    
    async def get_system_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about an AI system."""
        with self.driver.session() as session:
            system_manager = Neo4jSystemManager(session)
            return system_manager.get_system_info(name)
    
    async def get_system_relationships(self, name: str) -> List[Dict[str, Any]]:
        """Get relationships for an AI system."""
        with self.driver.session() as session:
            system_manager = Neo4jSystemManager(session)
            return system_manager.get_system_relationships(name)
    
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
                concept_manager = Neo4jConceptManager(
                    session,
                    self.llm,
                    self.vector_store,
                    self.similarity_threshold
                )
                system_manager = Neo4jSystemManager(session)
                
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
