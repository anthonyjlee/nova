"""TinyTroupe metrics agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.metrics import MetricsAgent as NovaMetricsAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class MetricsAgent(NovaMetricsAgent, TinyTroupeAgent):
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
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaMetricsAgent first
        NovaMetricsAgent.__init__(
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
            agent_type="metrics"
        )
        
        # Initialize metrics-specific attributes
        self._initialize_metrics_attributes()
        
        # Initialize metrics tracking
        self.active_metrics = {}  # metric_id -> metric_state
        self.collection_strategies = {}  # strategy_id -> strategy_config
        self.aggregation_rules = {}  # rule_id -> rule_config
        self.calculation_templates = {}  # template_id -> template_config
        self.retention_policies = {}  # policy_id -> policy_config
        
    def _initialize_metrics_attributes(self):
        """Initialize metrics-specific attributes."""
        attributes = {
            "occupation": "Advanced Metrics Manager",
            "desires": [
                "Process metrics effectively",
                "Track performance metrics",
                "Monitor resource usage",
                "Maintain metrics quality",
                "Collect metrics efficiently",
                "Aggregate data properly",
                "Calculate insights accurately",
                "Optimize storage patterns",
                "Manage retention",
                "Adapt to patterns"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_metrics": "focused",
                "towards_domain": "mindful",
                "towards_collection": "precise",
                "towards_aggregation": "systematic",
                "towards_calculation": "accurate",
                "towards_storage": "efficient",
                "towards_retention": "proactive",
                "towards_adaptation": "adaptive"
            },
            "capabilities": [
                "metrics_processing",
                "performance_tracking",
                "resource_monitoring",
                "pattern_metrics",
                "collection_optimization",
                "aggregation_management",
                "calculation_handling",
                "storage_optimization",
                "retention_handling",
                "pattern_adaptation"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced metrics awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update metric tracking
        if metric_id := content.get("metric_id"):
            await self._update_metric_state(metric_id, content)
            
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
                        
                # Update collection state emotions
                if concept.get("type") == "collection_state":
                    self.emotions.update({
                        "collection_state": concept.get("state", "neutral")
                    })
                    
                # Update aggregation state emotions
                if concept.get("type") == "aggregation_state":
                    self.emotions.update({
                        "aggregation_state": concept.get("state", "neutral")
                    })
                    
                # Update calculation state emotions
                if concept.get("type") == "calculation_state":
                    self.emotions.update({
                        "calculation_state": concept.get("state", "neutral")
                    })
                    
                # Update storage state emotions
                if concept.get("type") == "storage_state":
                    self.emotions.update({
                        "storage_state": concept.get("state", "neutral")
                    })
                    
                # Update retention state emotions
                if concept.get("type") == "retention_state":
                    self.emotions.update({
                        "retention_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def process_and_store(
        self,
        content: Dict[str, Any],
        metrics_type: str,
        target_domain: Optional[str] = None
    ):
        """Process metrics and store results with enhanced metrics awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Update collection strategies if needed
        if strategies := content.get("collection_strategies"):
            self._update_collection_strategies(strategies)
            
        # Update aggregation rules
        if rules := content.get("aggregation_rules"):
            self._update_aggregation_rules(rules)
            
        # Update calculation templates
        if templates := content.get("calculation_templates"):
            self._update_calculation_templates(templates)
            
        # Update retention policies
        if policies := content.get("retention_policies"):
            self._update_retention_policies(policies)
            
        # Process metrics
        result = await self.process_metrics(
            content,
            metrics_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store metrics results with enhanced metadata
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
                    "metric_states": self.active_metrics,
                    "collection_states": self.collection_strategies,
                    "aggregation_states": self.aggregation_rules,
                    "calculation_states": self.calculation_templates,
                    "retention_states": self.retention_policies,
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
            
        # Record metric-specific reflections
        for metric_id, metric_state in self.active_metrics.items():
            if metric_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Metric {metric_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record collection state reflections
        for strategy_id, strategy_state in self.collection_strategies.items():
            if strategy_state.get("needs_optimization", False):
                await self.record_reflection(
                    f"Collection strategy {strategy_id} needs optimization in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record aggregation state reflections
        for rule_id, rule_state in self.aggregation_rules.items():
            if rule_state.get("needs_tuning", False):
                await self.record_reflection(
                    f"Aggregation rule {rule_id} needs tuning in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record calculation state reflections
        for template_id, template_state in self.calculation_templates.items():
            if template_state.get("needs_update", False):
                await self.record_reflection(
                    f"Calculation template {template_id} needs update in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record retention state reflections
        for policy_id, policy_state in self.retention_policies.items():
            if policy_state.get("needs_review", False):
                await self.record_reflection(
                    f"Retention policy {policy_id} needs review in {self.domain} domain",
                    domain=self.domain
                )
        
        return result
        
    async def _update_metric_state(self, metric_id: str, content: Dict[str, Any]):
        """Update metric state tracking."""
        if metric_id not in self.active_metrics:
            self.active_metrics[metric_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "type": "unknown",
                "value": None,
                "unit": "",
                "metadata": {},
                "needs_attention": False,
                "aggregations": {},
                "history": []
            }
            
        metric_state = self.active_metrics[metric_id]
        
        # Update basic state
        if type_ := content.get("metric_type"):
            metric_state["type"] = type_
            metric_state["history"].append({
                "type": type_,
                "timestamp": datetime.now().isoformat()
            })
            
        if value := content.get("metric_value"):
            metric_state["value"] = value
            
        if unit := content.get("metric_unit"):
            metric_state["unit"] = unit
            
        # Update metadata
        if metadata := content.get("metric_metadata", {}):
            metric_state["metadata"].update(metadata)
            
        # Update aggregations
        if aggregations := content.get("metric_aggregations", {}):
            metric_state["aggregations"].update(aggregations)
            metric_state["needs_attention"] = any(
                agg.get("priority", 0.0) > 0.8
                for agg in aggregations.values()
            )
            
        # Apply calculation templates
        for template_id, template in self.calculation_templates.items():
            if self._matches_calculation_template(content, template):
                await self._apply_calculation_template(metric_id, template_id, template)
                
    def _update_collection_strategies(self, strategies: Dict[str, Dict]):
        """Update collection strategy configurations."""
        for strategy_id, strategy in strategies.items():
            if isinstance(strategy, dict):
                self.collection_strategies[strategy_id] = {
                    "type": strategy.get("type", "static"),
                    "interval": strategy.get("interval", "hourly"),
                    "batch_size": strategy.get("batch_size", 100),
                    "needs_optimization": strategy.get("needs_optimization", False),
                    "metadata": strategy.get("metadata", {})
                }
                
    def _update_aggregation_rules(self, rules: Dict[str, Dict]):
        """Update aggregation rule configurations."""
        for rule_id, rule in rules.items():
            if isinstance(rule, dict):
                self.aggregation_rules[rule_id] = {
                    "type": rule.get("type", "static"),
                    "function": rule.get("function", "avg"),
                    "window": rule.get("window", "1h"),
                    "needs_tuning": rule.get("needs_tuning", False),
                    "metadata": rule.get("metadata", {})
                }
                
    def _update_calculation_templates(self, templates: Dict[str, Dict]):
        """Update calculation template configurations."""
        for template_id, template in templates.items():
            if isinstance(template, dict):
                self.calculation_templates[template_id] = {
                    "type": template.get("type", "static"),
                    "formula": template.get("formula", ""),
                    "variables": template.get("variables", {}),
                    "needs_update": template.get("needs_update", False),
                    "metadata": template.get("metadata", {})
                }
                
    def _update_retention_policies(self, policies: Dict[str, Dict]):
        """Update retention policy configurations."""
        for policy_id, policy in policies.items():
            if isinstance(policy, dict):
                self.retention_policies[policy_id] = {
                    "type": policy.get("type", "time"),
                    "duration": policy.get("duration", "30d"),
                    "compression": policy.get("compression", "none"),
                    "needs_review": policy.get("needs_review", False),
                    "metadata": policy.get("metadata", {})
                }
                
    def _matches_calculation_template(self, content: Dict[str, Any], template: Dict) -> bool:
        """Check if content matches a calculation template."""
        variables = template.get("variables", {})
        if not variables:
            return False
            
        # Check if all required variables are present
        for var_name, var_config in variables.items():
            if var_name not in content:
                return False
                
            # Validate variable type
            if var_config.get("type") == "number":
                try:
                    float(content[var_name])
                except (TypeError, ValueError):
                    return False
                    
        return True
        
    async def _apply_calculation_template(
        self,
        metric_id: str,
        template_id: str,
        template: Dict
    ):
        """Apply a calculation template's formula."""
        metric_state = self.active_metrics[metric_id]
        formula = template.get("formula", "")
        variables = template.get("variables", {})
        
        if formula and variables:
            try:
                # Create variable mapping
                var_values = {}
                for var_name, var_config in variables.items():
                    if var_config.get("type") == "number":
                        var_values[var_name] = float(metric_state["value"])
                        
                # Evaluate formula
                import math
                result = eval(formula, {"math": math}, var_values)
                
                # Update metric state
                metric_state["value"] = result
                metric_state["history"].append({
                    "calculation": template_id,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Record reflection if needed
                if template.get("needs_update", False):
                    await self.record_reflection(
                        f"Calculation template {template_id} applied to {metric_id} needs update",
                        domain=self.domain
                    )
                    
            except Exception as e:
                logger.error(f"Error applying calculation template: {str(e)}")
                
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
