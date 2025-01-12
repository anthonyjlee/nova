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

logger = logging.getLogger(__name__)

class TinyFactory:
    """Factory for creating and managing tiny agents."""
    
    def __init__(self):
        """Initialize factory."""
        self._agents: Dict[str, BaseAgent] = {}
        self._initialized = False
        self._init_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize factory."""
        if self._initialized:
            return
            
        async with self._init_lock:
            if self._initialized:
                return
                
            logger.info("Initializing TinyFactory")
            self._initialized = True
            
    async def create_agent(self, agent_type: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """Create a new agent of specified type."""
        if not self._initialized:
            await self.initialize()
            
        agent_id = str(uuid4())
        agent_config = config or {}
        
        # Map agent types to classes
        agent_classes = {
            "parsing": ParsingAgent,
            "coordination": CoordinationAgent,
            "analytics": AnalyticsAgent,
            "orchestration": OrchestrationAgent
        }
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = agent_classes[agent_type]
        agent = agent_class()
        agent.id = agent_id
        
        # Initialize agent
        await agent.initialize()
        
        # Store agent
        self._agents[agent_id] = agent
        
        return agent
        
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
        
    async def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Get all agents of specified type."""
        return [
            agent for agent in self._agents.values()
            if isinstance(agent, self._get_agent_class(agent_type))
        ]
        
    async def delete_agent(self, agent_id: str):
        """Delete agent by ID."""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            await agent.cleanup()
            del self._agents[agent_id]
            
    def _get_agent_class(self, agent_type: str):
        """Get agent class by type."""
        agent_classes = {
            "parsing": ParsingAgent,
            "coordination": CoordinationAgent,
            "analytics": AnalyticsAgent,
            "orchestration": OrchestrationAgent
        }
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        return agent_classes[agent_type]
        
    async def cleanup(self):
        """Clean up all agents."""
        for agent_id in list(self._agents.keys()):
            await self.delete_agent(agent_id)
