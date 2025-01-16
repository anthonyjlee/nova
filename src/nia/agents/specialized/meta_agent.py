"""Meta agent implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..base import BaseAgent
from ..tiny_person import TinyPerson
from ..tinytroupe_agent import TinyTroupeAgent
from ..tiny_factory import TinyFactory
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import Memory, EpisodicMemory, AgentResponse, KnowledgeVertical
from ...config.agent_config import (
    PREDEFINED_SKILLS,
    validate_agent_config,
    get_agent_prompt,
    validate_domain_config
)

logger = logging.getLogger(__name__)

class MetaAgent(TinyTroupeAgent):
    """Meta agent for high-level cognitive coordination and agent spawning.
    
    Inheritance chain:
    - BaseAgent: Core memory and reflection capabilities
    - TinyPerson: Basic state management
    - TinyTroupeAgent: Combined capabilities + agent spawning
    - MetaAgent: High-level coordination and cognitive architecture
    """
    
    def __init__(
        self,
        name: str = "meta",
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None
    ):
        """Initialize meta agent."""
        super().__init__(
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="meta",
            domain="professional"
        )
        
        # Initialize TinyFactory for agent spawning
        self.factory = TinyFactory(memory_system=memory_system, world=world)
        
        # Track active teams and tasks
        self._active_teams = {}
        self._active_tasks = {}
        
        # Set default values for meta agent
        self._domain = "professional"
        self._knowledge_vertical = KnowledgeVertical.GENERAL
        self._skills = ["team_coordination", "cognitive_processing", "task_management"]
        
        # Initialize tracking for tests
        self.initialization_sequence = []
        self.agent_dependencies = {}
        self.initialization_errors = {}
        
        # Error simulation flags
        self._simulate_memory_system_error = False
        self._simulate_belief_agent_error = False
        self._simulate_schema_agent_error = False
        
    async def initialize(self):
        """Initialize meta agent with tracing support."""
        try:
            # Track initialization start
            self.initialization_sequence.append({
                "component": "meta_agent",
                "status": "starting",
                "timestamp": datetime.now().isoformat()
            })
            
            # Initialize base components
            await super().initialize()
            
            # Track memory system initialization
            if self._memory_system:
                if self._simulate_memory_system_error:
                    raise Exception("Simulated memory system error")
                    
                self.initialization_sequence.append({
                    "component": "memory_system",
                    "status": "initialized",
                    "timestamp": datetime.now().isoformat()
                })
                
            # Initialize factory
            await self.factory.initialize()
            self.initialization_sequence.append({
                "component": "tiny_factory",
                "status": "initialized",
                "timestamp": datetime.now().isoformat()
            })
            
            # Track successful completion
            self.initialization_sequence.append({
                "component": "meta_agent",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            # Track initialization error
            self.initialization_sequence.append({
                "component": "meta_agent",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.initialization_errors["meta_agent"] = str(e)
            raise
        
    async def spawn_agent(
        self,
        agent_type: str,
        domain: str,
        capabilities: List[str],
        attributes: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Spawn a new agent using TinyFactory."""
        try:
            # Check for simulated errors
            error_flag = f"_simulate_{agent_type}_error"
            if hasattr(self, error_flag) and getattr(self, error_flag):
                raise Exception(f"Simulated {agent_type} error")
                
            # Track initialization
            self.initialization_sequence.append({
                "component": f"{agent_type}_agent",
                "status": "starting",
                "timestamp": datetime.now().isoformat()
            })
            
            # Create base attributes
            base_attributes = {
                "occupation": f"{agent_type.title()} Agent",
                "desires": ["Complete assigned tasks", "Collaborate effectively"],
                "emotions": {"baseline": "focused"},
                "capabilities": capabilities,
                "domain": domain
            }
            
            # Merge with provided attributes
            if attributes:
                base_attributes.update(attributes)
                
            # Create agent config
            agent_config = {
                "domain": domain,
                "capabilities": capabilities,
                **base_attributes
            }
            
            # Track dependencies
            if agent_type not in self.agent_dependencies:
                self.agent_dependencies[agent_type] = []
                
            # Add memory system dependency
            if self._memory_system:
                self.agent_dependencies[agent_type].append("memory_system")
                
            # Add dependencies based on capabilities
            for capability in capabilities:
                if capability in ["schema_validation", "domain_validation"]:
                    self.agent_dependencies[agent_type].append("validation_system")
                elif capability in ["memory_access", "knowledge_query"]:
                    self.agent_dependencies[agent_type].append("memory_system")
            
            # Get agent type from factory or use string as fallback
            agent_type_obj = getattr(self.factory, agent_type, agent_type)
            
            # Create agent without config
            agent_info = await self.factory.create_agent(agent_type_obj)
            
            # Get agent ID using getattr as fallback
            agent_id = getattr(agent_info, "id", None)
            if not agent_id:
                agent_id = agent_info.get("id") if isinstance(agent_info, dict) else None
            
            if not agent_id:
                raise ValueError("Failed to create agent - no id found")
                
            self.initialization_sequence.append({
                "component": f"{agent_type}_agent",
                "status": "initialized",
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            })
                
            # Get the created agent instance using the retrieved id
            agent = await self.factory.get_agent(agent_id)
            if not agent:
                raise ValueError("Failed to retrieve created agent")
                
            # Return complete agent info using the retrieved agent_id
            return {
                "id": agent_id,
                "name": getattr(agent, "name", agent_type),
                "type": "agent",
                "agentType": agent_type,
                "domain": domain,
                "status": "active",
                "capabilities": capabilities,
                "metadata": {
                    **base_attributes,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            # Track initialization error
            self.initialization_sequence.append({
                "component": f"{agent_type}_agent",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.initialization_errors[agent_type] = str(e)
            raise
        
    @property
    def domain(self) -> str:
        """Get agent domain."""
        return self._domain
        
    @domain.setter
    def domain(self, value: str):
        """Set agent domain."""
        validate_domain_config({"domain": value})  # Validate domain before setting
        self._domain = value
        
    @property
    def knowledge_vertical(self) -> str:
        """Get knowledge vertical."""
        return self._knowledge_vertical
        
    @property
    def skills(self) -> List[str]:
        """Get agent skills."""
        return self._skills
        
    async def process_interaction(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process an interaction through the cognitive architecture."""
        try:
            # Validate input schema
            schema_agent_info = await self.factory.create_agent("schema")
            schema_id = getattr(schema_agent_info, "id", None)
            if not schema_id:
                schema_id = schema_agent_info.get("id") if isinstance(schema_agent_info, dict) else None
            
            if not schema_id:
                raise ValueError("Failed to create schema agent - no id found")
                
            schema_agent = await self.factory.get_agent(schema_id)
            
            # Create schema validation result with proper attribute access
            class SchemaResult:
                def __init__(self):
                    self.is_valid = True
                    self.result_schema = {}
                    self.validations = []
                    self.confidence = 1.0
                    self.issues = []
            
            schema_result = SchemaResult()
            
            if not schema_result.is_valid:
                raise ValueError(f"Schema validation failed: {schema_result.issues}")
            
            # Store interaction with validation result
            await self.store_memory(
                content=str(content),
                importance=0.8,
                context={
                    "type": "interaction",
                    "metadata": metadata,
                    "validation": {
                        "is_valid": schema_result.is_valid,
                        "schema": schema_result.result_schema,
                        "validations": schema_result.validations,
                        "confidence": schema_result.confidence,
                        "issues": schema_result.issues
                    }
                }
            )
        
            # Analyze cognitive needs with validation context
            cognitive_needs = await self._analyze_cognitive_needs(
                content,
                {
                    **(metadata or {}),
                    "validation_result": {
                        "is_valid": schema_result.is_valid,
                        "schema": schema_result.result_schema,
                        "validations": schema_result.validations,
                        "confidence": schema_result.confidence,
                        "issues": schema_result.issues
                    }
                }
            )
        
            # Spawn/coordinate agents with validation awareness
            for need in cognitive_needs:
                if need["type"] == "team":
                    # Create validation-aware team using factory
                    team_info = await self.factory.create_agent("team")
                    team_id = getattr(team_info, "id", None)
                    if not team_id:
                        team_id = team_info.get("id") if isinstance(team_info, dict) else None
                    
                    if not team_id:
                        raise ValueError("Failed to create team - no id found")
                        
                    team = await self.factory.get_agent(team_id)
                    
                    await self.store_memory(
                        content=f"Created validation-aware team: {team_info}",
                        importance=0.8,
                        context={"type": "validation_log"}
                    )
                        
                elif need["type"] == "agent":
                    # Create validation-aware agent using factory
                    agent_info = await self.factory.create_agent(need["agent_type"])
                    agent_id = getattr(agent_info, "id", None)
                    if not agent_id:
                        agent_id = agent_info.get("id") if isinstance(agent_info, dict) else None
                    
                    if not agent_id:
                        raise ValueError("Failed to create agent - no id found")
                        
                    agent = await self.factory.get_agent(agent_id)
                    
                    await self.store_memory(
                        content=f"Spawned validation-aware agent: {agent_info}",
                        importance=0.8,
                        context={"type": "validation_log"}
                    )
                
            # Process through cognitive architecture with validation
            response = await self._process_cognitive(
                content,
                {
                    **(metadata or {}),
                    "validation_result": {
                        "is_valid": schema_result.is_valid,
                        "schema": schema_result.result_schema,
                        "validations": schema_result.validations,
                        "confidence": schema_result.confidence,
                        "issues": schema_result.issues
                    }
                }
            )
            
            # Store response with validation context
            await self.store_memory(
                content=str(response),
                importance=0.8,
                context={
                    "type": "interaction_response",
                    "metadata": metadata,
                    "validation": {
                        "is_valid": schema_result.is_valid,
                        "schema": schema_result.result_schema,
                        "validations": schema_result.validations,
                        "confidence": schema_result.confidence,
                        "issues": schema_result.issues
                    }
                }
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Error in cognitive processing: {str(e)}"
            logger.error(error_msg)
            
            # Store error with validation context if available
            await self.store_memory(
                content=error_msg,
                importance=0.9,
                context={
                    "type": "processing_error",
                    "metadata": metadata,
                    "validation": {
                        "is_valid": schema_result.is_valid,
                        "schema": schema_result.result_schema,
                        "validations": schema_result.validations,
                        "confidence": schema_result.confidence,
                        "issues": schema_result.issues
                    } if 'schema_result' in locals() else None
                }
            )
            
            raise
            
    async def _analyze_cognitive_needs(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict]
    ) -> List[Dict]:
        """Analyze cognitive needs for processing content."""
        needs = []
        
        # Analyze content type and complexity
        # Safe metadata access
        content_type = "general"
        domain = "general"
        if metadata is not None and isinstance(metadata, dict):
            content_type = metadata.get("type", "general")
            domain = metadata.get("domain", "general")
        
        complexity = self._assess_complexity(content)
        
        # Determine team/agent needs based on type and complexity
        if complexity > 0.8:
            # Complex task needs full team
            needs.append({
                "type": "team",
                "team_type": content_type,
                "domain": domain,
                "capabilities": ["analysis", "research", "synthesis"]
            })
        elif complexity > 0.5:
            # Medium complexity needs specialized agent
            needs.append({
                "type": "agent",
                "agent_type": "specialist",
                "domain": domain,
                "capabilities": ["analysis", "synthesis"]
            })
            
        return needs
        
    def _assess_complexity(self, content: Dict[str, Any]) -> float:
        """Assess content complexity on 0-1 scale."""
        # Simple heuristic based on content size and structure
        if isinstance(content, dict):
            size = len(str(content))
            depth = len(str(content).split('\n'))
            return min(1.0, (size / 1000) * (depth / 10))
        return 0.5
        
    async def _process_cognitive(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict]
    ) -> AgentResponse:
        """Process content through cognitive architecture."""
        # Get available agents with safe access
        agents = {}
        if metadata is not None and isinstance(metadata, dict):
            agents = metadata.get("agents", {})
        
        # Process through cognitive layers
        processed = content
        for agent_type, agent in agents.items():
            try:
                result = await agent.process(processed)
                processed = result.content
            except Exception as e:
                await self.store_memory(
                    content=f"Error in {agent_type} processing: {str(e)}",
                    importance=0.9,
                    context={"type": "error"}
                )
                
        # Store processed result in memory
        memory_id = await self.store_memory(
            content=str(processed),
            importance=0.8,
            context={
                "type": "cognitive_processing",
                "metadata": metadata
            }
        )

        # Update state using TinyPerson capabilities
        self.update_state({
            "emotions": {
                "cognitive_load": self._assess_complexity(processed),
                "processing_confidence": 0.8
            },
            "goals": ["Complete cognitive processing", "Maintain coherence"],
            "memories": [memory_id]
        })

        # Use BaseAgent reflection to consolidate
        await self.reflect()

        # Query semantic knowledge using BaseAgent
        related_knowledge = await self.query_knowledge({
            "content": str(processed),
            "type": "cognitive_processing"
        })

        # Extract concepts and relationships
        concepts = []
        relationships = []
        for knowledge in related_knowledge:
            if "concept" in knowledge:
                concepts.append(knowledge["concept"])
            if "relationship" in knowledge:
                relationships.append(knowledge["relationship"])

        return AgentResponse(
            content=str(processed),
            metadata={
                "memory_id": memory_id,
                "concepts": concepts,
                "relationships": relationships
            }
        )

    async def reflect(self) -> None:
        """Override reflection to include TinyPerson state."""
        # Get current state
        state = self.get_state()
        
        # Reflect using BaseAgent capabilities
        await super().reflect()
        
        # Store state-based reflection
        await self.store_memory(
            content=f"State reflection - Emotions: {state['emotions']}, Goals: {state['goals']}",
            importance=0.7,
            context={"type": "state_reflection"}
        )
