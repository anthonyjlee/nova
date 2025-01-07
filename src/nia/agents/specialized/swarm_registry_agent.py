"""Swarm Registry Agent for managing swarm patterns and configurations."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..tinytroupe_agent import TinyTroupeAgent
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class SwarmRegistryAgent(TinyTroupeAgent):
    """Manages swarm patterns and configurations."""
    
    def __init__(
        self,
        name: str = "swarm_registry",
        memory_system: Optional[TwoLayerMemorySystem] = None,
        domain: str = "swarm_management",
        **kwargs
    ):
        """Initialize SwarmRegistryAgent."""
        super().__init__(name=name, memory_system=memory_system, domain=domain, **kwargs)
        self.store = self.memory_system.semantic.store if memory_system else None
    
    async def register_pattern(
        self,
        pattern_type: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register new swarm pattern.
        
        Args:
            pattern_type: Type of swarm pattern (e.g., hierarchical, mesh)
            config: Pattern configuration including tasks and relationships
            metadata: Optional metadata about the pattern
            
        Returns:
            Dict containing pattern_id and registration status
        """
        try:
            # Generate unique ID for pattern
            pattern_id = str(uuid.uuid4())
            
            # Prepare pattern data
            pattern_data = {
                "id": pattern_id,
                "type": pattern_type,
                "config": config,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Store in Neo4j
            query = """
            CREATE (p:SwarmPattern {
                id: $id,
                type: $type,
                config: $config,
                metadata: $metadata,
                created_at: $created_at,
                status: $status
            })
            RETURN p
            """
            
            await self.store.run_query(
                query,
                parameters=pattern_data
            )
            
            # Store in vector store for semantic search
            await self.memory_system.vector_store.store_vector(
                content=pattern_data,
                metadata={"type": "swarm_pattern"},
                layer="semantic"
            )
            
            return {
                "pattern_id": pattern_id,
                "registration_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error registering pattern: {str(e)}")
            return {
                "pattern_id": None,
                "registration_status": "failed",
                "error": str(e)
            }
    
    async def validate_config(
        self,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate swarm configuration.
        
        Args:
            config: Pattern configuration to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Check required fields
            required_fields = ["tasks", "dependencies"]
            for field in required_fields:
                if field not in config:
                    validation_results["is_valid"] = False
                    validation_results["errors"].append(f"Missing required field: {field}")
            
            # Validate tasks
            if "tasks" in config:
                tasks = config["tasks"]
                task_ids = set()
                
                for task in tasks:
                    # Check task structure
                    if not isinstance(task, dict):
                        validation_results["is_valid"] = False
                        validation_results["errors"].append("Task must be a dictionary")
                        continue
                        
                    # Check required task fields
                    if "id" not in task:
                        validation_results["is_valid"] = False
                        validation_results["errors"].append("Task missing id field")
                        continue
                        
                    # Check for duplicate task IDs
                    if task["id"] in task_ids:
                        validation_results["is_valid"] = False
                        validation_results["errors"].append(f"Duplicate task ID: {task['id']}")
                    task_ids.add(task["id"])
            
            # Validate dependencies
            if "dependencies" in config:
                dependencies = config["dependencies"]
                
                for dep in dependencies:
                    # Check dependency structure
                    if not isinstance(dep, dict):
                        validation_results["is_valid"] = False
                        validation_results["errors"].append("Dependency must be a dictionary")
                        continue
                        
                    # Check required dependency fields
                    required_dep_fields = ["from", "to"]
                    for field in required_dep_fields:
                        if field not in dep:
                            validation_results["is_valid"] = False
                            validation_results["errors"].append(f"Dependency missing {field} field")
                            continue
                    
                    # Verify task IDs exist
                    if dep.get("from") not in task_ids:
                        validation_results["is_valid"] = False
                        validation_results["errors"].append(f"Unknown task ID in dependency: {dep.get('from')}")
                    if dep.get("to") not in task_ids:
                        validation_results["is_valid"] = False
                        validation_results["errors"].append(f"Unknown task ID in dependency: {dep.get('to')}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating config: {str(e)}")
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    async def track_lifecycle(
        self,
        pattern_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track swarm lifecycle events.
        
        Args:
            pattern_id: ID of the swarm pattern
            event_type: Type of lifecycle event
            event_data: Optional event-specific data
            
        Returns:
            Dict containing tracking status
        """
        try:
            # Prepare event data
            event = {
                "id": str(uuid.uuid4()),
                "pattern_id": pattern_id,
                "type": event_type,
                "data": event_data or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Store event in Neo4j
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            CREATE (e:SwarmEvent {
                id: $id,
                type: $type,
                data: $data,
                timestamp: $timestamp
            })
            CREATE (p)-[:HAS_EVENT]->(e)
            RETURN e
            """
            
            await self.store.run_query(
                query,
                parameters=event
            )
            
            # Store in vector store for temporal analysis
            await self.memory_system.vector_store.store_vector(
                content=event,
                metadata={"type": "swarm_event"},
                layer="episodic"
            )
            
            return {
                "event_id": event["id"],
                "tracking_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error tracking lifecycle event: {str(e)}")
            return {
                "event_id": None,
                "tracking_status": "failed",
                "error": str(e)
            }
    
    async def get_pattern(
        self,
        pattern_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get swarm pattern by ID.
        
        Args:
            pattern_id: ID of the swarm pattern
            
        Returns:
            Pattern data if found, None otherwise
        """
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            RETURN p
            """
            
            result = await self.store.run_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            if result and result[0]:
                return dict(result[0]["p"])
            return None
            
        except Exception as e:
            logger.error(f"Error getting pattern: {str(e)}")
            return None
    
    async def list_patterns(
        self,
        pattern_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List swarm patterns with optional filtering.
        
        Args:
            pattern_type: Optional pattern type to filter by
            status: Optional status to filter by
            limit: Maximum number of patterns to return
            
        Returns:
            List of matching patterns
        """
        try:
            # Build query conditions
            conditions = []
            parameters = {"limit": limit}
            
            if pattern_type:
                conditions.append("p.type = $pattern_type")
                parameters["pattern_type"] = pattern_type
                
            if status:
                conditions.append("p.status = $status")
                parameters["status"] = status
            
            # Construct query
            query = "MATCH (p:SwarmPattern)"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " RETURN p LIMIT $limit"
            
            result = await self.store.run_query(query, parameters=parameters)
            
            return [dict(row["p"]) for row in result]
            
        except Exception as e:
            logger.error(f"Error listing patterns: {str(e)}")
            return []
    
    async def update_pattern(
        self,
        pattern_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update swarm pattern.
        
        Args:
            pattern_id: ID of the pattern to update
            updates: Dictionary of fields to update
            
        Returns:
            Dict containing update status
        """
        try:
            # Prepare update data
            update_data = {
                "pattern_id": pattern_id,
                "updates": updates,
                "updated_at": datetime.now().isoformat()
            }
            
            # Build update query
            set_clauses = []
            for key in updates:
                set_clauses.append(f"p.{key} = $updates.{key}")
            
            query = f"""
            MATCH (p:SwarmPattern {{id: $pattern_id}})
            SET {', '.join(set_clauses)},
                p.updated_at = $updated_at
            RETURN p
            """
            
            result = await self.store.run_query(
                query,
                parameters=update_data
            )
            
            if result and result[0]:
                return {
                    "update_status": "success",
                    "pattern": dict(result[0]["p"])
                }
            return {
                "update_status": "failed",
                "error": "Pattern not found"
            }
            
        except Exception as e:
            logger.error(f"Error updating pattern: {str(e)}")
            return {
                "update_status": "failed",
                "error": str(e)
            }
    
    async def delete_pattern(
        self,
        pattern_id: str
    ) -> Dict[str, Any]:
        """Delete swarm pattern.
        
        Args:
            pattern_id: ID of the pattern to delete
            
        Returns:
            Dict containing deletion status
        """
        try:
            # Delete pattern and its events
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            OPTIONAL MATCH (p)-[:HAS_EVENT]->(e:SwarmEvent)
            DETACH DELETE p, e
            """
            
            await self.store.run_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            # Delete from vector store
            await self.memory_system.vector_store.delete_vectors(
                filter_conditions={
                    "content.id": pattern_id,
                    "metadata.type": "swarm_pattern"
                }
            )
            
            return {
                "deletion_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error deleting pattern: {str(e)}")
            return {
                "deletion_status": "failed",
                "error": str(e)
            }
