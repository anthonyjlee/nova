"""TinyTroupe execution agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.execution import ExecutionAgent as NovaExecutionAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ExecutionAgent(NovaExecutionAgent, TinyTroupeAgent):  # Changed inheritance order
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
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaExecutionAgent first
        NovaExecutionAgent.__init__(
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
            agent_type="execution"
        )
        
        # Initialize execution tracking
        self.active_sequences = {}  # sequence_id -> sequence_state
        self.execution_patterns = {}  # pattern_id -> pattern_config
        self.resource_usage = {}  # resource_id -> usage_state
        self.error_recovery = {}  # error_id -> recovery_state
        self.retry_states = {}  # action_id -> retry_state
        self.schedule_queue = {}  # priority -> action_queue
        
        # Initialize execution-specific attributes
        self._initialize_execution_attributes()
        
    def _initialize_execution_attributes(self):
        """Initialize execution-specific attributes."""
        attributes = {
            "occupation": "Advanced Action Executor",
            "desires": [
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
            "emotions": {
                "baseline": "analytical",
                "towards_actions": "focused",
                "towards_domain": "mindful",
                "towards_sequences": "attentive",
                "towards_resources": "efficient",
                "towards_errors": "resilient",
                "towards_schedules": "organized",
                "towards_adaptation": "responsive"
            },
            "capabilities": [
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
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
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
                    self.desires.append(f"Address {concept['name']}")
                    
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
                    
                # Update emotions based on resource state
                if concept.get("type") == "resource_state":
                    self.emotions.update({
                        "resource_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def execute_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Execute actions and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Execute actions
        result = await self.execute_actions(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store execution results
        await self.store_memory(
            content={
                "type": "execution_result",
                "content": content,
                "execution": {
                    "is_valid": result.is_valid,
                    "actions": result.actions,
                    "status": result.status,
                    "resources": result.resources,
                    "issues": result.issues,
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
        if result.is_valid:
            await self.record_reflection(
                f"Execution completed successfully in {self.domain} domain",
                domain=self.domain
            )
        else:
            await self.record_reflection(
                f"Execution failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for resource issues
        resource_issues = [
            i for i in result.issues
            if i.get("type") == "resource_issue"
        ]
        if resource_issues:
            await self.record_reflection(
                f"Resource issues detected in {self.domain} domain - optimization needed",
                domain=self.domain
            )
            
        # Record reflection for retry attempts
        if result.status.get("retries", 0) > 0:
            await self.record_reflection(
                f"Multiple retry attempts needed in {self.domain} domain",
                domain=self.domain
            )
            
        # Update execution state
        self._update_execution_state(result)
        
        return result
        
    def _update_execution_state(self, result):
        """Update internal execution state tracking."""
        # Update active sequences
        for sequence_id, sequence in result.actions.items():
            if sequence["status"] == "active":
                self.active_sequences[sequence_id] = sequence
            else:
                self.active_sequences.pop(sequence_id, None)
                
        # Update resource usage
        for resource_id, usage in result.resources.items():
            self.resource_usage[resource_id] = usage
            
        # Update error recovery states
        for issue in result.issues:
            if issue.get("requires_recovery"):
                self.error_recovery[issue["id"]] = {
                    "status": "pending",
                    "strategy": issue.get("recovery_strategy"),
                    "attempts": 0
                }
                
        # Update retry states
        for action_id, status in result.status.get("action_states", {}).items():
            if status.get("needs_retry"):
                self.retry_states[action_id] = {
                    "attempts": status.get("retry_count", 0),
                    "next_attempt": datetime.now().isoformat(),
                    "strategy": status.get("retry_strategy")
                }
                
        # Update schedule queue
        for action in result.actions.values():
            priority = action.get("priority", 0)
            if priority not in self.schedule_queue:
                self.schedule_queue[priority] = []
            if action["status"] == "pending":
                self.schedule_queue[priority].append(action)
                
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
