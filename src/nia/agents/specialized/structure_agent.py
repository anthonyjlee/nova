"""TinyTroupe structure agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.structure import StructureAgent as MemoryStructureAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class StructureAgent(TinyTroupeAgent, MemoryStructureAgent):
    """Structure agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None
    ):
        """Initialize structure agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="structure"
        )
        
        # Initialize MemoryStructureAgent
        MemoryStructureAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None
        )
        
        # Initialize structure-specific attributes
        self._initialize_structure_attributes()
        
    def _initialize_structure_attributes(self):
        """Initialize structure-specific attributes."""
        self.define(
            occupation="Structure Analyst",
            desires=[
                "Analyze data structures",
                "Validate schemas",
                "Ensure structural integrity"
            ],
            emotions={
                "baseline": "methodical",
                "towards_analysis": "precise"
            }
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on structure analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on structure complexity
                if concept.get("type") == "complexity":
                    self.emotions.update({
                        "structure_complexity": concept.get("description", "moderate")
                    })
                    
                # Update desires based on validation needs
                if concept.get("type") == "validation_need":
                    self.desires.append(f"Validate {concept['name']}")
                    
        return response
        
    async def analyze_and_store(self, text: str, expected_schema: Optional[Dict] = None):
        """Analyze structure and store results."""
        # Analyze structure
        result = await self.analyze_structure(text, expected_schema)
        
        # Store analysis result
        await self.store_memory(
            content={
                "type": "structure_analysis",
                "text": text,
                "expected_schema": expected_schema,
                "analysis": {
                    "response": result.response,
                    "concepts": result.concepts,
                    "key_points": result.key_points,
                    "confidence": result.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.7,
            context={"type": "structure"}
        )
        
        return result
        
    async def validate_and_store(self, schema: Dict[str, Any]):
        """Validate schema and store results."""
        # Validate schema
        result = await self.validate_schema(schema)
        
        # Store validation result
        await self.store_memory(
            content={
                "type": "schema_validation",
                "schema": schema,
                "validation": result,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.6,
            context={"type": "validation"}
        )
        
        return result
