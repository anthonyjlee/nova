"""
Neo4j schema and constraint management.
"""

import logging
from neo4j import Session
from typing import List

logger = logging.getLogger(__name__)

class Neo4jSchemaManager:
    """Manages Neo4j schema and constraints."""
    
    def __init__(self, session: Session):
        """Initialize schema manager."""
        self.session = session
    
    def initialize_schema(self) -> None:
        """Initialize Neo4j schema with constraints."""
        constraints = [
            "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT capability_id IF NOT EXISTS FOR (c:Capability) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT evolution_id IF NOT EXISTS FOR (e:Evolution) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT system_id IF NOT EXISTS FOR (s:AISystem) REQUIRE s.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.session.run(constraint)
            except Exception as e:
                logger.error(f"Error creating constraint: {str(e)}")
    
    def cleanup_schema(self) -> None:
        """Clean up schema by dropping all constraints."""
        try:
            # First clean up any Memory nodes that might exist from before
            self.session.run("MATCH (m:Memory) DETACH DELETE m")
            
            # Drop constraints
            constraints = self.session.run("SHOW CONSTRAINTS")
            for constraint in constraints:
                name = constraint.get('name', '')
                if name:
                    self.session.run(f"DROP CONSTRAINT {name}")
        except Exception as e:
            logger.warning(f"Error dropping constraints: {str(e)}")
    
    def verify_initialization(self) -> None:
        """Verify schema initialization."""
        result = self.session.run("""
            MATCH (n)
            WITH labels(n) as labels, count(n) as count
            RETURN labels, count
        """)
        
        for record in result:
            logger.info(f"Initialized {record['count']} nodes with labels {record['labels']}")
        
        logger.info("Verified Neo4j schema initialization")
