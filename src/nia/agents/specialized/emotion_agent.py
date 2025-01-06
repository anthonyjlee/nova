"""TinyTroupe emotion agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.emotion import EmotionAgent as NovaEmotionAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class EmotionAgent(TinyTroupeAgent, NovaEmotionAgent):
    """Emotion agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize emotion agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaEmotionAgent first
        NovaEmotionAgent.__init__(
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
            agent_type="emotion"
        )
        
        # Initialize emotion-specific attributes
        self._initialize_emotion_attributes()
        
    def _initialize_emotion_attributes(self):
        """Initialize emotion-specific attributes."""
        attributes = {
            "occupation": "Emotion Analyst",
            "desires": [
                "Understand emotional states",
                "Track emotional changes",
                "Ensure emotional appropriateness",
                "Maintain domain boundaries"
            ],
            "emotions": {
                "baseline": "empathetic",
                "towards_analysis": "perceptive",
                "towards_domain": "mindful"
            },
            "capabilities": [
                "emotion_analysis",
                "intensity_tracking",
                "domain_validation",
                "context_awareness"
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
        
        # Update TinyTroupe state based on emotion analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "emotion":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on emotional needs
                if concept.get("type") == "emotional_need":
                    self.desires.append(f"Address {concept['name']}")
                    
                # Update emotions based on domain appropriateness
                if "domain_appropriateness" in concept:
                    appropriateness = float(concept["domain_appropriateness"])
                    if appropriateness > 0.8:
                        self.emotions.update({
                            "domain_state": "highly_appropriate"
                        })
                    elif appropriateness < 0.3:
                        self.emotions.update({
                            "domain_state": "concerning"
                        })
                    
        return response
        
    async def analyze_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Analyze emotions and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze emotions
        result = await self.analyze_emotion(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store emotion analysis
        await self.store_memory(
            content={
                "type": "emotion_analysis",
                "content": content,
                "analysis": {
                    "emotions": result.emotions,
                    "intensity": result.intensity,
                    "confidence": result.confidence,
                    "context": result.context,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "emotion",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence emotion analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence emotion analysis - may need additional context in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for intense emotions
        if result.intensity > 0.8:
            await self.record_reflection(
                f"High intensity emotions detected in {self.domain} domain - monitoring required",
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
                f"EmotionAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
