"""TinyTroupe context agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.context import ContextAgent as MemoryContextAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ContextAgent(TinyTroupeAgent, MemoryContextAgent):
    """Context agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None
    ):
        """Initialize context agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="context"
        )
        
        # Initialize MemoryContextAgent
        MemoryContextAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None
        )
        
        # Initialize context-specific attributes
        self._initialize_context_attributes()
        
    def _initialize_context_attributes(self):
        """Initialize context-specific attributes."""
        self.define(
            occupation="Context Analyst",
            desires=[
                "Understand environmental factors",
                "Track contextual changes",
                "Identify relevant background information"
            ],
            emotions={
                "baseline": "observant",
                "towards_environment": "aware"
            }
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on context analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on environmental factors
                if concept.get("type") == "environment":
                    self.emotions.update({
                        "environmental_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on contextual needs
                if concept.get("type") == "context_need":
                    self.desires.append(f"Investigate {concept['name']}")
                    
        return response
        
    async def analyze_and_store(self, context: Dict[str, Any]):
        """Analyze context and store results."""
        # Format content for processing
        content = {"content": str(context)}
        
        # Process context
        result = await self.process(content)
        
        # Store context analysis
        await self.store_memory(
            content={
                "type": "context_analysis",
                "context": context,
                "analysis": {
                    "concepts": result.concepts,
                    "key_points": result.key_points,
                    "confidence": result.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.7,
            context={"type": "context"}
        )
        
        return result
