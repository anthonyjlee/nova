"""Agent store for managing agent identities and capabilities."""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see metadata processing logs

class AgentStore(Neo4jBaseStore):
    """Store for managing agent identities."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize agent store."""
        super().__init__(uri=uri, **kwargs)
    
    async def store_agent(
        self,
        agent: Dict[str, Any]
    ) -> bool:
        """Store agent data.
        
        Args:
            agent: Agent data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract properties we want to store
            properties = {
                "id": agent["id"],
                "name": agent["name"],
                "type": agent["type"],
                "workspace": agent.get("workspace", "personal"),
                "domain": agent.get("domain"),
                "status": agent.get("status", "active"),
                "metadata": (lambda m: (
                    logger.debug(f"Serializing metadata for agent {agent['id']}: {m}"),
                    json.dumps(m)
                )[1])(agent.get("metadata", {})),  # Serialize metadata to JSON string
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            logger.info(f"Storing agent with properties: {properties}")
            
            query = """
            MERGE (a:Agent {id: $properties.id})
            SET a.name = $properties.name,
                a.type = $properties.type,
                a.workspace = $properties.workspace,
                a.domain = $properties.domain,
                a.status = $properties.status,
                a.metadata = $properties.metadata,
                a.created_at = $properties.created_at,
                a.updated_at = $properties.updated_at
            RETURN a
            """
            
            try:
                result = await self.run_query(
                    query,
                    parameters={"properties": properties}
                )
                logger.info(f"Store result: {result}")
                return bool(result and result[0])
            except Exception as e:
                logger.error(f"Neo4j query error: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"Error storing agent: {str(e)}")
            return False
            
    async def get_capabilities(
        self,
        agent_id: str
    ) -> List[str]:
        """Get agent capabilities.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of capability strings
        """
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            RETURN a.capabilities as capabilities
            """
            
            result = await self.run_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            if result and result[0]:
                return result[0]["capabilities"] or []
            return []
            
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            return []
    
    async def get_types(self) -> List[str]:
        """Get available agent types.
        
        Returns:
            List of agent type strings
        """
        try:
            query = """
            MATCH (a:Agent)
            RETURN DISTINCT a.type as type
            """
            
            result = await self.run_query(query)
            return [row["type"] for row in result if row["type"]]
            
        except Exception as e:
            logger.error(f"Error getting types: {str(e)}")
            return []
    
    async def search_agents(
        self,
        capability: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for agents by capability and domain.
        
        Args:
            capability: Optional capability to filter by
            domain: Optional domain to filter by
            
        Returns:
            List of matching agent data
        """
        try:
            # Build query conditions
            conditions = []
            parameters = {}
            
            if capability:
                conditions.append("$capability IN a.capabilities")
                parameters["capability"] = capability
                
            if domain:
                conditions.append("a.domain = $domain")
                parameters["domain"] = domain
            
            # Construct query
            query = "MATCH (a:Agent)"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " RETURN a"
            
            result = await self.run_query(query, parameters=parameters)
            
            # Convert nodes to dictionaries and deserialize metadata
            agents = []
            for row in result:
                agent_data = dict(row["a"])
                try:
                    metadata_str = agent_data.get("metadata")
                    logger.debug(f"Deserializing metadata for agent {agent_data.get('id', 'unknown')}: {metadata_str}")
                    if metadata_str:
                        agent_data["metadata"] = json.loads(metadata_str)
                        logger.debug(f"Successfully deserialized metadata: {agent_data['metadata']}")
                    else:
                        agent_data["metadata"] = {}
                        logger.debug("No metadata found, using empty dict")
                except Exception as e:
                    logger.warning(f"Failed to process metadata for agent {agent_data.get('id', 'unknown')}: {e}")
                    agent_data["metadata"] = {}
                agents.append(agent_data)
            return agents
            
        except Exception as e:
            logger.error(f"Error searching agents: {str(e)}")
            return []
    
    async def get_history(
        self,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """Get agent interaction history.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of interaction records
        """
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})-[:HAS_INTERACTION]->(i:Interaction)
            RETURN i
            ORDER BY i.timestamp DESC
            """
            
            result = await self.run_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            return [dict(row["i"]) for row in result]
            
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return []
    
    async def get_metrics(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get agent performance metrics.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary of performance metrics
        """
        try:
            # Get interaction metrics
            interactions_query = """
            MATCH (a:Agent {id: $agent_id})-[:HAS_INTERACTION]->(i:Interaction)
            WITH a,
                 count(i) as total_interactions,
                 sum(CASE WHEN i.status = 'success' THEN 1 ELSE 0 END) as successful_interactions,
                 avg(i.response_time) as avg_response_time
            RETURN total_interactions, successful_interactions, avg_response_time
            """
            
            interactions_result = await self.run_query(
                interactions_query,
                parameters={"agent_id": agent_id}
            )
            
            # Get memory metrics
            memory_query = """
            MATCH (a:Agent {id: $agent_id})
            RETURN a.memory_usage as memory_usage
            """
            
            memory_result = await self.run_query(
                memory_query,
                parameters={"agent_id": agent_id}
            )
            
            # Calculate metrics
            if interactions_result and interactions_result[0]:
                total = interactions_result[0]["total_interactions"]
                successful = interactions_result[0]["successful_interactions"]
                avg_response = interactions_result[0]["avg_response_time"]
                
                metrics = {
                    "task_completion_rate": successful / total if total > 0 else 0,
                    "average_response_time": avg_response or 0,
                    "total_interactions": total,
                    "successful_interactions": successful
                }
                
                # Add memory usage if available
                if memory_result and memory_result[0]:
                    metrics["memory_utilization"] = memory_result[0]["memory_usage"] or 0
                
                return metrics
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return {}
    
    async def set_status(
        self,
        agent_id: str,
        status: str
    ) -> bool:
        """Set agent status.
        
        Args:
            agent_id: ID of the agent
            status: New status value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            SET a.status = $status,
                a.updated_at = $updated_at
            RETURN a
            """
            
            result = await self.run_query(
                query,
                parameters={
                    "agent_id": agent_id,
                    "status": status,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            return bool(result and result[0])
            
        except Exception as e:
            logger.error(f"Error setting status: {str(e)}")
            return False
    
    async def get_status(
        self,
        agent_id: str
    ) -> Optional[str]:
        """Get agent status.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Status string if found, None otherwise
        """
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            RETURN a.status as status
            """
            
            result = await self.run_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            if result and result[0]:
                return result[0]["status"]
            return None
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return None
            
    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents.
        
        Returns:
            List of agent data dictionaries
        """
        try:
            # First check if we can connect
            try:
                await self.connect()
                logger.info("Successfully connected to Neo4j")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                raise

            # Simple query to get all agents
            query = "MATCH (a:Agent) RETURN a"
            logger.info("Executing query: %s", query)
            
            result = await self.run_query(query)
            logger.info("Query result: %s", result)
            
            # Convert nodes to dictionaries and deserialize metadata
            agents = []
            for row in result:
                # Get node properties
                node = row["a"]
                agent_data = dict(node)
                
                # Use name as id if no explicit id is set
                if "id" not in agent_data:
                    agent_data["id"] = agent_data.get("name", str(node.id))
                    # Also update the node in Neo4j
                    try:
                        update_query = """
                        MATCH (a:Agent {name: $name})
                        WHERE NOT EXISTS(a.id)
                        SET a.id = $id
                        """
                        await self.run_query(
                            update_query,
                            parameters={
                                "name": agent_data["name"],
                                "id": agent_data["id"]
                            }
                        )
                        logger.debug(f"Updated agent {agent_data['name']} with id {agent_data['id']}")
                    except Exception as e:
                        logger.warning(f"Failed to update agent {agent_data['name']} with id: {e}")
                
                # Try to get metadata from JSON string first
                try:
                    metadata_str = agent_data.get("metadata")
                    logger.debug(f"Deserializing metadata for agent {agent_data.get('id', 'unknown')}: {metadata_str}")
                    if metadata_str:
                        agent_data["metadata"] = json.loads(metadata_str)
                        logger.debug(f"Successfully deserialized metadata: {agent_data['metadata']}")
                    else:
                        # Fallback to individual fields
                        agent_data["metadata"] = {
                            "type": agent_data.get("type"),
                            "description": agent_data.get("description"),
                            "domain": agent_data.get("domain"),
                            "created_at": agent_data.get("created_at"),
                            "status": agent_data.get("status", "active")
                        }
                        logger.debug(f"Using fallback metadata: {agent_data['metadata']}")
                except Exception as e:
                    # Fallback to empty metadata
                    logger.warning(f"Failed to process metadata for agent {agent_data.get('id', 'unknown')}: {e}")
                    agent_data["metadata"] = {}
                logger.info("Agent data: %s", agent_data)
                agents.append(agent_data)
            
            return agents
            
        except Exception as e:
            logger.error(f"Error getting all agents: {str(e)}")
            return []
