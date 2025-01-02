"""TinyTroupe agent base implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from tinytroupe import TinyPerson
from .base import BaseAgent as MemoryBaseAgent
from ..world.environment import NIAWorld
from ..memory.two_layer import TwoLayerMemorySystem
from ..memory.types.memory_types import Memory, EpisodicMemory, Concept, AgentResponse

logger = logging.getLogger(__name__)

class TinyTroupeAgent(TinyPerson, MemoryBaseAgent):
    """Base agent implementation combining TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        agent_type: str = "base"
    ):
        """Initialize agent with both TinyTroupe and memory capabilities."""
        # Initialize TinyPerson
        TinyPerson.__init__(self, name)
        
        # Initialize MemoryBaseAgent
        MemoryBaseAgent.__init__(
            self,
            llm=None,  # TinyTroupe handles LLM interactions
            store=memory_system.semantic.driver if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            agent_type=agent_type
        )
        
        # Store additional attributes
        self.world = world
        self._initialize_attributes(attributes)
        
    def _initialize_attributes(self, attributes: Optional[Dict] = None):
        """Initialize TinyTroupe attributes."""
        attributes = attributes or {}
        self._configuration.update({
            "occupation": attributes.get("occupation", "Agent"),
            "current_goals": attributes.get("desires", ["Help users", "Learn and improve"]),
            "current_emotions": attributes.get("emotions", {"baseline": "neutral"}),
            "memory_references": attributes.get("memory_references", [])
        })
        
    async def observe(self, event: Dict):
        """Process an observation through both systems."""
        # Process through memory system
        await super().observe(event)
        
        # Process through TinyTroupe
        if "emotion" in event:
            self.emotions.update(event["emotion"])
            
        # Store observation
        await self.store_memory(
            content=event,
            importance=event.get("importance", 0.5),
            context={"type": "observation"}
        )
        
    async def act(self, action: str, **kwargs):
        """Perform an action through both systems."""
        # Log action in memory
        await self.store_memory(
            content={"action": action, "parameters": kwargs},
            context={"type": "action"}
        )
        
        # Execute through world if available
        if self.world:
            return await self.world.execute_action(self, action, **kwargs)
            
        logger.warning(f"Agent {self.name} has no world to execute action in")
        return None
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on response
        if response and response.concepts:
            for concept in response.concepts:
                # Learn concept
                await self.learn_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"],
                    related=concept.get("related", [])
                )
                
                # Update emotions based on concept
                if "emotion" in concept["type"].lower():
                    self.emotions.update({
                        concept["name"]: concept["description"]
                    })
                    
        return response
        
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
            if pattern["importance_avg"] > 0.7:
                self.emotions.update({
                    "interest": "high",
                    "focus": pattern["type"]
                })
                
            # Update desires based on common concepts
            if pattern["concepts"]:
                self.desires.extend([
                    f"Learn more about {concept}"
                    for concept in pattern["concepts"]
                ])
                
        # Store reflection
        await self.store_memory(
            content={
                "type": "reflection",
                "patterns": patterns,
                "emotions": self.emotions,
                "desires": self.desires,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.7,
            context={"type": "reflection"}
        )
