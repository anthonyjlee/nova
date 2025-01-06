"""TinyTroupe analysis agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.analysis import AnalysisAgent as NovaAnalysisAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class AnalysisAgent(TinyTroupeAgent, NovaAnalysisAgent):
    """Analysis agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize analysis agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaAnalysisAgent first
        NovaAnalysisAgent.__init__(
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
            agent_type="analysis"
        )
        
        # Initialize analysis-specific attributes
        self._initialize_analysis_attributes()
        
    def _initialize_analysis_attributes(self):
        """Initialize analysis-specific attributes."""
        attributes = {
            "occupation": "Content Analyst",
            "desires": [
                "Extract meaningful insights",
                "Identify patterns",
                "Detect anomalies",
                "Maintain analysis quality"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_content": "focused",
                "towards_domain": "mindful"
            },
            "capabilities": [
                "content_analysis",
                "pattern_detection",
                "insight_generation",
                "anomaly_detection"
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
        
        # Update TinyTroupe state based on analysis results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis results
                if concept.get("type") == "analysis_result":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on analysis needs
                if concept.get("type") == "analysis_need":
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
        analysis_type: str,
        target_domain: Optional[str] = None
    ):
        """Analyze content and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze content
        result = await self.analyze_content(
            content,
            analysis_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store analysis results
        await self.store_memory(
            content={
                "type": "content_analysis",
                "content": content,
                "analysis_type": analysis_type,
                "analysis": {
                    "is_valid": result.is_valid,
                    "analysis": result.analysis,
                    "insights": result.insights,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "analysis",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence analysis completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Analysis failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical analysis issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important insights
        important_insights = [
            i for i in result.insights
            if i.get("importance", 0.0) > 0.8
        ]
        if important_insights:
            await self.record_reflection(
                f"Important insights discovered in {self.domain} domain analysis",
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
                f"AnalysisAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
