"""TinyTroupe research agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.research import ResearchAgent as NovaResearchAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ResearchAgent(TinyTroupeAgent, NovaResearchAgent):
    """Research agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize research agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="research"
        )
        
        # Initialize NovaResearchAgent
        NovaResearchAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize research-specific attributes
        self._initialize_research_attributes()
        
    def _initialize_research_attributes(self):
        """Initialize research-specific attributes."""
        self.define(
            occupation="Research Analyst",
            desires=[
                "Understand research findings",
                "Track research sources",
                "Ensure research quality",
                "Maintain domain boundaries"
            ],
            emotions={
                "baseline": "analytical",
                "towards_analysis": "thorough",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "research_analysis",
                "source_validation",
                "domain_validation",
                "quality_assessment"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on research analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "finding":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on research needs
                if concept.get("type") == "research_need":
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
        """Analyze research and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze research
        result = await self.analyze_research(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store research analysis
        await self.store_memory(
            content={
                "type": "research_analysis",
                "content": content,
                "analysis": {
                    "findings": result.findings,
                    "confidence": result.confidence,
                    "sources": result.sources,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "research",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence research analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence research analysis - may need additional sources in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for novel findings
        novel_findings = [f for f in result.findings if f.get("novelty", 0) > 0.8]
        if novel_findings:
            await self.record_reflection(
                f"Novel research findings identified in {self.domain} domain - further investigation recommended",
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
                f"ResearchAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
