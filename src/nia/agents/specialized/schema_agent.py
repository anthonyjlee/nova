"""TinyTroupe schema agent implementation."""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from ...nova.core.schema import SchemaAgent as NovaSchemaAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class SchemaAgent(TinyTroupeAgent, NovaSchemaAgent):
    """Schema agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize schema agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="schema"
        )
        
        # Initialize NovaSchemaAgent
        NovaSchemaAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize schema-specific attributes
        self._initialize_schema_attributes()
        
    def _initialize_schema_attributes(self):
        """Initialize schema-specific attributes."""
        self.define(
            occupation="Schema Manager",
            desires=[
                "Maintain schema integrity",
                "Ensure domain compliance",
                "Detect schema issues",
                "Evolve schemas appropriately"
            ],
            emotions={
                "baseline": "analytical",
                "towards_schema": "focused",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "schema_analysis",
                "domain_validation",
                "issue_detection",
                "schema_evolution"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on schema analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on schema results
                if concept.get("type") == "schema_result":
                    self.emotions.update({
                        "schema_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on schema needs
                if concept.get("type") == "schema_need":
                    self.desires.append(f"Improve {concept['name']}")
                    
                # Update emotions based on domain relevance
                if "domain_relevance" in concept:
                    relevance = float(concept["domain_relevance"])
                    if relevance > 0.8:
                        self.emotions.update({
                            "domain_state": "highly_relevant"
                        })
                    elif relevance < 0.3:
                        self.emotions.update({
                            "domain_state": "low_relevance"
                        })
                    
        return response
        
    async def analyze_and_store(
        self,
        content: Dict[str, Any],
        schema_type: str,
        target_domain: Optional[str] = None
    ):
        """Analyze schema and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze schema
        result = await self.analyze_schema(
            content,
            schema_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store schema analysis
        await self.store_memory(
            content={
                "type": "schema_analysis",
                "content": content,
                "schema_type": schema_type,
                "analysis": {
                    "is_valid": result.is_valid,
                    "schema": result.schema,
                    "validations": result.validations,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "schema",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on schema result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence schema validation passed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Schema validation failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical schema issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
        
        return result
        
    async def generate_model(
        self,
        content: Dict[str, Any],
        model_name: str,
        target_domain: Optional[str] = None
    ) -> type[BaseModel]:
        """Generate Pydantic model with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze schema first
        result = await self.analyze_schema(
            content,
            "data",
            metadata={"domain": target_domain or self.domain}
        )
        
        if not result.is_valid:
            raise ValueError(
                f"Cannot generate model from invalid schema: {result.issues}"
            )
            
        # Generate model
        model = await self.generate_pydantic_model(result.schema, model_name)
        
        # Record reflection for model generation
        await self.record_reflection(
            f"Generated Pydantic model {model_name} from schema in {self.domain} domain",
            domain=self.domain
        )
        
        return model
        
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
                f"SchemaAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
