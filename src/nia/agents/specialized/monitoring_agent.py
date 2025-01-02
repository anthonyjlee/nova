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
        
        # Initialize monitoring tracking
        self.active_metrics = {}  # metric_id -> metric_state
        self.health_checks = {}  # check_id -> check_state
        self.alert_states = {}  # alert_id -> alert_state
        self.incident_tracking = {}  # incident_id -> incident_state
        self.trend_analysis = {}  # trend_id -> trend_state
        self.thresholds = {}  # threshold_id -> threshold_state
        
    def _initialize_monitoring_attributes(self):
        """Initialize monitoring-specific attributes."""
        self.define(
            occupation="Advanced System Monitor",
            desires=[
                "Monitor agents effectively",
                "Track performance metrics",
                "Ensure system health",
                "Maintain monitoring quality",
                "Collect real-time metrics",
                "Manage alert conditions",
                "Track incident resolution",
                "Analyze performance trends",
                "Optimize system health",
                "Adapt to changing conditions"
            ],
            emotions={
                "baseline": "analytical",
                "towards_agents": "focused",
                "towards_domain": "mindful",
                "towards_metrics": "precise",
                "towards_health": "vigilant",
                "towards_alerts": "responsive",
                "towards_incidents": "urgent",
                "towards_trends": "observant",
                "towards_adaptation": "adaptive"
            },
            domain=self.domain,
            capabilities=[
                "agent_monitoring",
                "metric_tracking",
                "health_checking",
                "pattern_monitoring",
                "alert_management",
                "incident_handling",
                "trend_analysis",
                "threshold_management",
                "performance_optimization",
                "system_adaptation"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced monitoring awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update metric tracking
        if metric_id := content.get("metric_id"):
            await self._update_metric_state(metric_id, content)
            
        # Update health checks
        if check_id := content.get("check_id"):
            await self._update_health_check(check_id, content)
            
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
                        
                # Update metric state emotions
                if concept.get("type") == "metric_state":
                    self.emotions.update({
                        "metric_state": concept.get("state", "neutral")
                    })
                    
                # Update health state emotions
                if concept.get("type") == "health_state":
                    self.emotions.update({
                        "health_state": concept.get("state", "neutral")
                    })
                    
                # Update alert state emotions
                if concept.get("type") == "alert_state":
                    self.emotions.update({
                        "alert_state": concept.get("state", "neutral")
                    })
                    
                # Update incident state emotions
                if concept.get("type") == "incident_state":
                    self.emotions.update({
                        "incident_state": concept.get("state", "neutral")
                    })
                    
                # Update trend state emotions
                if concept.get("type") == "trend_state":
                    self.emotions.update({
                        "trend_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def monitor_and_store(
        self,
        content: Dict[str, Any],
        monitoring_type: str,
        target_domain: Optional[str] = None
    ):
        """Monitor agents and store results with enhanced monitoring awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Update thresholds if needed
        if thresholds := content.get("thresholds"):
            self._update_thresholds(thresholds)
            
        # Update trend analysis
        if trends := content.get("trends"):
            await self._update_trend_analysis(trends)
            
        # Monitor agents
        result = await self.monitor_agents(
            content,
            monitoring_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store monitoring results with enhanced metadata
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
                    "metric_states": self.active_metrics,
                    "health_states": self.health_checks,
                    "alert_states": self.alert_states,
                    "incident_states": self.incident_tracking,
                    "trend_states": self.trend_analysis,
                    "threshold_states": self.thresholds,
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
            
        # Record metric-specific reflections
        for metric_id, metric_state in self.active_metrics.items():
            if metric_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Metric {metric_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record health check reflections
        for check_id, check_state in self.health_checks.items():
            if check_state.get("status") == "failing":
                await self.record_reflection(
                    f"Health check {check_id} failing in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record alert state reflections
        for alert_id, alert_state in self.alert_states.items():
            if alert_state.get("status") == "triggered":
                await self.record_reflection(
                    f"Alert {alert_id} triggered in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record incident tracking reflections
        for incident_id, incident_state in self.incident_tracking.items():
            if incident_state.get("status") == "unresolved":
                await self.record_reflection(
                    f"Incident {incident_id} unresolved in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record trend analysis reflections
        for trend_id, trend_state in self.trend_analysis.items():
            if trend_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Trend {trend_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record threshold state reflections
        for threshold_id, threshold_state in self.thresholds.items():
            if threshold_state.get("exceeded", False):
                await self.record_reflection(
                    f"Threshold {threshold_id} exceeded in {self.domain} domain",
                    domain=self.domain
                )
        
        return result
        
    async def _update_metric_state(self, metric_id: str, content: Dict[str, Any]):
        """Update metric state tracking."""
        if metric_id not in self.active_metrics:
            self.active_metrics[metric_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "value": None,
                "type": "gauge",
                "unit": "unknown",
                "metadata": {},
                "needs_attention": False,
                "thresholds": {},
                "history": []
            }
            
        metric_state = self.active_metrics[metric_id]
        
        # Update basic state
        if value := content.get("metric_value"):
            metric_state["value"] = value
            metric_state["history"].append({
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
            
        if unit := content.get("metric_unit"):
            metric_state["unit"] = unit
            
        if type_ := content.get("metric_type"):
            metric_state["type"] = type_
            
        # Update metadata
        if metadata := content.get("metric_metadata", {}):
            metric_state["metadata"].update(metadata)
            
        # Check thresholds
        if thresholds := content.get("metric_thresholds", {}):
            metric_state["thresholds"].update(thresholds)
            metric_state["needs_attention"] = any(
                value > threshold.get("max", float("inf")) or
                value < threshold.get("min", float("-inf"))
                for threshold in thresholds.values()
            )
            
    async def _update_health_check(self, check_id: str, content: Dict[str, Any]):
        """Update health check tracking."""
        if check_id not in self.health_checks:
            self.health_checks[check_id] = {
                "status": "unknown",
                "last_check": None,
                "check_type": "unknown",
                "metadata": {},
                "history": []
            }
            
        check_state = self.health_checks[check_id]
        
        # Update basic state
        if status := content.get("check_status"):
            check_state["status"] = status
            check_state["last_check"] = datetime.now().isoformat()
            check_state["history"].append({
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            
        if type_ := content.get("check_type"):
            check_state["check_type"] = type_
            
        # Update metadata
        if metadata := content.get("check_metadata", {}):
            check_state["metadata"].update(metadata)
            
        # Process check result
        if check_state["status"] == "failing":
            # Create alert if needed
            alert_id = f"alert_{check_id}"
            if alert_id not in self.alert_states:
                self.alert_states[alert_id] = {
                    "status": "triggered",
                    "source": check_id,
                    "severity": content.get("severity", "medium"),
                    "created_at": datetime.now().isoformat()
                }
                
            # Create incident if needed
            incident_id = f"incident_{check_id}"
            if incident_id not in self.incident_tracking:
                self.incident_tracking[incident_id] = {
                    "status": "unresolved",
                    "source": check_id,
                    "severity": content.get("severity", "medium"),
                    "created_at": datetime.now().isoformat(),
                    "steps_taken": []
                }
                
    def _update_thresholds(self, thresholds: Dict[str, Dict]):
        """Update threshold configurations."""
        for threshold_id, threshold in thresholds.items():
            if isinstance(threshold, dict):
                self.thresholds[threshold_id] = {
                    "type": threshold.get("type", "static"),
                    "min": float(threshold.get("min", float("-inf"))),
                    "max": float(threshold.get("max", float("inf"))),
                    "unit": threshold.get("unit", "unknown"),
                    "exceeded": False,
                    "metadata": threshold.get("metadata", {})
                }
                
    async def _update_trend_analysis(self, trends: Dict[str, Dict]):
        """Update trend analysis tracking."""
        for trend_id, trend in trends.items():
            if isinstance(trend, dict):
                current = self.trend_analysis.get(trend_id, {})
                
                self.trend_analysis[trend_id] = {
                    "type": trend.get("type", current.get("type", "unknown")),
                    "window": trend.get("window", current.get("window", "1h")),
                    "aggregation": trend.get("aggregation", current.get("aggregation", "avg")),
                    "data_points": trend.get("data_points", current.get("data_points", [])),
                    "needs_attention": trend.get("needs_attention", current.get("needs_attention", False)),
                    "metadata": trend.get("metadata", current.get("metadata", {}))
                }
                
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
