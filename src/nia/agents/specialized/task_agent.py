"""TinyTroupe task agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.task import TaskAgent as NovaTaskAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class TaskAgent(NovaTaskAgent, TinyTroupeAgent):
    """Task agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize task agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaTaskAgent first
        NovaTaskAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain
        )
        
        # Initialize task-specific attributes
        base_attributes = self._initialize_task_attributes()
        
        # Merge with provided attributes if any
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, dict) and key in base_attributes and isinstance(base_attributes[key], dict):
                    base_attributes[key].update(value)
                else:
                    base_attributes[key] = value
        
        # Initialize TinyTroupeAgent with merged attributes
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=base_attributes,
            agent_type="task"  # Using task agent type
        )
        
        # Ensure emotions and desires are properly initialized in configuration
        self._configuration["current_emotions"] = base_attributes.get("emotions", {})
        self._configuration["current_goals"] = base_attributes.get("desires", [])
        
    def _initialize_task_attributes(self) -> Dict[str, Any]:
        """Initialize task-specific attributes."""
        return {
            "occupation": "Task Analyst",
            "desires": [
                "Understand task requirements",
                "Track task dependencies",
                "Ensure task completion",
                "Maintain domain boundaries"
            ],
            "emotions": {
                "baseline": "focused",
                "towards_analysis": "systematic",
                "towards_domain": "mindful",
                "analysis_state": "neutral",  # Added default state
                "domain_state": "neutral"  # Added default state
            },
            "capabilities": [
                "task_analysis",
                "dependency_tracking",
                "domain_validation",
                "priority_assessment"
            ]
        }
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        try:
            # Process through memory system
            raw_response = await self.llm.analyze(content, metadata=metadata)
            
            # Convert raw response to structured response
            response = raw_response if isinstance(raw_response, AgentResponse) else AgentResponse(
                content=str(raw_response),
                metadata={"domain": self.domain}
            )
            
            # Update TinyTroupe state based on task analysis
            if isinstance(raw_response, dict):
                # Update emotions based on task states
                if "emotions" in raw_response:
                    self.emotions.update(raw_response["emotions"])
                    
                # Update desires based on task needs
                if "desires" in raw_response:
                    current_desires = list(self.desires)
                    for desire in raw_response["desires"]:
                        if isinstance(desire, str):
                            if not any(desire in d for d in current_desires):
                                current_desires.append(desire)
                        elif isinstance(desire, dict):
                            if "description" in desire:
                                description = desire["description"]
                                if not any(description in d for d in current_desires):
                                    current_desires.append(f"Address {description}")
                    self.desires = current_desires
                
                # Process concepts if present
                if "concepts" in raw_response:
                    for concept in raw_response["concepts"]:
                        if not isinstance(concept, dict):
                            continue
                            
                        # Update emotions based on task results
                        if concept.get("type") == "task":
                            self.emotions["analysis_state"] = concept.get("description", "neutral")
                            
                        # Update desires based on task needs
                        if concept.get("type") == "task_need":
                            need = concept.get("name", "unknown need")
                            if not any(need in desire for desire in self.desires):
                                self.desires.append(f"Address {need}")
                                
                        # Update emotions based on domain relevance
                        if "domain_relevance" in concept:
                            try:
                                relevance = float(concept["domain_relevance"])
                                if relevance > 0.8:
                                    self.emotions["domain_state"] = "highly_relevant"
                                elif relevance < 0.3:
                                    self.emotions["domain_state"] = "low_relevance"
                            except (ValueError, TypeError):
                                pass
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process: {str(e)}")
            return AgentResponse(
                content="Error processing content",
                metadata={"error": str(e), "domain": self.domain}
            )
        
    async def analyze_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Analyze tasks and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze tasks
        result = await self.analyze_tasks(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store task analysis
        await self.store_memory(
            content={
                "type": "task_analysis",
                "content": content,
                "analysis": {
                    "tasks": result.tasks,
                    "confidence": result.confidence,
                    "dependencies": result.dependencies,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "task",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence task analysis achieved in {target_domain or self.domain} domain",
                domain=target_domain or self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence task analysis - may need additional dependencies in {target_domain or self.domain} domain",
                domain=target_domain or self.domain
            )
            
        # Record reflection for blockers
        if result.dependencies.get("blockers", []):
            await self.record_reflection(
                f"Task blockers identified in {target_domain or self.domain} domain - resolution required",
                domain=target_domain or self.domain
            )
        
        return result
        
    @property
    def memory_system(self):
        """Get memory system."""
        return self._memory_system

    @property
    def emotions(self) -> Dict[str, str]:
        """Get agent emotions."""
        return self._configuration.get("current_emotions", {})
        
    @emotions.setter
    def emotions(self, value: Dict[str, str]):
        """Set agent emotions."""
        if not isinstance(value, dict):
            value = {}
        self._configuration["current_emotions"] = value
        
    def update_emotions(self, updates: Dict[str, str]):
        """Update emotions dictionary."""
        current = dict(self.emotions)
        current.update(updates)
        self.emotions = current
        
    @property
    def desires(self) -> List[str]:
        """Get agent desires."""
        return self._configuration.get("current_goals", [])
        
    @desires.setter
    def desires(self, value: List[str]):
        """Set agent desires."""
        if not isinstance(value, list):
            value = []
        self._configuration["current_goals"] = value

    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                return await self._memory_system.semantic.store.get_domain_access(
                    self.name,
                    domain
                )
            except Exception:
                return False
        return False
        
    async def validate_domain_access(self, domain: str):
        """Validate access to a domain before processing."""
        has_access = await self.get_domain_access(domain)
        if not has_access:
            raise PermissionError(
                f"TaskAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                await self._memory_system.semantic.store.record_reflection(
                    content=content,
                    domain=domain or self.domain
                )
            except Exception as e:
                logger.error(f"Error recording reflection: {str(e)}")
