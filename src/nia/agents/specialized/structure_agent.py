"""TinyTroupe structure agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.structure import StructureAgent as NovaStructureAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class StructureAgent(NovaStructureAgent, TinyTroupeAgent):
    """Structure agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize structure agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaStructureAgent first
        NovaStructureAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain
        )
        
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="structure"
        )
        
        # Initialize structure-specific attributes
        self._initialize_structure_attributes()
        
    def _initialize_structure_attributes(self):
        """Initialize structure-specific attributes."""
        attributes = {
            "occupation": "Structure Analyst",
            "desires": [
                "Analyze data structures",
                "Validate schemas",
                "Ensure structural integrity",
                "Maintain domain boundaries"
            ],
            "emotions": {
                "baseline": "methodical",
                "towards_analysis": "precise",
                "towards_validation": "thorough"
            },
            "capabilities": [
                "structure_analysis",
                "schema_validation",
                "domain_validation",
                "integrity_checking"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
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
                    
                # Update emotions based on domain validation
                if concept.get("type") == "domain_validation":
                    self.emotions.update({
                        "validation_state": concept.get("description", "stable")
                    })
                    
        return response
        
    async def analyze_and_store(
        self,
        text: str,
        expected_schema: Optional[Dict] = None,
        target_domain: Optional[str] = None
    ):
        """Analyze structure and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze structure
        result = await self.analyze_structure(
            text,
            expected_schema,
            metadata={"domain": target_domain or self.domain}
        )
        
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
                    "validation": result.validation,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.7,
            context={
                "type": "structure",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection if confidence is notable
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence structure analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence structure analysis - may need additional validation in {self.domain} domain",
                domain=self.domain
            )
        
        return result
        
    async def validate_and_store(
        self,
        schema: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Validate schema and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Validate schema
        result = await self.validate_schema(
            schema,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store validation result
        await self.store_memory(
            content={
                "type": "schema_validation",
                "schema": schema,
                "validation": result,
                "timestamp": datetime.now().isoformat()
            },
            importance=0.6,
            context={
                "type": "validation",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on validation result
        if result["is_valid"]:
            await self.record_reflection(
                f"Schema validation successful in {self.domain} domain",
                domain=self.domain
            )
        else:
            await self.record_reflection(
                f"Schema validation failed with {len(result['issues'])} issues in {self.domain} domain",
                domain=self.domain
            )
        
        return result
        
    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            return await self.memory_system.semantic.store.get_domain_access(
                self.name,
                domain
            )
        return False
        
    async def validate_domain_access(self, domain: str):
        """Validate access to a domain before processing."""
        if not await self.get_domain_access(domain):
            raise PermissionError(
                f"StructureAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
