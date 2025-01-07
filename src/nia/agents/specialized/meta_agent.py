"""TinyTroupe meta agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.meta import MetaAgent as NovaMetaAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse, DialogueContext

logger = logging.getLogger(__name__)

class MetaAgent(NovaMetaAgent, TinyTroupeAgent):
    """Meta agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        agents: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize meta agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaMetaAgent first
        NovaMetaAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            agents=agents or {},
            domain=self.domain
        )
        
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="meta"
        )
        
        # Initialize meta-specific attributes
        self._initialize_meta_attributes()
        
    def _initialize_meta_attributes(self):
        """Initialize meta-specific attributes."""
        attributes = {
            "occupation": "Meta Orchestrator",
            "desires": [
                "Synthesize agent perspectives",
                "Maintain dialogue coherence",
                "Ensure knowledge integration",
                "Respect domain boundaries"
            ],
            "emotions": {
                "baseline": "balanced",
                "towards_synthesis": "focused",
                "towards_domains": "respectful"
            },
            "capabilities": [
                "meta_synthesis",
                "agent_orchestration",
                "domain_management",
                "knowledge_integration"
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
                    
                # Update emotions based on domain complexity
                if concept.get("type") == "domain_complexity":
                    self.emotions.update({
                        "domain_state": concept.get("description", "stable")
                    })
                    
        return response
        
    async def orchestrate_and_store(
        self,
        content: Dict[str, Any],
        dialogue_context: Optional[DialogueContext] = None,
        target_domain: Optional[str] = None
    ):
        """Orchestrate agent responses and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Add dialogue context if provided
        if dialogue_context:
            content['dialogue_context'] = dialogue_context
            
        # Add domain information
        content['metadata'] = content.get('metadata', {})
        content['metadata']['domain'] = target_domain or self.domain
        
        # Process through meta agent
        result = await self.process_interaction(content['content'], content['metadata'])
        
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
            context={
                "type": "orchestration",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection if confidence is notable
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence orchestration achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence orchestration - may need additional agent input in {self.domain} domain",
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
                f"MetaAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
