"""Agent store implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class AgentStore(Neo4jBaseStore):
    """Store for managing agent data."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize store."""
        super().__init__(uri=uri, **kwargs)
        
    async def get_capabilities(self, agent_id: str) -> Optional[List[str]]:
        """Get agent capabilities."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            RETURN a.capabilities as capabilities
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            if result and result[0]:
                return result[0][0]
            return None
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            raise
    
    async def get_types(self) -> List[str]:
        """Get available agent types."""
        try:
            query = """
            MATCH (a:Agent)
            RETURN DISTINCT a.type as type
            """
            
            result = await self.driver.execute_query(query)
            return [record[0] for record in result if record[0]]
        except Exception as e:
            logger.error(f"Error getting types: {str(e)}")
            raise
    
    async def search_agents(
        self,
        capability: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for agents by capability and domain."""
        try:
            conditions = []
            parameters = {}
            
            if capability:
                conditions.append("$capability IN a.capabilities")
                parameters["capability"] = capability
            
            if domain:
                conditions.append("a.domain = $domain")
                parameters["domain"] = domain
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            query = f"""
            MATCH (a:Agent)
            WHERE {where_clause}
            RETURN a
            """
            
            result = await self.driver.execute_query(
                query,
                parameters=parameters
            )
            
            agents = []
            for record in result:
                agent_data = dict(record[0])
                # Remove Neo4j internal ID
                if "id" in agent_data:
                    del agent_data["id"]
                agents.append(agent_data)
            
            return agents
        except Exception as e:
            logger.error(f"Error searching agents: {str(e)}")
            raise
    
    async def get_history(self, agent_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get agent interaction history."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})-[:PARTICIPATED_IN]->(i:Interaction)
            RETURN i
            ORDER BY i.timestamp DESC
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            if not result:
                return None
            
            history = []
            for record in result:
                interaction_data = dict(record[0])
                # Remove Neo4j internal ID
                if "id" in interaction_data:
                    del interaction_data["id"]
                history.append(interaction_data)
            
            return history
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            raise
    
    async def get_metrics(self, agent_id: str) -> Optional[Dict[str, float]]:
        """Get agent performance metrics."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            RETURN a.metrics as metrics
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            if result and result[0]:
                return dict(result[0][0])
            return None
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise
    
    async def set_status(self, agent_id: str, status: str) -> None:
        """Set agent status."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            SET a.status = $status,
                a.updated_at = $updated_at
            """
            
            await self.driver.execute_query(
                query,
                parameters={
                    "agent_id": agent_id,
                    "status": status,
                    "updated_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error setting status: {str(e)}")
            raise
    
    async def get_status(self, agent_id: str) -> Optional[str]:
        """Get agent status."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            RETURN a.status as status
            """
            
            result = await self.driver.execute_query(
                query,
                parameters={"agent_id": agent_id}
            )
            
            if result and result[0]:
                return result[0][0]
            return None
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            raise
