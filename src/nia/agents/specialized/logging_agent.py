"""TinyTroupe logging agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.base import NovaAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class LoggingAgent(NovaAgent, TinyTroupeAgent):
    """Logging agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize logging agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaAgent first
        NovaAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain,
            agent_type="logging"
        )
        
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="logging"
        )
        
        # Initialize logging-specific attributes
        self._initialize_logging_attributes()
        
        # Initialize logging tracking
        self.active_logs = {}  # log_id -> log_state
        self.format_templates = {}  # template_id -> template_config
        self.storage_policies = {}  # policy_id -> policy_config
        self.context_rules = {}  # rule_id -> rule_config
        self.enrichment_rules = {}  # rule_id -> rule_config
        self.rotation_policies = {}  # policy_id -> policy_config
        
    def _initialize_logging_attributes(self):
        """Initialize logging-specific attributes."""
        attributes = {
            "occupation": "Advanced Log Manager",
            "desires": [
                "Process logs effectively",
                "Manage log levels",
                "Handle log contexts",
                "Maintain logging quality",
                "Structure logs efficiently",
                "Enrich context properly",
                "Format logs consistently",
                "Optimize storage patterns",
                "Manage rotations",
                "Adapt to patterns"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_logs": "focused",
                "towards_domain": "mindful",
                "towards_structure": "precise",
                "towards_context": "attentive",
                "towards_format": "consistent",
                "towards_storage": "efficient",
                "towards_rotation": "proactive",
                "towards_adaptation": "adaptive"
            },
            "capabilities": [
                "log_processing",
                "level_management",
                "context_handling",
                "pattern_logging",
                "structure_optimization",
                "context_enrichment",
                "format_management",
                "storage_optimization",
                "rotation_handling",
                "pattern_adaptation"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced logging awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update log tracking
        if log_id := content.get("log_id"):
            await self._update_log_state(log_id, content)
            
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on logging results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on logging results
                if concept.get("type") == "logging_result":
                    self.emotions.update({
                        "logging_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on logging needs
                if concept.get("type") == "logging_need":
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
                        
                # Update structure state emotions
                if concept.get("type") == "structure_state":
                    self.emotions.update({
                        "structure_state": concept.get("state", "neutral")
                    })
                    
                # Update context state emotions
                if concept.get("type") == "context_state":
                    self.emotions.update({
                        "context_state": concept.get("state", "neutral")
                    })
                    
                # Update format state emotions
                if concept.get("type") == "format_state":
                    self.emotions.update({
                        "format_state": concept.get("state", "neutral")
                    })
                    
                # Update storage state emotions
                if concept.get("type") == "storage_state":
                    self.emotions.update({
                        "storage_state": concept.get("state", "neutral")
                    })
                    
                # Update rotation state emotions
                if concept.get("type") == "rotation_state":
                    self.emotions.update({
                        "rotation_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def process_and_store(
        self,
        content: Dict[str, Any],
        logging_type: str,
        target_domain: Optional[str] = None
    ):
        """Process logs and store results with enhanced logging awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Update format templates if needed
        if templates := content.get("format_templates"):
            self._update_format_templates(templates)
            
        # Update storage policies
        if policies := content.get("storage_policies"):
            self._update_storage_policies(policies)
            
        # Update context rules
        if rules := content.get("context_rules"):
            self._update_context_rules(rules)
            
        # Update enrichment rules
        if rules := content.get("enrichment_rules"):
            self._update_enrichment_rules(rules)
            
        # Update rotation policies
        if policies := content.get("rotation_policies"):
            self._update_rotation_policies(policies)
            
        # Process logs
        result = await self.process(
            content,
            metadata={
                "type": logging_type,
                "domain": target_domain or self.domain
            }
        )
        
        # Store logging results with enhanced metadata
        await self.store_memory(
            content={
                "type": "log_processing",
                "content": content,
                "logging_type": logging_type,
                "logging": {
                    "is_valid": result.is_valid,
                    "logging": result.logging,
                    "logs": result.logs,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "log_states": self.active_logs,
                    "format_states": self.format_templates,
                    "storage_states": self.storage_policies,
                    "context_states": self.context_rules,
                    "enrichment_states": self.enrichment_rules,
                    "rotation_states": self.rotation_policies,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "logging",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on logging result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence logging completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Logging failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical logging issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important logs
        important_logs = [
            l for l in result.logs
            if l.get("importance", 0.0) > 0.8
        ]
        if important_logs:
            await self.record_reflection(
                f"Important logs processed in {self.domain} domain",
                domain=self.domain
            )
            
        # Record log-specific reflections
        for log_id, log_state in self.active_logs.items():
            if log_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Log {log_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record format state reflections
        for template_id, template_state in self.format_templates.items():
            if template_state.get("needs_update", False):
                await self.record_reflection(
                    f"Format template {template_id} needs update in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record storage state reflections
        for policy_id, policy_state in self.storage_policies.items():
            if policy_state.get("needs_optimization", False):
                await self.record_reflection(
                    f"Storage policy {policy_id} needs optimization in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record context state reflections
        for rule_id, rule_state in self.context_rules.items():
            if rule_state.get("needs_tuning", False):
                await self.record_reflection(
                    f"Context rule {rule_id} needs tuning in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record enrichment state reflections
        for rule_id, rule_state in self.enrichment_rules.items():
            if rule_state.get("needs_update", False):
                await self.record_reflection(
                    f"Enrichment rule {rule_id} needs update in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record rotation state reflections
        for policy_id, policy_state in self.rotation_policies.items():
            if policy_state.get("needs_review", False):
                await self.record_reflection(
                    f"Rotation policy {policy_id} needs review in {self.domain} domain",
                    domain=self.domain
                )
        
        return result
        
    async def _update_log_state(self, log_id: str, content: Dict[str, Any]):
        """Update log state tracking."""
        if log_id not in self.active_logs:
            self.active_logs[log_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "level": None,
                "type": "unknown",
                "format": "default",
                "metadata": {},
                "needs_attention": False,
                "context": {},
                "history": []
            }
            
        log_state = self.active_logs[log_id]
        
        # Update basic state
        if level := content.get("log_level"):
            log_state["level"] = level
            log_state["history"].append({
                "level": level,
                "timestamp": datetime.now().isoformat()
            })
            
        if type_ := content.get("log_type"):
            log_state["type"] = type_
            
        if format_ := content.get("log_format"):
            log_state["format"] = format_
            
        # Update metadata
        if metadata := content.get("log_metadata", {}):
            log_state["metadata"].update(metadata)
            
        # Update context
        if context := content.get("log_context", {}):
            log_state["context"].update(context)
            log_state["needs_attention"] = any(
                ctx.get("priority", 0.0) > 0.8
                for ctx in context.values()
            )
            
        # Apply format templates
        for template_id, template in self.format_templates.items():
            if self._matches_format_template(content, template):
                await self._apply_format_template(log_id, template_id, template)
                
    def _update_format_templates(self, templates: Dict[str, Dict]):
        """Update format template configurations."""
        for template_id, template in templates.items():
            if isinstance(template, dict):
                self.format_templates[template_id] = {
                    "type": template.get("type", "static"),
                    "pattern": template.get("pattern", ""),
                    "format": template.get("format", ""),
                    "needs_update": template.get("needs_update", False),
                    "metadata": template.get("metadata", {})
                }
                
    def _update_storage_policies(self, policies: Dict[str, Dict]):
        """Update storage policy configurations."""
        for policy_id, policy in policies.items():
            if isinstance(policy, dict):
                self.storage_policies[policy_id] = {
                    "type": policy.get("type", "static"),
                    "pattern": policy.get("pattern", ""),
                    "storage": policy.get("storage", "local"),
                    "needs_optimization": policy.get("needs_optimization", False),
                    "metadata": policy.get("metadata", {})
                }
                
    def _update_context_rules(self, rules: Dict[str, Dict]):
        """Update context rule configurations."""
        for rule_id, rule in rules.items():
            if isinstance(rule, dict):
                self.context_rules[rule_id] = {
                    "type": rule.get("type", "static"),
                    "pattern": rule.get("pattern", ""),
                    "context": rule.get("context", {}),
                    "needs_tuning": rule.get("needs_tuning", False),
                    "metadata": rule.get("metadata", {})
                }
                
    def _update_enrichment_rules(self, rules: Dict[str, Dict]):
        """Update enrichment rule configurations."""
        for rule_id, rule in rules.items():
            if isinstance(rule, dict):
                self.enrichment_rules[rule_id] = {
                    "type": rule.get("type", "static"),
                    "pattern": rule.get("pattern", ""),
                    "enrichment": rule.get("enrichment", {}),
                    "needs_update": rule.get("needs_update", False),
                    "metadata": rule.get("metadata", {})
                }
                
    def _update_rotation_policies(self, policies: Dict[str, Dict]):
        """Update rotation policy configurations."""
        for policy_id, policy in policies.items():
            if isinstance(policy, dict):
                self.rotation_policies[policy_id] = {
                    "type": policy.get("type", "time"),
                    "interval": policy.get("interval", "daily"),
                    "retention": policy.get("retention", 30),
                    "needs_review": policy.get("needs_review", False),
                    "metadata": policy.get("metadata", {})
                }
                
    def _matches_format_template(self, content: Dict[str, Any], template: Dict) -> bool:
        """Check if content matches a format template."""
        pattern = template.get("pattern", "")
        if not pattern:
            return False
            
        # Check pattern against log content
        if "message" in content:
            import re
            return bool(re.search(pattern, str(content["message"])))
            
        return False
        
    async def _apply_format_template(
        self,
        log_id: str,
        template_id: str,
        template: Dict
    ):
        """Apply a format template's formatting."""
        log_state = self.active_logs[log_id]
        format_config = template.get("format", {})
        
        # Apply formatting
        if isinstance(format_config, dict):
            if "timestamp_format" in format_config:
                log_state["metadata"]["timestamp_format"] = format_config["timestamp_format"]
            if "level_format" in format_config:
                log_state["metadata"]["level_format"] = format_config["level_format"]
            if "message_format" in format_config:
                log_state["metadata"]["message_format"] = format_config["message_format"]
                
        # Record format application
        log_state["history"].append({
            "format_template": template_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Record reflection if needed
        if template.get("needs_update", False):
            await self.record_reflection(
                f"Format template {template_id} applied to {log_id} needs update",
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
                f"LoggingAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
