"""TinyTroupe desire agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.desire import DesireAgent as NovaDesireAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class DesireAgent(TinyTroupeAgent, NovaDesireAgent):
    """Desire agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize desire agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaDesireAgent first
        NovaDesireAgent.__init__(
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
            agent_type="desire"
        )
        
        # Initialize desire-specific attributes
        self._initialize_desire_attributes()
        
    def _initialize_desire_attributes(self):
        """Initialize desire-specific attributes."""
        attributes = {
            "occupation": "Desire Analyst",
            "desires": [
                "Understand motivations",
                "Track goal progress",
                "Ensure desire alignment",
                "Maintain domain boundaries"
            ],
            "emotions": {
                "baseline": "motivated",
                "towards_analysis": "focused",
                "towards_domain": "mindful"
            },
            "capabilities": [
                "desire_analysis",
                "motivation_tracking",
                "domain_validation",
                "priority_assessment"
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
        
        # Update TinyTroupe state based on desire analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "desire":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on motivation needs
                if concept.get("type") == "motivation_need":
                    self.desires.append(f"Address {concept['name']}")
                    
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
        """Analyze desires and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze desires
        result = await self.analyze_desires(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store desire analysis
        await self.store_memory(
            content={
                "type": "desire_analysis",
                "content": content,
                "analysis": {
                    "desires": result.desires,
                    "confidence": result.confidence,
                    "motivations": result.motivations,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "desire",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence desire analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence desire analysis - may need additional motivation in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for priority factors
        if result.motivations.get("priority_factors", []):
            await self.record_reflection(
                f"Priority factors identified in {self.domain} domain - tracking required",
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
                f"DesireAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
