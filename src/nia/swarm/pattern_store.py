"""Swarm pattern storage implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class SwarmPatternStore(Neo4jBaseStore):
    """Stores swarm patterns and configurations."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize store."""
        super().__init__(uri=uri, **kwargs)
    
    async def store_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store swarm pattern in Neo4j."""
        try:
            # Create pattern node
            query = """
            MERGE (p:SwarmPattern {id: $pattern_id})
            SET p.type = $pattern_type,
                p.config = $config,
                p.metadata = $metadata,
                p.created_at = $created_at,
                p.updated_at = $updated_at
            """
            
            await self.driver.execute_query(
                query,
                parameters={
                    "pattern_id": pattern_id,
                    "pattern_type": pattern_type,
                    "config": config,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error storing pattern: {str(e)}")
            raise
    
    async def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve swarm pattern."""
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            OPTIONAL MATCH (p)-[r]->(related:SwarmPattern)
            RETURN p, collect(DISTINCT {
                type: type(r),
                pattern_id: related.id,
                pattern_type: related.type
            }) as relationships
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            if result and result[0]:
                pattern_data = dict(result[0][0])
                relationships = [
                    rel for rel in result[0][1]
                    if rel["pattern_id"] is not None
                ]
                
                return {
                    **pattern_data,
                    "relationships": relationships
                }
            return None
        except Exception as e:
            logger.error(f"Error getting pattern: {str(e)}")
            raise
    
    async def link_patterns(
        self,
        from_pattern_id: str,
        to_pattern_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create relationships between patterns."""
        try:
            # Validate pattern IDs
            for pattern_id in [from_pattern_id, to_pattern_id]:
                if not await self.get_pattern(pattern_id):
                    raise ValueError(f"Pattern {pattern_id} not found")
            
            # Create relationship
            query = f"""
            MATCH (p1:SwarmPattern {{id: $from_id}})
            MATCH (p2:SwarmPattern {{id: $to_id}})
            MERGE (p1)-[r:{relationship_type}]->(p2)
            SET r += $properties
            """
            
            await self.driver.execute_query(
                query,
                parameters={
                    "from_id": from_pattern_id,
                    "to_id": to_pattern_id,
                    "properties": properties or {}
                }
            )
        except Exception as e:
            logger.error(f"Error linking patterns: {str(e)}")
            raise
    
    async def search_patterns(
        self,
        pattern_type: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for patterns based on criteria."""
        try:
            conditions = []
            parameters = {}
            
            if pattern_type:
                conditions.append("p.type = $pattern_type")
                parameters["pattern_type"] = pattern_type
            
            if metadata_filters:
                for key, value in metadata_filters.items():
                    conditions.append(f"p.metadata.{key} = ${key}")
                    parameters[key] = value
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            query = f"""
            MATCH (p:SwarmPattern)
            WHERE {where_clause}
            RETURN p
            ORDER BY p.created_at DESC
            """
            
            result = await self.driver.execute_query(
                query,
                parameters=parameters
            )
            
            patterns = []
            for record in result:
                pattern_data = dict(record[0])
                patterns.append(pattern_data)
            
            return patterns
        except Exception as e:
            logger.error(f"Error searching patterns: {str(e)}")
            raise
    
    async def update_pattern(
        self,
        pattern_id: str,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update pattern configuration."""
        try:
            # Validate pattern exists
            if not await self.get_pattern(pattern_id):
                raise ValueError(f"Pattern {pattern_id} not found")
            
            # Build update query
            set_clauses = ["p.updated_at = $updated_at"]
            parameters = {
                "pattern_id": pattern_id,
                "updated_at": datetime.now().isoformat()
            }
            
            if config is not None:
                set_clauses.append("p.config = $config")
                parameters["config"] = config
            
            if metadata is not None:
                set_clauses.append("p.metadata = $metadata")
                parameters["metadata"] = metadata
            
            query = f"""
            MATCH (p:SwarmPattern {{id: $pattern_id}})
            SET {', '.join(set_clauses)}
            """
            
            await self.driver.execute_query(
                query,
                parameters=parameters
            )
        except Exception as e:
            logger.error(f"Error updating pattern: {str(e)}")
            raise
    
    async def delete_pattern(self, pattern_id: str) -> None:
        """Delete pattern and its relationships."""
        try:
            # Validate pattern exists
            if not await self.get_pattern(pattern_id):
                raise ValueError(f"Pattern {pattern_id} not found")
            
            # Delete pattern and relationships
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            DETACH DELETE p
            """
            
            await self.driver.execute_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
        except Exception as e:
            logger.error(f"Error deleting pattern: {str(e)}")
            raise
    
    async def get_pattern_history(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Get pattern version history."""
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})-[:HAS_VERSION]->(v:PatternVersion)
            RETURN v
            ORDER BY v.version DESC
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            versions = []
            for record in result:
                version_data = dict(record[0])
                versions.append(version_data)
            
            return versions
        except Exception as e:
            logger.error(f"Error getting pattern history: {str(e)}")
            raise
    
    async def create_pattern_version(
        self,
        pattern_id: str,
        version: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create new pattern version."""
        try:
            # Validate pattern exists
            if not await self.get_pattern(pattern_id):
                raise ValueError(f"Pattern {pattern_id} not found")
            
            # Create version node
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            CREATE (v:PatternVersion {
                version: $version,
                config: $config,
                metadata: $metadata,
                created_at: $created_at
            })
            CREATE (p)-[:HAS_VERSION]->(v)
            """
            
            await self.driver.execute_query(
                query,
                parameters={
                    "pattern_id": pattern_id,
                    "version": version,
                    "config": config,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error creating pattern version: {str(e)}")
            raise
