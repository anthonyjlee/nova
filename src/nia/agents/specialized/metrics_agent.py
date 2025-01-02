"""TinyTroupe metrics agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.metrics import MetricsAgent as NovaMetricsAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class MetricsAgent(TinyTroupeAgent, NovaMetricsAgent):
    """Metrics agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize metrics agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="metrics"
        )
        
        # Initialize NovaMetricsAgent
        NovaMetricsAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize metrics-specific attributes
        self._initialize_metrics_attributes()
        
    def _initialize_metrics_attributes(self):
        """Initialize metrics-specific attributes."""
        self.define(
            occupation="Metrics Manager",
            desires=[
                "Process metrics effectively",
                "Track performance metrics",
                "Monitor resource usage",
                "Maintain metrics quality"
            ],
            emotions={
                "baseline": "analytical",
                "towards_metrics": "focused",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "metrics_processing",
                "performance_tracking",
                "resource_monitoring",
                "pattern_metrics"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on metrics results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on metrics results
                if concept.get("type") == "metrics_result":
                    self.emotions.update({
                        "metrics_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on metrics needs
                if concept.get("type") == "metrics_need":
                    self.desires.append(f"Track {concept['name']}")
                    
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
        
    async def process_and_store(
        self,
        content: Dict[str, Any],
        metrics_type: str,
        target_domain: Optional[str] = None
    ):
        """Process metrics and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Process metrics
        result = await self.process_metrics(
            content,
            metrics_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store metrics results
        await self.store_memory(
            content={
                "type": "metrics_processing",
                "content": content,
                "metrics_type": metrics_type,
                "metrics": {
                    "is_valid": result.is_valid,
                    "metrics": result.metrics,
                    "values": result.values,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "metrics",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on metrics result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence metrics completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Metrics failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical metrics issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important values
        important_values = [
            v for v in result.values
            if v.get("importance", 0.0) > 0.8
        ]
        if important_values:
            await self.record_reflection(
                f"Important metrics values processed in {self.domain} domain",
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
                f"MetricsAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
