"""TinyTroupe meta agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.meta import MetaAgent as MemoryMetaAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse, DialogueContext

logger = logging.getLogger(__name__)

class MetaAgent(TinyTroupeAgent, MemoryMetaAgent):
    """Meta agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        agents: Optional[Dict] = None
    ):
        """Initialize meta agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="meta"
        )
        
        # Initialize MemoryMetaAgent
        MemoryMetaAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            agents=agents or {}
        )
        
        # Initialize meta-specific attributes
        self._initialize_meta_attributes()
        
    def _initialize_meta_attributes(self):
        """Initialize meta-specific attributes."""
        self.define(
            occupation="Meta Orchestrator",
            desires=[
                "Synthesize agent perspectives",
                "Maintain dialogue coherence",
                "Ensure knowledge integration"
            ],
            emotions={
                "baseline": "balanced",
                "towards_synthesis": "focused"
            }
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on meta analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on synthesis quality
                if concept.get("type") == "synthesis_quality":
                    self.emotions.update({
                        "synthesis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on integration needs
                if concept.get("type") == "integration_need":
                    self.desires.append(f"Integrate {concept['name']}")
                    
        return response
        
    async def orchestrate_and_store(self, content: Dict[str, Any], dialogue_context: Optional[DialogueContext] = None):
        """Orchestrate agent responses and store results."""
        # Add dialogue context if provided
        if dialogue_context:
            content['dialogue_context'] = dialogue_context
            
        # Process through meta agent
        result = await self.process_interaction(content['content'], content.get('metadata'))
        
        # Store orchestration result
        await self.store_memory(
            content={
                "type": "orchestration_result",
                "content": content,
                "analysis": {
                    "response": result.response,
                    "concepts": result.concepts,
                    "key_points": result.key_points,
                    "confidence": result.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={"type": "orchestration"}
        )
        
        return result
