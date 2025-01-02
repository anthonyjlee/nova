"""TinyTroupe orchestration agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.orchestration import OrchestrationAgent as NovaOrchestrationAgent
from ...nova.core.analytics import AnalyticsAgent, AnalyticsResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class OrchestrationAgent(TinyTroupeAgent, NovaOrchestrationAgent):
    """Orchestration agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize orchestration agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="orchestration"
        )
        
        # Initialize NovaOrchestrationAgent
        NovaOrchestrationAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize analytics agent
        self.analytics = AnalyticsAgent(domain=self.domain)
        
        # Initialize orchestration-specific attributes
        self._initialize_orchestration_attributes()
        
        # Initialize task flow tracking
        self.active_flows = {}  # flow_id -> flow_state
        self.flow_patterns = {}  # pattern_id -> pattern_config
        self.execution_monitors = {}  # task_id -> monitor_state
        self.resource_allocations = {}  # resource_id -> allocation_state
        self.dependency_graph = {}  # task_id -> dependencies
        
    def _initialize_orchestration_attributes(self):
        """Initialize orchestration-specific attributes."""
        self._configuration.update({
            "occupation": "Advanced Agent Orchestrator",
            "current_goals": [
                "Coordinate agents effectively",
                "Optimize agent interactions",
                "Ensure task completion",
                "Maintain orchestration quality",
                "Optimize task flows",
                "Manage resource allocation",
                "Monitor execution progress",
                "Handle dependencies efficiently",
                "Adapt to changing conditions",
                "Ensure system resilience"
            ],
            "current_emotions": {
                "baseline": "analytical",
                "towards_agents": "focused",
                "towards_domain": "mindful",
                "towards_flows": "attentive",
                "towards_resources": "efficient",
                "towards_execution": "vigilant",
                "towards_adaptation": "responsive"
            },
            "domain": self.domain,
            "capabilities": [
                "agent_orchestration",
                "flow_coordination",
                "decision_making",
                "pattern_orchestration",
                "flow_optimization",
                "resource_management",
                "execution_monitoring",
                "dependency_handling",
                "adaptive_planning",
                "resilience_management"
            ]
        })
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced flow awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update flow tracking with analytics
        if flow_id := content.get("flow_id"):
            await self._update_flow_state(flow_id, content)
            
            # Get flow analytics
            analytics_result = await self._get_flow_analytics(flow_id)
            
            # Update flow state based on analytics
            if analytics_result and analytics_result.is_valid:
                await self._apply_analytics_insights(flow_id, analytics_result)
            
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on orchestration results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on orchestration results
                if concept.get("type") == "orchestration_result":
                    self.emotions.update({
                        "orchestration_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on orchestration needs
                if concept.get("type") == "orchestration_need":
                    self.desires.append(f"Coordinate {concept['name']}")
                    
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
                        
                # Update flow state emotions
                if concept.get("type") == "flow_state":
                    self.emotions.update({
                        "flow_state": concept.get("state", "neutral")
                    })
                    
                # Update resource state emotions
                if concept.get("type") == "resource_state":
                    self.emotions.update({
                        "resource_state": concept.get("state", "neutral")
                    })
                    
                # Update execution state emotions
                if concept.get("type") == "execution_state":
                    self.emotions.update({
                        "execution_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def _get_flow_analytics(self, flow_id: str) -> Optional[AnalyticsResult]:
        """Get analytics for a specific flow."""
        try:
            flow_state = self.active_flows.get(flow_id)
            if not flow_state:
                return None
                
            content = {
                "type": "flow_analytics",
                "flow_id": flow_id,
                "flow_state": flow_state,
                "timestamp": datetime.now().isoformat()
            }
            
            return await self.analytics.process_analytics(
                content=content,
                analytics_type="behavioral",
                metadata={"domain": self.domain}
            )
        except Exception as e:
            logger.error(f"Error getting flow analytics: {str(e)}")
            return None
            
    async def _apply_analytics_insights(
        self,
        flow_id: str,
        analytics: AnalyticsResult
    ):
        """Apply analytics insights to flow state."""
        flow_state = self.active_flows.get(flow_id)
        if not flow_state:
            return
            
        # Update analytics state
        flow_state["analytics"] = {
            "last_update": datetime.now().isoformat(),
            "performance": analytics.analytics.get("analytics", {}),
            "predictions": {},
            "optimizations": []
        }
        
        # Apply insights
        for insight in analytics.insights:
            if insight.get("type") == "performance":
                flow_state["analytics"]["performance"].update(
                    insight.get("metrics", {})
                )
            elif insight.get("type") == "prediction":
                flow_state["analytics"]["predictions"][
                    insight.get("metric", "unknown")
                ] = insight.get("value", 0.0)
            elif insight.get("type") == "optimization":
                flow_state["analytics"]["optimizations"].append({
                    "type": insight.get("optimization_type"),
                    "description": insight.get("description"),
                    "confidence": insight.get("confidence", 0.0)
                })
                
        # Update attention needs based on analytics
        if analytics.confidence < 0.5:
            flow_state["needs_attention"] = True
            await self.record_reflection(
                f"Flow {flow_id} needs attention due to low analytics confidence",
                domain=self.domain
            )
            
    async def orchestrate_and_store(
        self,
        content: Dict[str, Any],
        orchestration_type: str,
        target_domain: Optional[str] = None
    ):
        """Orchestrate agents and store results with enhanced flow awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Get analytics for orchestration decision
        analytics_result = await self.analytics.process_analytics(
            content={
                "type": "orchestration_analytics",
                "content": content,
                "orchestration_type": orchestration_type,
                "timestamp": datetime.now().isoformat()
            },
            analytics_type="predictive",
            metadata={"domain": target_domain or self.domain}
        )
        
        # Update flow patterns if needed
        if patterns := content.get("flow_patterns"):
            self._update_flow_patterns(patterns)
            
        # Update resource allocations with analytics insights
        if resources := content.get("resources"):
            await self._update_resource_allocations(resources, analytics_result)
            
        # Update dependency graph
        if dependencies := content.get("dependencies"):
            self._update_dependency_graph(dependencies)
            
        # Orchestrate agents
        result = await self.orchestrate_agents(
            content,
            orchestration_type,
            metadata={
                "domain": target_domain or self.domain,
                "analytics": analytics_result.analytics if analytics_result else None
            }
        )
        
        # Store orchestration results with enhanced metadata
        await self.store_memory(
            content={
                "type": "agent_orchestration",
                "content": content,
                "orchestration_type": orchestration_type,
                "orchestration": {
                    "is_valid": result.is_valid,
                    "orchestration": result.orchestration,
                    "decisions": result.decisions,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "flow_states": self.active_flows,
                    "resource_states": self.resource_allocations,
                    "execution_states": self.execution_monitors,
                    "analytics": analytics_result.analytics if analytics_result else None,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "orchestration",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on orchestration result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence orchestration completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Orchestration failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical orchestration issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important decisions
        important_decisions = [
            d for d in result.decisions
            if d.get("importance", 0.0) > 0.8
        ]
        if important_decisions:
            await self.record_reflection(
                f"Important agent coordination decisions made in {self.domain} domain orchestration",
                domain=self.domain
            )
            
        # Record analytics-based reflections
        if analytics_result and analytics_result.insights:
            for insight in analytics_result.insights:
                if insight.get("importance", 0.0) > 0.7:
                    await self.record_reflection(
                        f"Analytics insight: {insight.get('description')}",
                        domain=self.domain
                    )
            
        # Record flow-specific reflections
        for flow_id, flow_state in self.active_flows.items():
            if flow_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Flow {flow_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record resource-specific reflections
        for resource_id, allocation in self.resource_allocations.items():
            if allocation.get("utilization", 0.0) > 0.9:
                await self.record_reflection(
                    f"Resource {resource_id} nearing capacity in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record execution-specific reflections
        for task_id, monitor in self.execution_monitors.items():
            if monitor.get("status") == "blocked":
                await self.record_reflection(
                    f"Task {task_id} blocked in {self.domain} domain - intervention needed",
                    domain=self.domain
                )
        
        return result
        
    async def _update_flow_state(self, flow_id: str, content: Dict[str, Any]):
        """Update flow state tracking with analytics integration."""
        if flow_id not in self.active_flows:
            self.active_flows[flow_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "steps_completed": 0,
                "current_phase": "initialization",
                "metrics": {},
                "needs_attention": False,
                "analytics": {
                    "last_update": None,
                    "performance": {},
                    "predictions": {},
                    "optimizations": []
                }
            }
            
        flow_state = self.active_flows[flow_id]
        
        # Update basic state
        if status := content.get("flow_status"):
            flow_state["status"] = status
            
        if phase := content.get("flow_phase"):
            flow_state["current_phase"] = phase
            
        # Update metrics
        if metrics := content.get("flow_metrics", {}):
            flow_state["metrics"].update(metrics)
            
        # Update completion tracking
        if content.get("step_completed"):
            flow_state["steps_completed"] += 1
            
        # Check for attention needs
        flow_state["needs_attention"] = any([
            content.get("needs_attention", False),
            content.get("has_blockers", False),
            content.get("resource_constraints", False)
        ])
        
        # Apply relevant flow patterns
        for pattern_id, pattern in self.flow_patterns.items():
            if self._matches_pattern(content, pattern):
                await self._apply_flow_pattern(flow_id, pattern_id, pattern)
                
    def _update_flow_patterns(self, patterns: Dict[str, Dict]):
        """Update flow pattern configurations."""
        for pattern_id, pattern in patterns.items():
            if isinstance(pattern, dict):
                self.flow_patterns[pattern_id] = {
                    "conditions": pattern.get("conditions", {}),
                    "actions": pattern.get("actions", []),
                    "priority": float(pattern.get("priority", 0.5))
                }
                
    async def _update_resource_allocations(
        self,
        resources: Dict[str, Dict],
        analytics: Optional[AnalyticsResult] = None
    ):
        """Update resource allocation tracking with analytics insights."""
        for resource_id, allocation in resources.items():
            if isinstance(allocation, dict):
                current = self.resource_allocations.get(resource_id, {})
                
                # Get analytics prediction if available
                predicted_utilization = None
                if analytics and analytics.analytics:
                    predictions = analytics.analytics.get("analytics", {})
                    if resource_pred := predictions.get(f"resource_{resource_id}"):
                        predicted_utilization = resource_pred.get("value")
                
                self.resource_allocations[resource_id] = {
                    "type": allocation.get("type", current.get("type", "unknown")),
                    "capacity": float(allocation.get("capacity", current.get("capacity", 0.0))),
                    "utilization": float(allocation.get("utilization", current.get("utilization", 0.0))),
                    "predicted_utilization": predicted_utilization,
                    "assigned_to": list(allocation.get("assigned_to", current.get("assigned_to", []))),
                    "constraints": allocation.get("constraints", current.get("constraints", {})),
                    "analytics": {
                        "last_update": datetime.now().isoformat(),
                        "predictions": analytics.analytics if analytics else {}
                    }
                }
                
    def _update_dependency_graph(self, dependencies: Dict[str, List[str]]):
        """Update task dependency tracking."""
        for task_id, deps in dependencies.items():
            if isinstance(deps, (list, set)):
                self.dependency_graph[task_id] = set(deps)
                
    def _matches_pattern(self, content: Dict[str, Any], pattern: Dict) -> bool:
        """Check if content matches a flow pattern."""
        conditions = pattern.get("conditions", {})
        
        for key, value in conditions.items():
            if key not in content:
                return False
                
            if isinstance(value, (str, int, float, bool)):
                if content[key] != value:
                    return False
            elif isinstance(value, dict):
                if not isinstance(content[key], dict):
                    return False
                if not all(
                    content[key].get(k) == v
                    for k, v in value.items()
                ):
                    return False
                    
        return True
        
    async def _apply_flow_pattern(
        self,
        flow_id: str,
        pattern_id: str,
        pattern: Dict
    ):
        """Apply a flow pattern's actions."""
        flow_state = self.active_flows[flow_id]
        
        for action in pattern.get("actions", []):
            action_type = action.get("type")
            
            if action_type == "update_phase":
                flow_state["current_phase"] = action["phase"]
            elif action_type == "add_metric":
                flow_state["metrics"][action["name"]] = action["value"]
            elif action_type == "set_attention":
                flow_state["needs_attention"] = action["value"]
            elif action_type == "record_reflection":
                await self.record_reflection(
                    f"Flow pattern {pattern_id} triggered in {flow_id}: {action['message']}",
                    domain=self.domain
                )
                
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
                f"OrchestrationAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
