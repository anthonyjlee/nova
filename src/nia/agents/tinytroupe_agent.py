"""TinyTroupe agent base implementation."""

import logging
import uuid
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from .tiny_person import TinyPerson
from .base import BaseAgent as MemoryBaseAgent
from ..world.environment import NIAWorld
from ..memory.two_layer import TwoLayerMemorySystem
from ..core.types.memory_types import Memory, EpisodicMemory, SemanticMemory, AgentResponse, MemoryType
from ..config import validate_agent_config

logger = logging.getLogger(__name__)

class TinyTroupeAgent(TinyPerson, MemoryBaseAgent):
    """Base agent implementation combining TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        agent_type: str = "base",
        domain: str = "professional"
    ):
        """Initialize agent with both TinyTroupe and memory capabilities."""
        # Validate configuration
        config = {
            "name": name,
            "agent_type": agent_type,
            "domain": "professional"
        }
        validate_agent_config(agent_type, config)
        
        # Initialize TinyPerson
        TinyPerson.__init__(self, name)
        
        # Initialize MemoryBaseAgent
        MemoryBaseAgent.__init__(
            self,
            name=name,
            agent_type=agent_type,
            memory_system=memory_system,
            world=world,
            attributes=attributes
        )
        
        # Store additional attributes
        self.world = world
        self._initialize_attributes(attributes)
        
    def _initialize_attributes(self, attributes: Optional[Dict] = None):
        """Initialize TinyTroupe attributes."""
        attributes = attributes or {}
        self._configuration = {
            "occupation": attributes.get("occupation", "Agent"),
            "current_goals": attributes.get("desires", ["Help users", "Learn and improve"]),
            "current_emotions": attributes.get("emotions", {"baseline": "neutral"}),
            "memory_references": {},  # Initialize empty memory references
            "capabilities": attributes.get("capabilities", [])
        }
        
    def define(self, occupation: str = None, desires: List[str] = None, 
              emotions: Dict[str, str] = None, domain: str = None,
              capabilities: List[str] = None):
        """Define or update agent attributes.
        
        Args:
            occupation: Agent's role/occupation
            desires: List of agent's goals/desires
            emotions: Dictionary of emotional states
            domain: Agent's operating domain
            capabilities: List of agent capabilities
        """
        if occupation:
            self._configuration["occupation"] = occupation
        if desires:
            self._configuration["current_goals"] = desires
        if emotions:
            self._configuration["current_emotions"] = emotions
        if domain:
            self._configuration["domain"] = domain
        if capabilities:
            self._configuration["capabilities"] = capabilities
        
    async def observe(self, event: Dict):
        """Process an observation through both systems."""
        # Process through memory system
        await super().observe(event)
        
        # Process through TinyTroupe
        if "emotion" in event:
            self._configuration["current_emotions"].update(event["emotion"])
            
        # Store observation
        memory_id = await self.store_memory(
            content=str(event),
            importance=event.get("importance", 0.5),
            context={"type": "observation"}
        )
        if memory_id:
            self._configuration["memory_references"][memory_id] = {
                "type": "observation",
                "timestamp": datetime.now().isoformat()
            }
        
    async def act(self, action: str, **kwargs):
        """Perform an action through both systems."""
        # Log action in memory
        memory_id = await self.store_memory(
            content=f"Action: {action}, Parameters: {str(kwargs)}",
            importance=0.5,
            context={
                "type": "action",
                "action": action,
                "parameters": kwargs
            }
        )
        if memory_id:
            self._configuration["memory_references"][memory_id] = {
                "type": "action",
                "timestamp": datetime.now().isoformat()
            }
        
        # Execute through world if available
        if self.world:
            return await self.world.execute_action(self, action, **kwargs)
            
        logger.warning(f"Agent {self.name} has no world to execute action in")
        return None
        
    async def learn_concept(self, name: str, type: str, description: str, related: List[str] = None):
        """Learn a new concept."""
        # Store concept in memory
        memory_id = await self.store_memory(
            content=f"Learning concept: {name} ({type}) - {description}",
            importance=0.8,
            context={"type": "concept_learning"},
            concepts=[{
                "name": name,
                "type": type,
                "description": description,
                "related": related or []
            }]
        )
        
        # Update memory references
        if memory_id:
            self._configuration["memory_references"][memory_id] = {
                "type": "concept",
                "timestamp": datetime.now().isoformat()
            }
            
        # Update emotions if concept is emotional
        if "emotion" in type.lower():
            self._configuration["current_emotions"][name] = description
            
    async def store_memory(self, content: str, importance: float = 0.5, context: Dict = None, concepts: List = None, relationships: List = None) -> str:
        """Store memory in both systems."""
        # Create memory object
        memory = EpisodicMemory(
            content=content,
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=importance,
            context=context or {},
            concepts=concepts or [],
            relationships=relationships or [],
            participants=[],
            metadata={}
        )
        
        # Store in memory system
        memory_id = await self.memory_system.episodic.store_memory(memory)
        
        # Update memory references
        if memory_id:
            self._configuration["memory_references"][memory_id] = {
                "type": context.get("type", "memory") if context else "memory",
                "timestamp": datetime.now().isoformat()
            }
            
        return memory_id
            
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Store memory
        memory_id = await self.store_memory(
            content=content["content"] if "content" in content else str(content),
            importance=content.get("importance", 0.8),
            context=content.get("context", {}),
            concepts=content.get("concepts", []),
            relationships=content.get("relationships", [])
        )
        
        # Update memory references
        if memory_id:
            self._configuration["memory_references"][memory_id] = {
                "type": "process",
                "timestamp": datetime.now().isoformat()
            }
        
        # Update TinyTroupe state based on content
        if "concepts" in content:
            for concept in content["concepts"]:
                # Learn concept
                await self.learn_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"],
                    related=concept.get("related", [])
                )
        
        return AgentResponse(
            memory_id=memory_id,
            content=content,
            concepts=content.get("concepts", []),
            relationships=content.get("relationships", [])
        )
        
    async def reflect(self):
        """Reflect through both systems."""
        # Reflect through memory system
        await super().reflect()
        
        # Get recent memories
        recent_memories = await self.recall_memories(
            query={"time_range": {"hours": 1}},
            limit=10
        )
        
        if not recent_memories:
            return
            
        # Analyze patterns
        patterns = self._analyze_patterns(recent_memories)
        
        # Update TinyTroupe state based on patterns
        for pattern in patterns:
            # Update emotions based on pattern importance
            if pattern.get("importance_avg", 0) > 0.7:
                self._configuration["current_emotions"].update({
                    "interest": "high",
                    "focus": pattern.get("type", "general")
                })
                
            # Update desires based on common concepts
            if pattern.get("concepts"):
                self._configuration["current_goals"].extend([
                    f"Learn more about {concept}"
                    for concept in pattern["concepts"]
                ])
                
        # Store reflection
        memory_id = await self.store_memory(
            content=f"Reflection: {len(patterns)} patterns found. Emotions: {self._configuration['current_emotions']}. Goals: {self._configuration['current_goals']}",
            importance=0.7,
            context={
                "type": "reflection",
                "patterns": patterns,
                "emotions": self._configuration["current_emotions"],
                "desires": self._configuration["current_goals"],
                "timestamp": datetime.now().isoformat()
            }
        )
        if memory_id:
            self._configuration["memory_references"][memory_id] = {
                "type": "reflection",
                "timestamp": datetime.now().isoformat()
            }
            
    def _analyze_patterns(self, memories: List[EpisodicMemory]) -> List[Dict]:
        """Analyze patterns in memories."""
        patterns = []
        
        # Group memories by type
        type_groups = {}
        for memory in memories:
            memory_type = memory.context.get("type", "general")
            if memory_type not in type_groups:
                type_groups[memory_type] = []
            type_groups[memory_type].append(memory)
            
        # Analyze each group
        for memory_type, group in type_groups.items():
            # Calculate average importance
            importance_avg = sum(m.importance for m in group) / len(group)
            
            # Extract common concepts
            concept_counts = {}
            for memory in group:
                for concept in memory.concepts:
                    name = concept.get("name") if isinstance(concept, dict) else concept.name
                    concept_counts[name] = concept_counts.get(name, 0) + 1
                    
            # Get most common concepts
            common_concepts = sorted(
                concept_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            patterns.append({
                "type": memory_type,
                "importance_avg": importance_avg,
                "concepts": [name for name, _ in common_concepts],
                "count": len(group)
            })
            
        return patterns

class TinyFactory:
    """Factory class for creating and managing TinyTroupe agents."""
    
    def __init__(
        self,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None
    ):
        """Initialize the factory with shared dependencies."""
        self.memory_system = memory_system
        self.world = world
        self.agents = {}  # agent_id -> agent instance
        
    def create_agent(
        self,
        agent_type: str,
        domain: str,
        capabilities: List[str],
        supervisor_id: Optional[str] = None,
        attributes: Optional[Dict] = None
    ) -> str:
        """Create a new agent with specified type and capabilities.
        
        Args:
            agent_type: Type of agent to create (e.g., "worker", "supervisor")
            domain: Operating domain for the agent
            capabilities: List of agent capabilities
            supervisor_id: Optional ID of supervising agent
            attributes: Optional additional attributes
            
        Returns:
            str: Unique ID of created agent
        """
        # Generate unique ID
        agent_id = str(uuid.uuid4())
        
        # Create base attributes
        base_attributes = {
            "occupation": f"{agent_type.title()} Agent",
            "desires": ["Complete assigned tasks", "Collaborate effectively"],
            "emotions": {"baseline": "focused"},
            "capabilities": capabilities,
            "domain": domain
        }
        
        # Merge with provided attributes
        if attributes:
            base_attributes.update(attributes)
            
        # Create agent instance
        agent = TinyTroupeAgent(
            name=f"{agent_type}_{agent_id[:8]}",
            memory_system=self.memory_system,
            world=self.world,
            attributes=base_attributes,
            agent_type=agent_type
        )
        
        # Store agent
        self.agents[agent_id] = agent
        
        # If supervisor specified, establish relationship
        if supervisor_id and supervisor_id in self.agents:
            supervisor = self.agents[supervisor_id]
            # Record supervision relationship in memory
            if self.memory_system and hasattr(self.memory_system, "semantic"):
                self.memory_system.semantic.store.create_relationship(
                    supervisor_id,
                    agent_id,
                    "SUPERVISES",
                    {
                        "established": datetime.now().isoformat(),
                        "domain": domain
                    }
                )
        
        return agent_id
        
    def get_agent(self, agent_id: str) -> Optional[TinyTroupeAgent]:
        """Retrieve an agent by ID."""
        return self.agents.get(agent_id)
        
    def get_agents_by_type(self, agent_type: str) -> List[TinyTroupeAgent]:
        """Get all agents of a specific type."""
        return [
            agent for agent in self.agents.values()
            if agent.agent_type == agent_type
        ]
        
    def get_agents_by_domain(self, domain: str) -> List[TinyTroupeAgent]:
        """Get all agents operating in a specific domain."""
        return [
            agent for agent in self.agents.values()
            if agent._configuration.get("domain") == domain
        ]
        
    def get_agents_by_capability(self, capability: str) -> List[TinyTroupeAgent]:
        """Get all agents with a specific capability."""
        return [
            agent for agent in self.agents.values()
            if capability in agent._configuration.get("capabilities", [])
        ]
