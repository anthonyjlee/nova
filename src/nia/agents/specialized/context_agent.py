"""TinyTroupe context agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.context import ContextAgent as NovaContextAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ContextAgent(TinyTroupeAgent, NovaContextAgent):
    """Context agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
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
        
        # Initialize NovaContextAgent
        NovaContextAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize context-specific attributes
        self._initialize_context_attributes()
        
    def _initialize_context_attributes(self):
        """Initialize context-specific attributes."""
        self.define(
            occupation="Context Analyst",
            desires=[
                "Understand environmental factors",
                "Track contextual changes",
                "Identify relevant background information",
                "Maintain domain awareness"
            ],
            emotions={
                "baseline": "observant",
                "towards_environment": "aware",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "context_analysis",
                "environment_tracking",
                "domain_awareness",
                "background_analysis"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
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
        context: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Analyze context and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze context
        result = await self.analyze_context(
            context,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store context analysis
        await self.store_memory(
            content={
                "type": "context_analysis",
                "context": context,
                "analysis": {
                    "concepts": result.concepts,
                    "key_points": result.key_points,
                    "confidence": result.confidence,
                    "environment": result.environment,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.7,
            context={
                "type": "context",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection if confidence is notable
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence context analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence context analysis - may need additional investigation in {self.domain} domain",
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
                f"ContextAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
