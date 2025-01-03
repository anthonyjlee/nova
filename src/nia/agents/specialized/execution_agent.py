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
        # Initialize NovaExecutionAgent first
        NovaExecutionAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes or {},
            agent_type="execution"
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
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
        try:
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
            logger.debug("Successfully initialized execution attributes")
        except Exception as e:
            logger.error(f"Failed to initialize execution attributes: {str(e)}")
            # Set default attributes
            self.attributes = {
                "occupation": "Advanced Action Executor",
                "desires": ["Execute actions effectively"],
                "emotions": {"baseline": "analytical"},
                "domain": self.domain,
                "capabilities": ["action_execution"]
            }
