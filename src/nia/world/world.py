"""World environment for agents."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from uuid import uuid4

logger = logging.getLogger(__name__)

class World:
    """World environment for agents."""
    
    def __init__(self):
        """Initialize world."""
        self._state: Dict[str, Any] = {}
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._observers: Dict[str, callable] = {}
        
    async def initialize(self):
        """Initialize world."""
        if self._initialized:
            return
            
        async with self._init_lock:
            if self._initialized:
                return
                
            logger.info("Initializing World")
            
            # Initialize default state
            self._state = {
                "agents": {},
                "tasks": {},
                "resources": {},
                "environment": {
                    "time": None,
                    "active_agents": set(),
                    "available_resources": set()
                }
            }
            
            self._initialized = True
            logger.info("World initialization complete")
            
    async def get_state(self) -> Dict[str, Any]:
        """Get current world state."""
        if not self._initialized:
            await self.initialize()
        return self._state
        
    async def update_state(self, updates: Dict[str, Any]):
        """Update world state."""
        if not self._initialized:
            await self.initialize()
            
        # Deep update state
        self._deep_update(self._state, updates)
        
        # Notify observers
        await self._notify_observers(updates)
        
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep update dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
                
    async def register_agent(self, agent_id: str, capabilities: List[str]):
        """Register agent in world."""
        if not self._initialized:
            await self.initialize()
            
        self._state["agents"][agent_id] = {
            "id": agent_id,
            "capabilities": capabilities,
            "status": "idle",
            "current_task": None
        }
        
        self._state["environment"]["active_agents"].add(agent_id)
        
    async def unregister_agent(self, agent_id: str):
        """Unregister agent from world."""
        if not self._initialized:
            await self.initialize()
            
        if agent_id in self._state["agents"]:
            del self._state["agents"][agent_id]
            
        if agent_id in self._state["environment"]["active_agents"]:
            self._state["environment"]["active_agents"].remove(agent_id)
            
    async def add_task(self, task: Dict[str, Any]):
        """Add task to world."""
        if not self._initialized:
            await self.initialize()
            
        task_id = task.get("id", str(uuid4()))
        self._state["tasks"][task_id] = task
        
    async def remove_task(self, task_id: str):
        """Remove task from world."""
        if not self._initialized:
            await self.initialize()
            
        if task_id in self._state["tasks"]:
            del self._state["tasks"][task_id]
            
    async def add_resource(self, resource: Dict[str, Any]):
        """Add resource to world."""
        if not self._initialized:
            await self.initialize()
            
        resource_id = resource.get("id", str(uuid4()))
        self._state["resources"][resource_id] = resource
        self._state["environment"]["available_resources"].add(resource_id)
        
    async def remove_resource(self, resource_id: str):
        """Remove resource from world."""
        if not self._initialized:
            await self.initialize()
            
        if resource_id in self._state["resources"]:
            del self._state["resources"][resource_id]
            
        if resource_id in self._state["environment"]["available_resources"]:
            self._state["environment"]["available_resources"].remove(resource_id)
            
    async def add_observer(self, observer_id: str, callback: callable):
        """Add state observer."""
        self._observers[observer_id] = callback
        
    async def remove_observer(self, observer_id: str):
        """Remove state observer."""
        if observer_id in self._observers:
            del self._observers[observer_id]
            
    async def _notify_observers(self, updates: Dict[str, Any]):
        """Notify observers of state updates."""
        for callback in self._observers.values():
            try:
                await callback(updates)
            except Exception as e:
                logger.error(f"Error notifying observer: {str(e)}")
                
    async def execute_action(self, agent: Any, action: str, **kwargs) -> Any:
        """Execute an action in the world.
        
        Args:
            agent: Agent executing the action
            action: Action to execute
            **kwargs: Additional action parameters
            
        Returns:
            Result of the action
        """
        if not self._initialized:
            await self.initialize()
            
        # Log action
        logger.debug(f"Agent {agent.name} executing action: {action}")
        
        # Update agent status
        if agent.name in self._state["agents"]:
            self._state["agents"][agent.name]["status"] = "executing"
            
        try:
            # Handle different action types
            if action == "query_state":
                return await self.get_state()
            elif action == "update_state":
                await self.update_state(kwargs.get("updates", {}))
                return True
            elif action == "register":
                await self.register_agent(
                    agent.name,
                    kwargs.get("capabilities", [])
                )
                return True
            elif action == "unregister":
                await self.unregister_agent(agent.name)
                return True
            else:
                logger.warning(f"Unknown action: {action}")
                return None
                
        finally:
            # Reset agent status
            if agent.name in self._state["agents"]:
                self._state["agents"][agent.name]["status"] = "idle"
