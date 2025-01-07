"""TinyTroupe world environment for NIA."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from tinytroupe import TinyWorld
from ..memory.two_layer import TwoLayerMemorySystem
from ..core.types.memory_types import Memory, EpisodicMemory

logger = logging.getLogger(__name__)

class NIAWorld(TinyWorld):
    """World environment for NIA agents."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NIAWorld, cls).__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        name: str = "NIAWorld",
        memory_system: Optional[TwoLayerMemorySystem] = None
    ):
        """Initialize world with memory system."""
        if not hasattr(self, '_initialized'):
            super().__init__(name)
            self.memory = memory_system
            self.state = {
                "tasks_paused": False,
                "conversation_enabled": True,
                "active_agents": set(),
                "pending_tasks": []
            }
            self.resources = {}
            self.task_domains = {}
            self._initialized = True
        
    def define_resource(self, name: str, value: Any):
        """Define a world resource."""
        self.resources[name] = {
            "value": value,
            "created_at": datetime.now(),
            "accessed_by": set()
        }
        
    def get_resource(self, name: str, agent_name: str = None) -> Any:
        """Get a world resource."""
        if name not in self.resources:
            return None
            
        resource = self.resources[name]
        if agent_name:
            resource["accessed_by"].add(agent_name)
            
        return resource["value"]
        
    async def execute_action(self, agent: 'BaseAgent', action: str, **kwargs) -> Any:
        """Execute an agent action."""
        # Log action
        if self.memory:
            await self.memory.store_experience(
                EpisodicMemory(
                    content={
                        "action": action,
                        "agent": agent.name,
                        "parameters": kwargs
                    },
                    source="world",
                    importance=0.6,
                    context={
                        "type": "action",
                        "world": self.name
                    }
                )
            )
        
        # Check if action is allowed
        if self.state["tasks_paused"] and action != "converse":
            logger.warning(f"Tasks are paused. Only conversation is allowed.")
            return None
            
        # Execute action based on type
        if action == "converse":
            return await self._handle_conversation(agent, **kwargs)
        elif action == "observe":
            return await self._handle_observation(agent, **kwargs)
        elif action == "use_resource":
            return self._handle_resource_use(agent, **kwargs)
        else:
            return await self._handle_custom_action(agent, action, **kwargs)
            
    async def _handle_conversation(self, agent: 'BaseAgent', message: str, target: str = None, **kwargs) -> Dict:
        """Handle conversation action."""
        if not self.state["conversation_enabled"]:
            logger.warning("Conversation is disabled")
            return None
            
        response = {
            "type": "conversation",
            "from": agent.name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if target:
            target_agent = self.get_agent(target)
            if target_agent:
                response["to"] = target
                # Let target agent process message
                await target_agent.observe({
                    "type": "message",
                    "from": agent.name,
                    "content": message
                })
                
        return response
        
    async def _handle_observation(self, agent: 'BaseAgent', observation: Dict, **kwargs) -> Dict:
        """Handle observation action."""
        # Process observation
        await agent.observe(observation)
        
        # Notify relevant agents
        if "notify" in kwargs:
            for target in kwargs["notify"]:
                target_agent = self.get_agent(target)
                if target_agent:
                    await target_agent.observe(observation)
                    
        return {
            "type": "observation",
            "agent": agent.name,
            "observation": observation,
            "timestamp": datetime.now().isoformat()
        }
        
    def _handle_resource_use(self, agent: 'BaseAgent', resource: str, **kwargs) -> Any:
        """Handle resource use action."""
        return self.get_resource(resource, agent.name)
        
    async def _handle_custom_action(self, agent: 'BaseAgent', action: str, **kwargs) -> Any:
        """Handle custom action types."""
        # Default implementation - override for custom actions
        logger.warning(f"Unhandled action type: {action}")
        return None
        
    async def pause_tasks(self):
        """Pause task execution while maintaining conversations."""
        self.state["tasks_paused"] = True
        
        if self.memory:
            await self.memory.store_experience(
                EpisodicMemory(
                    content="Tasks paused",
                    source="world",
                    importance=0.7,
                    context={
                        "type": "system",
                        "world": self.name
                    }
                )
            )
            
    async def resume_tasks(self):
        """Resume task execution."""
        self.state["tasks_paused"] = False
        
        if self.memory:
            await self.memory.store_experience(
                EpisodicMemory(
                    content="Tasks resumed",
                    source="world",
                    importance=0.7,
                    context={
                        "type": "system",
                        "world": self.name
                    }
                )
            )
            
        # Process any pending tasks
        while self.state["pending_tasks"]:
            task = self.state["pending_tasks"].pop(0)
            await self._process_task(task)
            
    async def _process_task(self, task: Dict):
        """Process a pending task."""
        if "agent" in task and "action" in task:
            agent = self.get_agent(task["agent"])
            if agent:
                await self.execute_action(
                    agent,
                    task["action"],
                    **(task.get("parameters", {}))
                )
                
    def register_domain(self, domain: str, agents: List[str] = None):
        """Register a task domain."""
        self.task_domains[domain] = {
            "agents": agents or [],
            "created_at": datetime.now(),
            "active": True
        }
        
    def get_domain_agents(self, domain: str) -> List[str]:
        """Get agents registered to a domain."""
        return self.task_domains.get(domain, {}).get("agents", [])
