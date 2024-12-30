"""TinyTroupe parsing agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.parsing import NovaParser
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ParsingAgent(TinyTroupeAgent, NovaParser):
    """Parsing agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None
    ):
        """Initialize parsing agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="parsing"
        )
        
        # Initialize NovaParser
        NovaParser.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None
        )
        
        # Initialize parsing-specific attributes
        self._initialize_parsing_attributes()
        
    def _initialize_parsing_attributes(self):
        """Initialize parsing-specific attributes."""
        self.define(
            occupation="Content Parser",
            desires=[
                "Extract structured information",
                "Identify key concepts",
                "Validate content structure"
            ],
            emotions={
                "baseline": "analytical",
                "towards_content": "focused"
            }
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on parsing analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on content complexity
                if concept.get("type") == "complexity":
                    self.emotions.update({
                        "content_complexity": concept.get("description", "moderate")
                    })
                    
                # Update desires based on parsing needs
                if concept.get("type") == "validation_need":
                    self.desires.append(f"Validate {concept['name']}")
                    
        return response
        
    async def parse_and_store(self, text: str):
        """Parse text and store results."""
        # Parse text
        result = await self.parse_text(text)
        
        # Store parsing memory
        await self.store_memory(
            content={
                "type": "parsing_result",
                "text": text,
                "analysis": {
                    "concepts": result.concepts,
                    "key_points": result.key_points,
                    "confidence": result.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.6,
            context={"type": "parsing"}
        )
        
        return result
