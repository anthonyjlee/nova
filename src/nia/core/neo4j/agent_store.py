"""Agent store implementation."""

from typing import Dict, Any, List, Optional
from .base_store import Neo4jBaseStore

class AgentStore(Neo4jBaseStore):
    """Store for agent operations."""
    
    async def initialize(self):
        """Initialize agent store."""
        await self.connect()
        
    async def create_agent(self, agent_id: str, agent_type: str, properties: Dict[str, Any]):
        """Create an agent node."""
        query = """
        CREATE (a:Agent {id: $agent_id, type: $agent_type})
        SET a += $properties
        RETURN a
        """
        return await self.run_query(query, {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "properties": properties
        })
        
    async def get_agent(self, agent_id: str):
        """Get agent by ID."""
        query = """
        MATCH (a:Agent)
        WHERE a.id = $agent_id
        RETURN a
        """
        return await self.run_query(query, {"agent_id": agent_id})
        
    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents."""
        query = """
        MATCH (a:Agent)
        RETURN a
        ORDER BY a.created_at DESC
        """
        result = await self.run_query(query)
        # Convert Neo4j nodes to dictionaries
        agents = []
        for record in result:
            if record.get("a"):
                agent = record["a"]
                if isinstance(agent, dict):
                    agents.append(agent)
                else:
                    # Handle Neo4j node object if needed
                    agents.append(dict(agent))
        return agents
        
    async def update_agent(self, agent_id: str, properties: Dict[str, Any]):
        """Update agent properties."""
        query = """
        MATCH (a:Agent)
        WHERE a.id = $agent_id
        SET a += $properties
        RETURN a
        """
        return await self.run_query(query, {
            "agent_id": agent_id,
            "properties": properties
        })
        
    async def delete_agent(self, agent_id: str):
        """Delete agent by ID."""
        query = """
        MATCH (a:Agent)
        WHERE a.id = $agent_id
        DETACH DELETE a
        """
        return await self.run_query(query, {"agent_id": agent_id})
        
    async def get_agents_by_type(self, agent_type: str):
        """Get all agents of a specific type."""
        query = """
        MATCH (a:Agent)
        WHERE a.type = $agent_type
        RETURN a
        """
        return await self.run_query(query, {"agent_type": agent_type})
        
    async def create_agent_relationship(self, from_id: str, to_id: str, rel_type: str, properties: Optional[Dict[str, Any]] = None):
        """Create a relationship between agents."""
        query = """
        MATCH (from:Agent), (to:Agent)
        WHERE from.id = $from_id AND to.id = $to_id
        CREATE (from)-[r:$rel_type]->(to)
        SET r = $properties
        RETURN r
        """
        return await self.run_query(query, {
            "from_id": from_id,
            "to_id": to_id,
            "rel_type": rel_type,
            "properties": properties or {}
        })
        
    async def get_agent_relationships(self, agent_id: str, rel_type: Optional[str] = None, direction: str = "BOTH"):
        """Get agent relationships."""
        if direction not in ["INCOMING", "OUTGOING", "BOTH"]:
            raise ValueError("Invalid direction. Must be INCOMING, OUTGOING, or BOTH")
            
        if direction == "INCOMING":
            pattern = "<-[r]-"
        elif direction == "OUTGOING":
            pattern = "-[r]->"
        else:
            pattern = "-[r]-"
            
        rel_type_str = f":{rel_type}" if rel_type else ""
        
        query = f"""
        MATCH (a:Agent)
        WHERE a.id = $agent_id
        MATCH (a){pattern}(other:Agent){rel_type_str}
        RETURN r, other
        """
        return await self.run_query(query, {"agent_id": agent_id})
        
    async def get_agent_capabilities(self, agent_id: str):
        """Get agent capabilities."""
        query = """
        MATCH (a:Agent)-[:HAS_CAPABILITY]->(c:Capability)
        WHERE a.id = $agent_id
        RETURN c
        """
        return await self.run_query(query, {"agent_id": agent_id})
        
    async def add_agent_capability(self, agent_id: str, capability: Dict[str, Any]):
        """Add a capability to an agent."""
        query = """
        MATCH (a:Agent)
        WHERE a.id = $agent_id
        CREATE (c:Capability)
        SET c = $capability
        CREATE (a)-[:HAS_CAPABILITY]->(c)
        RETURN c
        """
        return await self.run_query(query, {
            "agent_id": agent_id,
            "capability": capability
        })
        
    async def remove_agent_capability(self, agent_id: str, capability_id: str):
        """Remove a capability from an agent."""
        query = """
        MATCH (a:Agent)-[r:HAS_CAPABILITY]->(c:Capability)
        WHERE a.id = $agent_id AND c.id = $capability_id
        DELETE r, c
        """
        return await self.run_query(query, {
            "agent_id": agent_id,
            "capability_id": capability_id
        })
