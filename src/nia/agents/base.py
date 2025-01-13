"""Base agent implementations."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from nia.core.types.memory_types import Memory, MemoryType, EpisodicMemory

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str = None,
        agent_type: str = None,
        memory_system: Optional['TwoLayerMemorySystem'] = None,
        world: Optional['NIAWorld'] = None,
        attributes: Optional[Dict] = None
    ):
        """Initialize agent."""
        self.name = name or agent_type
        self.agent_type = agent_type or name
        self.logger = logging.getLogger(f"agent.{self.name}")
        self.memory_system = memory_system
        self.world = world
        self.attributes = attributes or {}
        
    async def store_memory(
        self,
        content: Any,
        importance: float = 0.7,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        concepts: Optional[List[Dict]] = None,
        relationships: Optional[List[Dict]] = None
    ) -> str:
        """Store memory in the memory system."""
        if self.memory_system:
            memory = EpisodicMemory(
                content=content,
                type=MemoryType.EPISODIC,
                timestamp=datetime.now().isoformat(),
                importance=importance,
                context=context or {},
                metadata=metadata or {},
                concepts=concepts or [],
                relationships=relationships or []
            )
            return await self.memory_system.episodic.store_memory(memory)
        return ""
        
    async def recall_memories(
        self,
        query: Dict,
        limit: int = 10
    ) -> List[EpisodicMemory]:
        """Recall memories from the memory system."""
        if self.memory_system:
            results = await self.memory_system.query_episodic(query)
            # Convert results to EpisodicMemory objects if they aren't already
            converted_results = []
            for r in results:
                if isinstance(r, EpisodicMemory):
                    converted_results.append(r)
                elif isinstance(r, dict):
                    converted_results.append(EpisodicMemory(**r))
                else:
                    # Try to convert to dict first
                    try:
                        r_dict = dict(r)
                        converted_results.append(EpisodicMemory(**r_dict))
                    except Exception as e:
                        self.logger.error(f"Failed to convert memory result: {str(e)}")
                        continue
            return converted_results
        return []
        
    async def reflect(self) -> None:
        """Reflect on memories and consolidate knowledge."""
        if not self.memory_system:
            raise Exception("No memory system available")
        try:
            await self.memory_system.consolidate_memories()
        except Exception as e:
            self.logger.error(f"Failed to consolidate memories: {str(e)}")
            raise Exception(f"Consolidation failed: {str(e)}")
            
    async def query_knowledge(self, query: Dict) -> List[Dict]:
        """Query semantic knowledge."""
        if self.memory_system and hasattr(self.memory_system, 'semantic'):
            return await self.memory_system.semantic.query_knowledge(query)
        return []

class CoordinationAgent(BaseAgent):
    """Agent for coordinating other agents."""
    
    def __init__(self):
        """Initialize coordination agent."""
        super().__init__("CoordinationAgent")
        self.active_agents = {}
        
    async def handle_message(self, message: Dict):
        """Handle incoming message."""
        self.logger.debug(f"Handling message: {message}")
        # Placeholder for actual message handling
        return {}

class AnalyticsAgent(BaseAgent):
    """Agent for analytics and metrics."""
    
    def __init__(self):
        """Initialize analytics agent."""
        super().__init__("AnalyticsAgent")
        self.metrics = {}
        
    async def track_metric(self, name: str, value: Any):
        """Track a metric."""
        self.logger.debug(f"Tracking metric {name}: {value}")
        self.metrics[name] = value

class ParsingAgent(BaseAgent):
    """Agent for parsing and processing input."""
    
    def __init__(self):
        """Initialize parsing agent."""
        super().__init__("ParsingAgent")
        
    async def parse(self, content: str) -> Dict:
        """Parse input content."""
        self.logger.debug(f"Parsing content: {content}")
        return {"parsed": content}

class OrchestrationAgent(BaseAgent):
    """Agent for orchestrating other agents."""
    
    def __init__(self):
        """Initialize orchestration agent."""
        super().__init__("OrchestrationAgent")
        self.active_tasks = {}
        
    async def orchestrate(self, task: Dict) -> Dict:
        """Orchestrate a task across agents."""
        self.logger.debug(f"Orchestrating task: {task}")
        task_id = str(hash(str(task)))
        self.active_tasks[task_id] = task
        return {"task_id": task_id, "status": "orchestrating"}
