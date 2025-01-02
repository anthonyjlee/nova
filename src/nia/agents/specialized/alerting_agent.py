"""TinyTroupe alerting agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.alerting import AlertingAgent as NovaAlertingAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class AlertingAgent(TinyTroupeAgent, NovaAlertingAgent):
    """Alerting agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize alerting agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="alerting"
        )
        
        # Initialize NovaAlertingAgent
        NovaAlertingAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize alerting-specific attributes
        self._initialize_alerting_attributes()
        
    def _initialize_alerting_attributes(self):
        """Initialize alerting-specific attributes."""
        self.define(
            occupation="Alert Manager",
            desires=[
                "Process alerts effectively",
                "Manage notification channels",
                "Handle incidents promptly",
                "Maintain alerting quality"
            ],
            emotions={
                "baseline": "analytical",
                "towards_alerts": "focused",
                "towards_domain": "mindful"
            },
            domain=self.domain,
            capabilities=[
                "alert_processing",
                "notification_management",
                "incident_handling",
                "pattern_alerting"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on alerting results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on alerting results
                if concept.get("type") == "alerting_result":
                    self.emotions.update({
                        "alerting_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on alerting needs
                if concept.get("type") == "alerting_need":
                    self.desires.append(f"Process {concept['name']}")
                    
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
        alerting_type: str,
        target_domain: Optional[str] = None
    ):
        """Process alerts and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Process alerts
        result = await self.process_alerts(
            content,
            alerting_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store alerting results
        await self.store_memory(
            content={
                "type": "alert_processing",
                "content": content,
                "alerting_type": alerting_type,
                "alerting": {
                    "is_valid": result.is_valid,
                    "alerting": result.alerting,
                    "alerts": result.alerts,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "alerting",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on alerting result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence alerting completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Alerting failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical alerting issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important alerts
        important_alerts = [
            a for a in result.alerts
            if a.get("importance", 0.0) > 0.8
        ]
        if important_alerts:
            await self.record_reflection(
                f"Important alerts processed in {self.domain} domain",
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
                f"AlertingAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
