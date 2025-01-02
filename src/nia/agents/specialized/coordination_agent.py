t"""TinyTroupe coordination agent implementation."""

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
            capabilities=[
                "group_management",
                "resource_allocation",
                "dependency_tracking",
                "conflict_resolution",
                "performance_monitoring",
                "domain_coordination",
                "state_management"
            ]
        )
        
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
