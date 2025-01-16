"""Factory for creating and managing tiny agents."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from uuid import uuid4

from .base import BaseAgent
from .specialized.parsing_agent import ParsingAgent
from .specialized.coordination_agent import CoordinationAgent
from .specialized.analytics_agent import AnalyticsAgent
from .specialized.orchestration_agent import OrchestrationAgent
from .specialized.schema_agent import SchemaAgent

logger = logging.getLogger(__name__)

class TinyFactory:
    """Factory for creating and managing tiny agents."""
    
    def __init__(self, memory_system=None, world=None):
        """Initialize factory."""
        self._agents: Dict[str, BaseAgent] = {}
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self.memory_system = memory_system
        self.world = world
        
    async def initialize(self):
        """Initialize factory."""
        if self._initialized:
            return
            
        async with self._init_lock:
            if self._initialized:
                return
                
            logger.info("Initializing TinyFactory")
            self._initialized = True
            
    async def create_agent(
        self,
        agent_type: str,
        domain: str,
        capabilities: List[str],
        supervisor_id: Optional[str] = None,
        attributes: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new agent with specified type and capabilities.
        
        Args:
            agent_type: Type of agent to create
            domain: Operating domain for the agent
            capabilities: List of agent capabilities
            supervisor_id: Optional ID of supervising agent
            attributes: Optional additional attributes
            
        Returns:
            Dict[str, Any]: Dictionary containing agent info including id, type, domain, and capabilities
        """
        if not self._initialized:
            await self.initialize()
            
        agent_id = str(uuid4())
        
        # Create agent config
        agent_config = {
            "name": f"{agent_type}_{agent_id[:8]}",
            "agent_type": agent_type,
            "domain": domain,
            "capabilities": capabilities,
            **(attributes or {})
        }
        
        # Create agent instance
        if agent_type == "test":
            # Use base agent class for test agents
            agent = BaseAgent(
                name=agent_id,
                agent_type=agent_type,
                memory_system=self.memory_system,
                world=self.world,
                attributes=attributes
            )
        else:
            # Map agent types to classes
            agent_classes = {
                "parsing": ParsingAgent,
                "coordination": CoordinationAgent,
                "analytics": AnalyticsAgent,
                "orchestration": OrchestrationAgent,
                "schema": SchemaAgent
            }
            
            # Import MetaAgent at runtime to avoid circular import
            if agent_type == "meta":
                from .specialized.meta_agent import MetaAgent
                agent_classes["meta"] = MetaAgent
            
            if agent_type not in agent_classes:
                raise ValueError(f"Unknown agent type: {agent_type}")
                
            agent_class = agent_classes[agent_type]
            agent = agent_class(
                name=agent_id,
                memory_system=self.memory_system,
                world=self.world,
                attributes=attributes
            )
        agent.id = agent_id
        
        # Initialize agent
        await agent.initialize()
        
        # Register agent with world if available
        if self.world:
            await self.world.register_agent(agent_id, capabilities)
        
        # Store agent
        self._agents[agent_id] = agent
        
        # Return object with id property
        return {
            "id": agent_id,
            "type": agent_type,
            "domain": domain,
            "capabilities": capabilities
        }
        
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
        
    async def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Get all agents of specified type."""
        if agent_type == "test":
            return [
                agent for agent in self._agents.values()
                if agent.agent_type == "test"
            ]
            
        # For specialized agents, use class-based check
        try:
            agent_class = self._get_agent_class(agent_type)
            return [
                agent for agent in self._agents.values()
                if isinstance(agent, agent_class)
            ]
        except ValueError:
            return []
        
    async def delete_agent(self, agent_id: str):
        """Delete agent by ID."""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            
            # Unregister from world if available
            if self.world:
                await self.world.unregister_agent(agent_id)
            
            # Cleanup and remove agent
            await agent.cleanup()
            del self._agents[agent_id]
            
    def _get_agent_class(self, agent_type: str):
        """Get agent class by type."""
        agent_classes = {
            "parsing": ParsingAgent,
            "coordination": CoordinationAgent,
            "analytics": AnalyticsAgent,
            "orchestration": OrchestrationAgent,
            "schema": SchemaAgent
        }
        
        # Import MetaAgent at runtime to avoid circular import
        if agent_type == "meta":
            from .specialized.meta_agent import MetaAgent
            agent_classes["meta"] = MetaAgent
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        return agent_classes[agent_type]
        
    async def cleanup(self):
        """Clean up all agents."""
        for agent_id in list(self._agents.keys()):
            await self.delete_agent(agent_id)
