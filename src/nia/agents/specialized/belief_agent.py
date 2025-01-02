"""TinyTroupe belief agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.belief import BeliefAgent as NovaBeliefAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class BeliefAgent(TinyTroupeAgent, NovaBeliefAgent):
    """Belief agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize belief agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="belief"
        )
        
        # Initialize NovaBeliefAgent
        NovaBeliefAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize belief-specific attributes
        self._initialize_belief_attributes()
        
    def _initialize_belief_attributes(self):
        """Initialize belief-specific attributes."""
        self.define(
            occupation="Belief Analyst",
            desires=[
                "Understand belief systems",
                "Validate knowledge claims",
                "Ensure belief coherence",
                "Maintain domain boundaries"
            ],
            emotions={
                "baseline": "analytical",
                "towards_analysis": "objective",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "belief_analysis",
                "evidence_validation",
                "domain_validation",
                "coherence_checking"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on belief analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "belief":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on belief needs
                if concept.get("type") == "belief_need":
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
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Analyze beliefs and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze beliefs
        result = await self.analyze_beliefs(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store belief analysis
        await self.store_memory(
            content={
                "type": "belief_analysis",
                "content": content,
                "analysis": {
                    "beliefs": result.beliefs,
                    "confidence": result.confidence,
                    "evidence": result.evidence,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "belief",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence belief analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence belief analysis - may need additional evidence in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for contradictions
        if result.evidence.get("contradictions", []):
            await self.record_reflection(
                f"Contradictory evidence found in {self.domain} domain - further investigation needed",
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
                f"BeliefAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
