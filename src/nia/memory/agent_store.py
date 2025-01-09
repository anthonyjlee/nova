"""Agent store for managing agent identities and capabilities."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class AgentStore(Neo4jBaseStore):
    """Store for managing agent identities."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize agent store."""
        super().__init__(uri=uri, **kwargs)
    
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
            
            return [dict(row["a"]) for row in result]
            
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
            query = """
            MATCH (a:Agent)
            OPTIONAL MATCH (a)-[:SUPERVISES]->(s:Agent)
            OPTIONAL MATCH (a)-[:ASSIGNED_TO]->(t:Task)
            WITH a,
                 collect(DISTINCT s.id) as supervised_agents,
                 collect(DISTINCT t.id) as assigned_tasks
            RETURN {
                id: toString(elementId(a)),
                name: a.name,
                type: a.type,
                status: a.status,
                domain: a.domain,
                capabilities: a.capabilities,
                created_at: toString(a.created_at),
                supervisor_id: a.supervisor_id,
                supervised_agents: supervised_agents,
                assigned_tasks: assigned_tasks
            } as agent
            """
            
            result = await self.run_query(query)
            return [row["agent"] for row in result]
            
        except Exception as e:
            logger.error(f"Error getting all agents: {str(e)}")
            return []
