"""Nova orchestrator implementation using TinyTroupe."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .core.meta import MetaAgent, MetaResult
from ..world.environment import NIAWorld
from ..memory.two_layer import TwoLayerMemorySystem
from ..memory.types.memory_types import Memory, EpisodicMemory, TaskOutput, MemoryType
from ..agents.base import BaseAgent

logger = logging.getLogger(__name__)

class Nova(MetaAgent):
    """Nova orchestrator for coordinating agents."""
    
    def __init__(
        self,
        name: str = "Nova",
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        llm: Optional['LLMInterface'] = None
    ):
        """Initialize Nova orchestrator."""
        self.name = name  # Set name first
        self.memory_system = memory_system  # Store memory system
        
        # Initialize MetaAgent with memory system components
        super().__init__(
            llm=llm,
            store=memory_system.semantic.driver if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            agents={}  # Will be populated as agents are spawned
        )
        
        self.world = world or NIAWorld(memory_system=memory_system)
        self._initialize_tinytroupe_attributes()
        
        # Register with world if name is unique
        if self.world:
            existing_names = [agent.name for agent in self.world.agents] if hasattr(self.world, 'agents') else []
            if self.name not in existing_names:
                self.world.add_agent(self)
            else:
                # Generate unique name by appending number
                i = 1
                while f"{self.name}_{i}" in existing_names:
                    i += 1
                self.name = f"{self.name}_{i}"
                self.world.add_agent(self)
            
    def _initialize_tinytroupe_attributes(self):
        """Initialize TinyTroupe-specific attributes."""
        self.occupation = "Meta Orchestrator"
        self.desires = [
            "Coordinate agents effectively",
            "Maintain system coherence",
            "Enable emergent behavior",
            "Preserve conversation during tasks"
        ]
        self.emotions = {
            "baseline": "focused",
            "towards_agents": "supportive"
        }
        
    async def recall_memories(
        self,
        query: Dict,
        limit: int = 10
    ) -> List[Memory]:
        """Recall memories from the memory system."""
        if self.memory_system:
            return await self.memory_system.query_memories(query, limit=limit)
        return []

    async def store_memory(
        self,
        content: Any,
        importance: float = 0.7,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        """Store memory in the memory system."""
        if self.memory_system:
            await self.memory_system.store_experience(
                EpisodicMemory(
                    content=str(content) if not isinstance(content, str) else content,
                    type=MemoryType.EPISODIC,
                    timestamp=datetime.now().isoformat(),
                    importance=importance,
                    context=context or {},
                    metadata=metadata or {}
                )
            )

    async def spawn_agent(
        self,
        agent_type: str,
        name: Optional[str] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ) -> BaseAgent:
        """Spawn a new agent."""
        # Generate name if not provided
        if name is None:
            name = f"{agent_type}_{len(self.world.agents)}"
            
        # Create agent
        agent = BaseAgent(
            name=name,
            memory_system=self.memory_system,
            world=self.world,
            attributes=attributes
        )
        
        # Register with world
        self.world.add_agent(agent)
        
        # Register domain if provided
        if domain:
            self.world.register_domain(domain, [agent.name])
            
        # Log agent creation
        await self.store_memory(
            content={
                "type": "agent_creation",
                "agent": name,
                "agent_type": agent_type,
                "domain": domain
            },
            importance=0.7,
            context={"type": "system"}
        )
        
        return agent
        
    async def handle_conversation(
        self,
        message: str,
        source: Optional[str] = None,
        target: Optional[str] = None
    ) -> Dict:
        """Handle conversation between agents."""
        # Process through MetaAgent first
        result = await self.process_interaction(message)
        
        # Then handle through world if needed
        if target:
            await self.world.execute_action(
                self,
                "converse",
                message=result.response,
                target=target
            )
            
        return {
            "type": "conversation",
            "message": result.response,
            "source": source or self.name,
            "target": target,
            "result": result
        }
        
    async def start_task(
        self,
        task: Dict,
        domain: Optional[str] = None
    ) -> str:
        """Start a new task."""
        task_id = str(hash(f"{task}_{datetime.now().isoformat()}"))
        
        # Store task in memory
        await self.store_memory(
            content={
                "type": "task_start",
                "task_id": task_id,
                "task": task,
                "domain": domain
            },
            importance=0.8,
            context={"type": "task"}
        )
        
        # Get or create domain agents
        agents = []
        if domain:
            existing_agents = self.world.get_domain_agents(domain)
            if existing_agents:
                agents = [self.world.get_agent(name) for name in existing_agents]
            else:
                # Spawn new agent for domain
                agent = await self.spawn_agent(
                    agent_type="TaskAgent",
                    domain=domain,
                    attributes={
                        "task_id": task_id,
                        "task": task
                    }
                )
                agents = [agent]
                
        # Assign task to agents
        for agent in agents:
            await self.world.execute_action(
                agent,
                "process_task",
                task_id=task_id,
                task=task
            )
            
        return task_id
        
    async def pause_tasks(self):
        """Pause task execution while maintaining conversations."""
        await self.world.pause_tasks()
        
    async def resume_tasks(self):
        """Resume task execution."""
        await self.world.resume_tasks()
        
    async def detect_emergent_tasks(self, conversation: str) -> List[Dict]:
        """Detect potential emergent tasks from conversation."""
        # Get recent context
        recent_memories = await self.recall_memories(
            query={"time_range": {"minutes": 30}},
            limit=10
        )
        
        # Look for task indicators
        tasks = []
        indicators = ["need to", "should", "must", "let's", "we could"]
        
        for indicator in indicators:
            if indicator in conversation.lower():
                # Extract task details
                task = {
                    "type": "emergent",
                    "source": "conversation",
                    "description": conversation,
                    "context": [m.content for m in recent_memories],
                    "importance": 0.7
                }
                tasks.append(task)
                
                # Store potential task
                await self.store_memory(
                    content={
                        "type": "emergent_task",
                        "task": task
                    },
                    importance=0.7,
                    context={"type": "task_detection"}
                )
                
        return tasks
        
    async def get_task_status(self, task_id: str) -> Dict:
        """Get status of a task."""
        # Query task memories
        memories = await self.recall_memories(
            query={
                "filter": {
                    "content.task_id": task_id
                }
            }
        )
        
        if not memories:
            return {"status": "unknown"}
            
        # Analyze task progression
        latest = max(memories, key=lambda m: m.timestamp)
        
        return {
            "status": self._determine_task_status(latest),
            "last_update": latest.timestamp,
            "memories": len(memories)
        }
        
    def _determine_task_status(self, memory: Memory) -> str:
        """Determine task status from memory."""
        content = memory.content
        if isinstance(content, dict):
            if content.get("type") == "task_complete":
                return "completed"
            elif content.get("type") == "task_error":
                return "error"
            elif content.get("type") == "task_start":
                return "in_progress"
        return "unknown"
