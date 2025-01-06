"""TinyTroupe reflection agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.reflection import ReflectionAgent as NovaReflectionAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ReflectionAgent(NovaReflectionAgent, TinyTroupeAgent):
    """Reflection agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize reflection agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaReflectionAgent first
        NovaReflectionAgent.__init__(
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
            agent_type="reflection"
        )
        
        # Initialize reflection-specific attributes
        self._initialize_reflection_attributes()
        
    def _initialize_reflection_attributes(self):
        """Initialize reflection-specific attributes."""
        attributes = {
            "occupation": "Reflection Analyst",
            "desires": [
                "Understand patterns",
                "Track learning progress",
                "Ensure insight quality",
                "Maintain domain boundaries"
            ],
            "emotions": {
                "baseline": "contemplative",
                "towards_analysis": "introspective",
                "towards_domain": "mindful"
            },
            "capabilities": [
                "reflection_analysis",
                "pattern_recognition",
                "domain_validation",
                "learning_assessment"
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
        
        # Update TinyTroupe state based on reflection analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "insight":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on learning needs
                if concept.get("type") == "learning_need":
                    self.desires.append(f"Explore {concept['name']}")
                    
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
        """Analyze reflection and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze reflection
        result = await self.analyze_reflection(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store reflection analysis
        await self.store_memory(
            content={
                "type": "reflection_analysis",
                "content": content,
                "analysis": {
                    "insights": result.insights,
                    "confidence": result.confidence,
                    "patterns": result.patterns,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "reflection",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence reflection analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence reflection analysis - may need additional patterns in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for recurring themes
        if result.patterns.get("recurring_themes", []):
            await self.record_reflection(
                f"Recurring themes identified in {self.domain} domain - further analysis recommended",
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
                f"ReflectionAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
