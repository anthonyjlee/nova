"""
Neo4j AI system and capability management.
"""

import logging
from neo4j import Session
from typing import Dict, List, Any, Optional
from ..memory_types import (
    AISystem, Capability,
    DEFAULT_CAPABILITIES,
    NOVA, NIA, ECHO,
    RelationshipTypes as RT
)

logger = logging.getLogger(__name__)

class Neo4jSystemManager:
    """Manages AI systems and capabilities in Neo4j."""
    
    def __init__(self, session: Session):
        """Initialize system manager."""
        self.session = session
    
    def initialize_systems(self) -> None:
        """Initialize core AI system nodes."""
        try:
            # Create AI systems
            systems_query = f"""
            MERGE (nova:AISystem {{id: $nova.id}})
            SET nova += $nova
            
            MERGE (nia:AISystem {{id: $nia.id}})
            SET nia += $nia
            
            MERGE (echo:AISystem {{id: $echo.id}})
            SET echo += $echo
            
            WITH nova, nia, echo
            MERGE (echo)-[r1:{RT.PREDECESSOR_OF}]->(nia)
            MERGE (nia)-[r2:{RT.PREDECESSOR_OF}]->(nova)
            SET r1.transition_date = datetime($nia_date),
                r2.transition_date = datetime($nova_date)
            """
            
            self.session.run(
                systems_query,
                nova=vars(NOVA),
                nia=vars(NIA),
                echo=vars(ECHO),
                nia_date=NIA.created_at.isoformat(),
                nova_date=NOVA.created_at.isoformat()
            )
            
            # Create capabilities
            capabilities_query = f"""
            UNWIND $capabilities as cap
            MERGE (c:Capability {{id: cap.id}})
            SET c += cap
            
            WITH c
            MATCH (nia:AISystem {{name: 'Nia'}})
            WHERE c.id in $nia_capabilities
            MERGE (nia)-[h:{RT.HAS_CAPABILITY}]->(c)
            SET h.confidence = 1.0,
                h.context = 'predecessor'
            """
            
            self.session.run(
                capabilities_query,
                capabilities=[vars(cap) for cap in DEFAULT_CAPABILITIES],
                nia_capabilities=NIA.capabilities
            )
            
            logger.info("Initialized AI systems and capabilities")
            
        except Exception as e:
            logger.error(f"Error initializing systems: {str(e)}")
            raise
    
    def get_system_info(self, name: str) -> Optional[Dict[str, Any]]:
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
            
            result = self.session.run(query, name=name)
            record = result.single()
            return record["system"] if record else None
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return None
    
    def get_system_relationships(self, name: str) -> List[Dict[str, Any]]:
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
            
            result = self.session.run(query, name=name)
            return [dict(record["relationship"]) for record in result]
            
        except Exception as e:
            logger.error(f"Error getting system relationships: {str(e)}")
            return []
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
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
            
            result = self.session.run(query)
            return [dict(record["capability"]) for record in result]
            
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            return []
    
    def cleanup_systems(self) -> None:
        """Remove all system nodes and relationships."""
        try:
            self.session.run("MATCH (s:AISystem) DETACH DELETE s")
            self.session.run("MATCH (c:Capability) DETACH DELETE c")
            logger.info("Cleaned up system nodes and relationships")
        except Exception as e:
            logger.error(f"Error cleaning up systems: {str(e)}")
            raise
