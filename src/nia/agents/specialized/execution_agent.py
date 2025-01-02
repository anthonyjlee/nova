"""TinyTroupe execution agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.execution import ExecutionAgent as NovaExecutionAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ExecutionAgent(TinyTroupeAgent, NovaExecutionAgent):
    """Execution agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize execution agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="execution"
        )
        
        # Initialize NovaExecutionAgent
        NovaExecutionAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize execution-specific attributes
        self._initialize_execution_attributes()
        
        # Initialize execution tracking
        self.active_sequences = {}  # sequence_id -> sequence_state
        self.execution_patterns = {}  # pattern_id -> pattern_config
        self.resource_usage = {}  # resource_id -> usage_state
        self.error_recovery = {}  # error_id -> recovery_state
        self.retry_states = {}  # action_id -> retry_state
        self.schedule_queue = {}  # priority -> action_queue
        
    def _initialize_execution_attributes(self):
        """Initialize execution-specific attributes."""
        self.define(
            occupation="Advanced Action Executor",
            desires=[
                "Execute actions effectively",
                "Optimize step sequences",
                "Ensure action completion",
                "Maintain execution quality",
                "Optimize resource usage",
                "Handle errors gracefully",
                "Manage execution schedules",
                "Ensure system resilience",
                "Monitor execution progress",
                "Adapt to changing conditions"
            ],
            emotions={
                "baseline": "analytical",
                "towards_actions": "focused",
                "towards_domain": "mindful",
                "towards_sequences": "attentive",
                "towards_resources": "efficient",
                "towards_errors": "resilient",
                "towards_schedules": "organized",
                "towards_adaptation": "responsive"
            },
            domain=self.domain,
            capabilities=[
                "action_execution",
                "step_coordination",
                "sequence_optimization",
                "pattern_execution",
                "resource_optimization",
                "error_recovery",
                "schedule_management",
                "retry_handling",
                "progress_monitoring",
                "adaptive_execution"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced execution awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update sequence tracking
        if sequence_id := content.get("sequence_id"):
            await self._update_sequence_state(sequence_id, content)
            
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on execution results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on execution results
                if concept.get("type") == "execution_result":
                    self.emotions.update({
                        "execution_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on execution needs
                if concept.get("type") == "execution_need":
                    self.desires.append(f"Execute {concept['name']}")
                    
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
                        
                # Update sequence state emotions
                if concept.get("type") == "sequence_state":
                    self.emotions.update({
                        "sequence_state": concept.get("state", "neutral")
                    })
                    
                # Update resource state emotions
                if concept.get("type") == "resource_state":
                    self.emotions.update({
                        "resource_state": concept.get("state", "neutral")
                    })
                    
                # Update error state emotions
                if concept.get("type") == "error_state":
                    self.emotions.update({
                        "error_state": concept.get("state", "neutral")
                    })
                    
                # Update schedule state emotions
                if concept.get("type") == "schedule_state":
                    self.emotions.update({
                        "schedule_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def execute_and_store(
        self,
        content: Dict[str, Any],
        execution_type: str,
        target_domain: Optional[str] = None
    ):
        """Execute actions and store results with enhanced execution awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Update execution patterns if needed
        if patterns := content.get("execution_patterns"):
            self._update_execution_patterns(patterns)
            
        # Update resource usage
        if resources := content.get("resources"):
            await self._update_resource_usage(resources)
            
        # Update schedule queue
        if schedule := content.get("schedule"):
            self._update_schedule_queue(schedule)
            
        # Execute actions
        result = await self.execute_actions(
            content,
            execution_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store execution results with enhanced metadata
        await self.store_memory(
            content={
                "type": "action_execution",
                "content": content,
                "execution_type": execution_type,
                "execution": {
                    "is_valid": result.is_valid,
                    "execution": result.execution,
                    "actions": result.actions,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "sequence_states": self.active_sequences,
                    "resource_states": self.resource_usage,
                    "error_states": self.error_recovery,
                    "retry_states": self.retry_states,
                    "schedule_states": self.schedule_queue,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "execution",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on execution result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence execution completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Execution failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical execution issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important actions
        important_actions = [
            a for a in result.actions
            if a.get("importance", 0.0) > 0.8
        ]
        if important_actions:
            await self.record_reflection(
                f"Important action steps completed in {self.domain} domain execution",
                domain=self.domain
            )
            
        # Record sequence-specific reflections
        for sequence_id, sequence_state in self.active_sequences.items():
            if sequence_state.get("needs_optimization", False):
                await self.record_reflection(
                    f"Sequence {sequence_id} needs optimization in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record resource-specific reflections
        for resource_id, usage in self.resource_usage.items():
            if usage.get("utilization", 0.0) > 0.9:
                await self.record_reflection(
                    f"Resource {resource_id} nearing capacity in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record error recovery reflections
        for error_id, recovery in self.error_recovery.items():
            if recovery.get("status") == "failed":
                await self.record_reflection(
                    f"Error recovery failed for {error_id} in {self.domain} domain - escalation needed",
                    domain=self.domain
                )
                
        # Record retry state reflections
        for action_id, retry_state in self.retry_states.items():
            if retry_state.get("attempts", 0) >= retry_state.get("max_attempts", 3):
                await self.record_reflection(
                    f"Action {action_id} exceeded retry limit in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record schedule state reflections
        for priority, queue in self.schedule_queue.items():
            if len(queue) > queue.get("threshold", 10):
                await self.record_reflection(
                    f"Priority {priority} queue exceeding threshold in {self.domain} domain",
                    domain=self.domain
                )
        
        return result
        
    async def _update_sequence_state(self, sequence_id: str, content: Dict[str, Any]):
        """Update sequence state tracking."""
        if sequence_id not in self.active_sequences:
            self.active_sequences[sequence_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "steps_completed": 0,
                "current_phase": "initialization",
                "metrics": {},
                "needs_optimization": False,
                "resource_usage": {},
                "error_count": 0
            }
            
        sequence_state = self.active_sequences[sequence_id]
        
        # Update basic state
        if status := content.get("sequence_status"):
            sequence_state["status"] = status
            
        if phase := content.get("sequence_phase"):
            sequence_state["current_phase"] = phase
            
        # Update metrics
        if metrics := content.get("sequence_metrics", {}):
            sequence_state["metrics"].update(metrics)
            
        # Update completion tracking
        if content.get("step_completed"):
            sequence_state["steps_completed"] += 1
            
        # Update resource usage
        if resource_usage := content.get("resource_usage", {}):
            sequence_state["resource_usage"].update(resource_usage)
            
        # Update error tracking
        if content.get("error_occurred"):
            sequence_state["error_count"] += 1
            
        # Check optimization needs
        sequence_state["needs_optimization"] = any([
            content.get("needs_optimization", False),
            sequence_state["error_count"] > 3,
            any(usage > 0.8 for usage in sequence_state["resource_usage"].values())
        ])
        
        # Apply relevant execution patterns
        for pattern_id, pattern in self.execution_patterns.items():
            if self._matches_pattern(content, pattern):
                await self._apply_execution_pattern(sequence_id, pattern_id, pattern)
                
    def _update_execution_patterns(self, patterns: Dict[str, Dict]):
        """Update execution pattern configurations."""
        for pattern_id, pattern in patterns.items():
            if isinstance(pattern, dict):
                self.execution_patterns[pattern_id] = {
                    "conditions": pattern.get("conditions", {}),
                    "actions": pattern.get("actions", []),
                    "priority": float(pattern.get("priority", 0.5))
                }
                
    async def _update_resource_usage(self, resources: Dict[str, Dict]):
        """Update resource usage tracking."""
        for resource_id, usage in resources.items():
            if isinstance(usage, dict):
                current = self.resource_usage.get(resource_id, {})
                
                self.resource_usage[resource_id] = {
                    "type": usage.get("type", current.get("type", "unknown")),
                    "allocated": float(usage.get("allocated", current.get("allocated", 0.0))),
                    "utilized": float(usage.get("utilized", current.get("utilized", 0.0))),
                    "peak": float(usage.get("peak", current.get("peak", 0.0))),
                    "constraints": usage.get("constraints", current.get("constraints", {}))
                }
                
    def _update_schedule_queue(self, schedule: Dict[str, List[Dict]]):
        """Update schedule queue tracking."""
        for priority, actions in schedule.items():
            if isinstance(actions, list):
                if priority not in self.schedule_queue:
                    self.schedule_queue[priority] = {
                        "actions": [],
                        "threshold": 10,
                        "metrics": {}
                    }
                    
                self.schedule_queue[priority]["actions"].extend(actions)
                
    def _matches_pattern(self, content: Dict[str, Any], pattern: Dict) -> bool:
        """Check if content matches an execution pattern."""
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
        
    async def _apply_execution_pattern(
        self,
        sequence_id: str,
        pattern_id: str,
        pattern: Dict
    ):
        """Apply an execution pattern's actions."""
        sequence_state = self.active_sequences[sequence_id]
        
        for action in pattern.get("actions", []):
            action_type = action.get("type")
            
            if action_type == "update_phase":
                sequence_state["current_phase"] = action["phase"]
            elif action_type == "add_metric":
                sequence_state["metrics"][action["name"]] = action["value"]
            elif action_type == "set_optimization":
                sequence_state["needs_optimization"] = action["value"]
            elif action_type == "update_resource":
                sequence_state["resource_usage"][action["resource"]] = action["usage"]
            elif action_type == "record_reflection":
                await self.record_reflection(
                    f"Execution pattern {pattern_id} triggered in {sequence_id}: {action['message']}",
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
                f"ExecutionAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
