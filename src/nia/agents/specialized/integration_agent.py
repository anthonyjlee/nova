"""TinyTroupe integration agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.integration import IntegrationAgent as NovaIntegrationAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class IntegrationAgent(TinyTroupeAgent, NovaIntegrationAgent):
    """Integration agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize integration agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaIntegrationAgent first
        NovaIntegrationAgent.__init__(
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
            agent_type="integration"
        )
        
        # Initialize integration-specific attributes
        self._initialize_integration_attributes()
        
    def _initialize_integration_attributes(self):
        """Initialize integration-specific attributes."""
        attributes = {
            "occupation": "Content Integrator",
            "desires": [
                "Connect insights meaningfully",
                "Identify relationships",
                "Build coherent understanding",
                "Maintain integration quality"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_content": "focused",
                "towards_domain": "mindful"
            },
            "capabilities": [
                "content_integration",
                "relationship_identification",
                "insight_connection",
                "pattern_integration"
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
        
        # Update TinyTroupe state based on integration results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on integration results
                if concept.get("type") == "integration_result":
                    self.emotions.update({
                        "integration_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on integration needs
                if concept.get("type") == "integration_need":
                    self.desires.append(f"Connect {concept['name']}")
                    
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
        
    async def integrate_and_store(
        self,
        content: Dict[str, Any],
        integration_type: str,
        target_domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Integrate content and store results with domain awareness."""
        try:
            # Get debug flags
            debug_flags = metadata.get("debug_flags", {}) if metadata else {}
            
            # Validate domain access if specified
            if target_domain:
                await self.validate_domain_access(target_domain)
                
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content="Starting content integration with validation tracking",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            # Collect validation results from all agents
            validation_results = self._collect_validation_results(metadata)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=f"Collected validation results: {validation_results}",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            # Integrate content with validation context
            result = await self.integrate_content(
                content,
                integration_type,
                metadata={
                    "domain": target_domain or self.domain,
                    "validation_results": validation_results,
                    "debug_flags": debug_flags
                }
            )
        
            # Analyze validation patterns across agents
            validation_patterns = self._analyze_validation_patterns(
                validation_results,
                result.insights
            )
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=f"Analyzed validation patterns: {validation_patterns}",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            # Store integration results with validation context
            await self.store_memory(
                content={
                    "type": "content_integration",
                    "content": content,
                    "integration_type": integration_type,
                    "integration": {
                        "is_valid": result.is_valid,
                        "integration": result.integration,
                        "insights": result.insights,
                        "confidence": result.confidence,
                        "issues": result.issues,
                        "validation_patterns": validation_patterns,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                importance=0.8,
                context={
                    "type": "integration",
                    "domain": target_domain or self.domain,
                    "validation_results": validation_results
                }
            )
        
            # Record reflections with validation awareness
            if result.is_valid and result.confidence > 0.8:
                await self.record_reflection(
                    f"High confidence integration with validation completed in {self.domain} domain",
                    domain=self.domain
                )
            elif not result.is_valid:
                await self.record_reflection(
                    f"Integration failed - validation issues detected in {self.domain} domain",
                    domain=self.domain
                )
                
            # Record reflection for critical validation issues
            critical_validation_issues = [
                i for i in validation_patterns 
                if i.get("severity") == "high" and i.get("frequency", 0) > 1
            ]
            if critical_validation_issues:
                await self.record_reflection(
                    f"Critical validation patterns require attention in {self.domain} domain: {critical_validation_issues}",
                    domain=self.domain
                )
                
            # Record reflection for validation insights
            validation_insights = [
                i for i in result.insights
                if i.get("type") == "validation" and i.get("importance", 0.0) > 0.8
            ]
            if validation_insights:
                await self.record_reflection(
                    f"Important validation insights discovered in {self.domain} domain: {validation_insights}",
                    domain=self.domain
                )
        
            return result
            
        except Exception as e:
            error_msg = f"Error in content integration: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
            raise
            
    def _collect_validation_results(self, metadata: Optional[Dict]) -> Dict[str, Any]:
        """Collect validation results from all agents.
        
        Args:
            metadata: Metadata containing agent results
            
        Returns:
            Dict containing validation results by agent
        """
        results = {}
        
        if not metadata:
            return results
            
        # Collect validation results from each agent
        for agent_type, agent_data in metadata.items():
            if isinstance(agent_data, dict):
                validation_result = agent_data.get("validation_result")
                if validation_result:
                    results[agent_type] = validation_result
                    
        return results
        
    def _analyze_validation_patterns(
        self,
        validation_results: Dict[str, Any],
        insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze validation patterns across agents.
        
        Args:
            validation_results: Validation results by agent
            insights: Integration insights
            
        Returns:
            List of validation patterns with metadata
        """
        patterns = []
        
        # Track common validation issues
        issue_counts = {}
        for agent_type, result in validation_results.items():
            if isinstance(result, dict) and "issues" in result:
                for issue in result["issues"]:
                    key = f"{issue.get('type')}:{issue.get('description')}"
                    if key in issue_counts:
                        issue_counts[key]["frequency"] += 1
                        issue_counts[key]["agents"].append(agent_type)
                    else:
                        issue_counts[key] = {
                            "type": issue.get("type"),
                            "description": issue.get("description"),
                            "severity": issue.get("severity", "low"),
                            "frequency": 1,
                            "agents": [agent_type]
                        }
                        
        # Add patterns for common issues
        for pattern in issue_counts.values():
            if pattern["frequency"] > 1:  # Only include if seen in multiple agents
                patterns.append({
                    "type": "cross_agent_validation",
                    "description": pattern["description"],
                    "severity": pattern["severity"],
                    "frequency": pattern["frequency"],
                    "affected_agents": pattern["agents"]
                })
                
        # Add patterns from validation insights
        for insight in insights:
            if insight.get("type") == "validation":
                pattern = {
                    "type": "validation_insight",
                    "description": insight.get("description"),
                    "severity": "medium",
                    "importance": insight.get("importance", 0.5)
                }
                patterns.append(pattern)
                
        return patterns
        
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
                f"IntegrationAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
