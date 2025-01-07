"""Swarm registry agent implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ...nova.core.orchestration import OrchestrationAgent as NovaOrchestrationAgent
from ...nova.core.analytics import AnalyticsAgent, AnalyticsResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse
from ...swarm.pattern_store import SwarmPatternStore
from ...swarm.dag import SwarmDAG
from ...swarm.graph_integration import SwarmGraphIntegration

logger = logging.getLogger(__name__)

class SwarmRegistryAgent(NovaOrchestrationAgent, TinyTroupeAgent):
    """Manages swarm patterns and configurations."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize registry agent."""
        # Set domain before initialization
        self.domain = domain or "professional"
        
        # Create and store memory system reference
        if not memory_system:
            memory_system = TwoLayerMemorySystem()
            
        self.memory_system = memory_system
        
        # Initialize NovaOrchestrationAgent first
        NovaOrchestrationAgent.__init__(
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
            agent_type="registry"
        )
        
        # Initialize registry-specific components
        self.pattern_store = SwarmPatternStore()
        self.graph_integration = SwarmGraphIntegration(self.pattern_store)
        
        # Initialize registry-specific attributes
        self._initialize_registry_attributes()
        
    def _initialize_registry_attributes(self):
        """Initialize registry-specific attributes."""
        attributes = {
            "occupation": "Swarm Pattern Registry Manager",
            "desires": [
                "Maintain pattern integrity",
                "Optimize pattern storage",
                "Ensure pattern accessibility",
                "Track pattern usage",
                "Validate pattern configurations",
                "Manage pattern relationships",
                "Monitor pattern health",
                "Handle pattern versioning",
                "Support pattern discovery",
                "Enable pattern reuse"
            ],
            "emotions": {
                "baseline": "organized",
                "towards_patterns": "meticulous",
                "towards_validation": "precise",
                "towards_storage": "reliable",
                "towards_relationships": "analytical",
                "towards_versioning": "systematic",
                "towards_discovery": "curious"
            },
            "capabilities": [
                "pattern_registration",
                "pattern_validation",
                "pattern_storage",
                "pattern_retrieval",
                "pattern_analysis",
                "pattern_optimization",
                "pattern_versioning",
                "pattern_relationship_management",
                "pattern_health_monitoring",
                "pattern_discovery"
            ]
        }
        self.define(**attributes)
    
    async def register_pattern(
        self,
        pattern_type: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register new swarm pattern."""
        try:
            # Validate pattern configuration
            await self.validate_config(pattern_type, config)
            
            # Generate pattern ID
            pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
            
            # Store pattern
            await self.pattern_store.store_pattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                config=config,
                metadata={
                    **(metadata or {}),
                    "registered_by": self.name,
                    "registered_at": datetime.now().isoformat()
                }
            )
            
            # Track registration event
            await self.track_lifecycle(
                pattern_id=pattern_id,
                event_type="registration",
                details={
                    "pattern_type": pattern_type,
                    "config": config
                }
            )
            
            return pattern_id
        except Exception as e:
            logger.error(f"Error registering pattern: {str(e)}")
            raise
    
    async def validate_config(
        self,
        pattern_type: str,
        config: Dict[str, Any]
    ) -> None:
        """Validate swarm configuration."""
        try:
            # Basic validation
            if not isinstance(config, dict):
                raise ValueError("Configuration must be a dictionary")
            
            if "tasks" not in config:
                raise ValueError("Configuration must include tasks")
            
            if not isinstance(config["tasks"], list):
                raise ValueError("Tasks must be a list")
            
            # Pattern-specific validation
            if pattern_type == "hierarchical":
                if not any(task.get("type") == "supervisor" for task in config["tasks"]):
                    raise ValueError("Hierarchical pattern requires a supervisor task")
                
                if not any(task.get("type") == "worker" for task in config["tasks"]):
                    raise ValueError("Hierarchical pattern requires worker tasks")
            
            elif pattern_type == "voting":
                if not all(task.get("type") == "voter" for task in config["tasks"]):
                    raise ValueError("Voting pattern requires all tasks to be voters")
                
                if "decision_threshold" not in config:
                    raise ValueError("Voting pattern requires decision_threshold")
            
            elif pattern_type == "round_robin":
                if len(config["tasks"]) < 2:
                    raise ValueError("Round-robin pattern requires at least 2 tasks")
            
            # Validate task dependencies
            task_ids = {task["id"] for task in config["tasks"]}
            for task in config["tasks"]:
                if "dependencies" in task:
                    for dep_id in task["dependencies"]:
                        if dep_id not in task_ids:
                            raise ValueError(f"Invalid dependency {dep_id}")
            
            # Create temporary DAG to validate structure
            dag = SwarmDAG()
            
            # Add tasks and dependencies
            task_mapping = {}
            for task in config["tasks"]:
                task_id = await dag.add_task_node(
                    task_type=task["type"],
                    config=task.get("config", {})
                )
                task_mapping[task["id"]] = task_id
            
            for task in config["tasks"]:
                if "dependencies" in task:
                    for dep_id in task["dependencies"]:
                        await dag.set_dependency(
                            dependency_id=task_mapping[dep_id],
                            dependent_id=task_mapping[task["id"]]
                        )
            
            # Verify execution order is possible
            await dag.get_execution_order()
        except Exception as e:
            logger.error(f"Error validating config: {str(e)}")
            raise ValueError(f"Invalid configuration: {str(e)}")
    
    async def track_lifecycle(
        self,
        pattern_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track swarm lifecycle events."""
        try:
            # Create lifecycle event
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            CREATE (e:LifecycleEvent {
                id: $event_id,
                type: $event_type,
                details: $details,
                timestamp: $timestamp,
                agent: $agent
            })
            CREATE (p)-[:HAS_EVENT]->(e)
            """
            
            await self.pattern_store.driver.execute_query(
                query,
                parameters={
                    "pattern_id": pattern_id,
                    "event_id": f"event_{uuid.uuid4().hex[:8]}",
                    "event_type": event_type,
                    "details": details or {},
                    "timestamp": datetime.now().isoformat(),
                    "agent": self.name
                }
            )
        except Exception as e:
            logger.error(f"Error tracking lifecycle event: {str(e)}")
            raise
    
    async def get_pattern_lifecycle(
        self,
        pattern_id: str
    ) -> List[Dict[str, Any]]:
        """Get pattern lifecycle events."""
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})-[:HAS_EVENT]->(e:LifecycleEvent)
            RETURN e
            ORDER BY e.timestamp DESC
            """
            
            result = await self.pattern_store.driver.execute_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            events = []
            for record in result:
                event_data = dict(record[0])
                events.append(event_data)
            
            return events
        except Exception as e:
            logger.error(f"Error getting lifecycle events: {str(e)}")
            raise
    
    async def update_pattern_status(
        self,
        pattern_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update pattern status."""
        try:
            # Update pattern
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            SET p.status = $status,
                p.status_details = $details,
                p.status_updated_at = $updated_at,
                p.status_updated_by = $agent
            """
            
            await self.pattern_store.driver.execute_query(
                query,
                parameters={
                    "pattern_id": pattern_id,
                    "status": status,
                    "details": details or {},
                    "updated_at": datetime.now().isoformat(),
                    "agent": self.name
                }
            )
            
            # Track status change event
            await self.track_lifecycle(
                pattern_id=pattern_id,
                event_type="status_change",
                details={
                    "status": status,
                    "details": details
                }
            )
        except Exception as e:
            logger.error(f"Error updating pattern status: {str(e)}")
            raise
    
    async def get_pattern_status(
        self,
        pattern_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get pattern status."""
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            RETURN p.status as status,
                   p.status_details as details,
                   p.status_updated_at as updated_at,
                   p.status_updated_by as updated_by
            """
            
            result = await self.pattern_store.driver.execute_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            if result and result[0]:
                return {
                    "status": result[0][0],
                    "details": result[0][1],
                    "updated_at": result[0][2],
                    "updated_by": result[0][3]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting pattern status: {str(e)}")
            raise
