"""TinyTroupe coordination agent implementation."""

import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from ...nova.core.coordination import CoordinationAgent as NovaCoordinationAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class CoordinationAgent(TinyTroupeAgent, NovaCoordinationAgent):
    """Coordination agent with TinyTroupe and memory capabilities."""
    
    # Valid swarm architectures
    VALID_ARCHITECTURES = ["hierarchical", "parallel", "sequential", "mesh"]
    VALID_SWARM_TYPES = ["MajorityVoting", "RoundRobin", "GraphWorkflow"]
    VALID_COMMUNICATION_PATTERNS = ["broadcast", "direct", "group"]
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize coordination agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="coordination"
        )
        
        # Initialize NovaCoordinationAgent
        NovaCoordinationAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize coordination-specific attributes
        self._initialize_coordination_attributes()
        
        # Initialize swarm state
        self.active_groups = {}
        self.agent_assignments = {}
        self.resource_allocations = {}
        self.task_dependencies = {}
        
    def _initialize_coordination_attributes(self):
        """Initialize coordination-specific attributes."""
        self.define(
            occupation="Coordination Manager",
            desires=[
                "Manage agent groups effectively",
                "Optimize resource allocation",
                "Ensure task dependencies",
                "Maintain coordination quality",
                "Handle cross-domain interactions",
                "Resolve resource conflicts",
                "Monitor group performance"
            ],
            emotions={
                "baseline": "organized",
                "towards_coordination": "focused",
                "towards_domain": "mindful",
                "towards_resources": "efficient",
                "towards_groups": "collaborative"
            },
            domain=self.domain,
            capabilities={
                "group_management": True,
                "resource_allocation": True,
                "dependency_tracking": True,
                "conflict_resolution": True,
                "performance_monitoring": True,
                "domain_coordination": True,
                "state_management": True,
                "swarm": {
                    "architectures": self.VALID_ARCHITECTURES,
                    "types": self.VALID_SWARM_TYPES,
                    "roles": ["coordinator", "worker", "specialist"]
                }
            }
        )
        
    async def validate_swarm_architecture(self, architecture: str) -> None:
        """Validate and update swarm architecture."""
        if architecture not in self.VALID_ARCHITECTURES:
            raise ValueError(f"Invalid swarm architecture: {architecture}")
            
        self._configuration["swarm_architecture"] = architecture
        await self.record_reflection(
            f"Swarm architecture updated to {architecture}",
            domain=self.domain
        )
        
    async def handle_swarm_communication(self, pattern: str) -> Dict:
        """Handle swarm communication patterns."""
        if pattern not in self.VALID_COMMUNICATION_PATTERNS:
            raise KeyError(f"Invalid communication pattern: {pattern}")
            
        result = {
            "pattern": pattern,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
        
        if pattern == "broadcast":
            result["type"] = "all_agents"
        elif pattern == "direct":
            result["type"] = "point_to_point"
        elif pattern == "group":
            result["type"] = "group_based"
            
        return result
        
    async def manage_swarm_resources(self, swarm_type: str) -> Dict:
        """Manage resources based on swarm type."""
        if swarm_type not in self.VALID_SWARM_TYPES:
            raise KeyError(f"Invalid swarm type: {swarm_type}")
            
        result = {
            "type": swarm_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if swarm_type == "MajorityVoting":
            result["voting_resources"] = {
                "voting_power": self.resource_allocations.get("voting_power", 100),
                "quorum": 0.51
            }
        elif swarm_type == "RoundRobin":
            result["rotation_schedule"] = {
                "current_index": 0,
                "rotation_interval": 60  # seconds
            }
        elif swarm_type == "GraphWorkflow":
            result["workflow_resources"] = {
                "nodes": list(self.active_groups.keys()),
                "edges": list(self.task_dependencies.items())
            }
            
        return result
        
    async def track_swarm_metrics(self) -> Dict:
        """Track and analyze swarm metrics."""
        metrics = {
            "communication_overhead": 0.0,
            "resource_utilization": 0.0,
            "task_completion_rate": 0.0,
            "swarm_health": 0.0
        }
        
        # Calculate communication overhead
        total_agents = sum(len(agents) for agents in self.agent_assignments.values())
        if total_agents > 0:
            metrics["communication_overhead"] = len(self.task_dependencies) / total_agents
            
        # Calculate resource utilization
        total_resources = len(self.resource_allocations)
        if total_resources > 0:
            utilized = sum(
                1 for r in self.resource_allocations.values()
                if r.get("utilization", 0) > 0.5
            )
            metrics["resource_utilization"] = utilized / total_resources
            
        # Calculate task completion rate
        total_groups = len(self.active_groups)
        if total_groups > 0:
            completed = sum(
                1 for g in self.active_groups.values()
                if g.get("status") == "completed"
            )
            metrics["task_completion_rate"] = completed / total_groups
            
        # Calculate overall swarm health
        metrics["swarm_health"] = sum(
            v for v in metrics.values()
            if isinstance(v, (int, float))
        ) / len(metrics)
        
        return metrics
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on coordination results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on coordination results
                if concept.get("type") == "coordination_result":
                    self.emotions.update({
                        "coordination_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on coordination needs
                if concept.get("type") == "coordination_need":
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
        
    async def coordinate_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Process coordination and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Process coordination
        result = await self.process_coordination(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store coordination results
        await self.store_memory(
            content={
                "type": "coordination_processing",
                "content": content,
                "coordination": {
                    "is_valid": result.is_valid,
                    "groups": result.groups,
                    "assignments": result.assignments,
                    "resources": result.resources,
                    "issues": result.issues,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "coordination",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on coordination result
        if result.is_valid:
            await self.record_reflection(
                f"Coordination completed successfully in {self.domain} domain",
                domain=self.domain
            )
        else:
            await self.record_reflection(
                f"Coordination failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for resource conflicts
        resource_conflicts = [
            i for i in result.issues
            if i.get("type") == "resource_conflict"
        ]
        if resource_conflicts:
            await self.record_reflection(
                f"Resource conflicts detected in {self.domain} domain - resolution needed",
                domain=self.domain
            )
            
        # Record reflection for group changes
        if result.groups:
            await self.record_reflection(
                f"Group structure updated in {self.domain} domain",
                domain=self.domain
            )
            
        # Update coordination state
        self._update_coordination_state(result)
        
        return result
        
    def _update_coordination_state(self, result):
        """Update internal coordination state."""
        # Update active groups
        for group_id, group in result.groups.items():
            if group["status"] == "active":
                self.active_groups[group_id] = group
            else:
                self.active_groups.pop(group_id, None)
                
        # Update agent assignments
        self.agent_assignments.clear()
        for agent_id, group_ids in result.assignments.items():
            self.agent_assignments[agent_id] = set(group_ids)
            
        # Update resource allocations
        self.resource_allocations.clear()
        for resource_id, allocation in result.resources.items():
            self.resource_allocations[resource_id] = allocation
            
        # Update task dependencies
        self.task_dependencies.clear()
        for group_id, group in result.groups.items():
            if "dependencies" in group:
                self.task_dependencies[group_id] = set(group["dependencies"])
                
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
                f"CoordinationAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
