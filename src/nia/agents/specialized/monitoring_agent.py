"""TinyTroupe monitoring agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.monitoring import MonitoringAgent as NovaMonitoringAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class MonitoringAgent(TinyTroupeAgent, NovaMonitoringAgent):
    """Monitoring agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize monitoring agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="monitoring"
        )
        
        # Initialize NovaMonitoringAgent
        NovaMonitoringAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize monitoring-specific attributes
        self._initialize_monitoring_attributes()
        
    def _initialize_monitoring_attributes(self):
        """Initialize monitoring-specific attributes."""
        self.define(
            occupation="Agent Monitor",
            desires=[
                "Monitor agents effectively",
                "Track performance metrics",
                "Ensure system health",
                "Maintain monitoring quality"
            ],
            emotions={
                "baseline": "analytical",
                "towards_agents": "focused",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "agent_monitoring",
                "metric_tracking",
                "health_checking",
                "pattern_monitoring"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on monitoring results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on monitoring results
                if concept.get("type") == "monitoring_result":
                    self.emotions.update({
                        "monitoring_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on monitoring needs
                if concept.get("type") == "monitoring_need":
                    self.desires.append(f"Monitor {concept['name']}")
                    
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
        
    async def monitor_and_store(
        self,
        content: Dict[str, Any],
        monitoring_type: str,
        target_domain: Optional[str] = None
    ):
        """Monitor agents and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Monitor agents
        result = await self.monitor_agents(
            content,
            monitoring_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store monitoring results
        await self.store_memory(
            content={
                "type": "agent_monitoring",
                "content": content,
                "monitoring_type": monitoring_type,
                "monitoring": {
                    "is_valid": result.is_valid,
                    "monitoring": result.monitoring,
                    "metrics": result.metrics,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "monitoring",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on monitoring result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence monitoring completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Monitoring failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical monitoring issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important metrics
        important_metrics = [
            m for m in result.metrics
            if m.get("importance", 0.0) > 0.8
        ]
        if important_metrics:
            await self.record_reflection(
                f"Important monitoring metrics recorded in {self.domain} domain",
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
                f"MonitoringAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
