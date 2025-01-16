"""Meta agent implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..base import BaseAgent
from ..tiny_person import TinyPerson
from ..tinytroupe_agent import TinyTroupeAgent, TinyFactory
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
        # Create config for meta agent
        config = {
            "name": name,
            "agent_type": "meta",
            "domain": "professional",
            "knowledge_vertical": KnowledgeVertical.GENERAL,
            "skills": ["team_coordination", "cognitive_processing", "task_management"]
        }
        
        super().__init__(
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            config=config
        )
        
        # Initialize TinyFactory for agent spawning
        self.factory = TinyFactory(memory_system=memory_system, world=world)
        
        # Track active teams and tasks
        self._active_teams = {}
        self._active_tasks = {}
        
        # Store domain from config
        self._domain = config["domain"]
        
    async def spawn_agent(
        self,
        agent_type: str,
        domain: str,
        capabilities: List[str],
        attributes: Optional[Dict] = None
    ) -> str:
        """Spawn a new agent using TinyFactory."""
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
        
        # Create agent
        agent = await self.factory.create_agent(
            agent_type=agent_type,
            config=agent_config
        )
        
        return agent.id
        
    @property
    def domain(self) -> str:
        """Get agent domain."""
        return self._domain
        
    @domain.setter
    def domain(self, value: str):
        """Set agent domain."""
        self._domain = value
        
    async def process_interaction(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process an interaction through the cognitive architecture."""
        try:
            # Get debug flags
            debug_flags = metadata.get("debug_flags", {}) if metadata else {}
            
            # Validate input schema
            schema_agent = await self.spawn_agent(
                agent_type="schema",
                domain=self.domain,
                capabilities=["schema_validation"],
                attributes={"role": "validator"}
            )
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content="Starting schema validation",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            # Get schema agent instance
            schema_agent_instance = self.factory.get_agent(schema_agent)
            if not schema_agent_instance:
                raise ValueError(f"Failed to get schema agent {schema_agent}")
                
            # Analyze schema using SchemaAgent's analyze_schema method
            schema_result = await schema_agent_instance.analyze_schema(
                content=content,
                schema_type="interaction",
                metadata=metadata
            )
            
            if not schema_result.is_valid:
                if debug_flags.get("strict_mode"):
                    raise ValueError(f"Schema validation failed: {schema_result.issues}")
                else:
                    await self.store_memory(
                        content=f"Schema validation warning: {schema_result.issues}",
                        importance=0.9,
                        context={"type": "validation_warning"}
                    )
            
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
                    # Create validation-aware team
                    team = await self.create_team(
                        team_type=need["team_type"],
                        domain=need["domain"],
                        capabilities=[*need["capabilities"], "schema_validation"]
                    )
                    
                    if debug_flags.get("log_validation"):
                        await self.store_memory(
                            content=f"Created validation-aware team: {team}",
                            importance=0.8,
                            context={"type": "validation_log"}
                        )
                        
                elif need["type"] == "agent":
                    # Spawn validation-aware agent
                    agent = await self.spawn_agent(
                        agent_type=need["agent_type"],
                        domain=need["domain"],
                        capabilities=[*need["capabilities"], "schema_validation"],
                        attributes={
                            "validation_result": {
                                "is_valid": schema_result.is_valid,
                                "schema": schema_result.result_schema,
                                "validations": schema_result.validations,
                                "confidence": schema_result.confidence,
                                "issues": schema_result.issues
                            },
                            "debug_flags": debug_flags
                        }
                    )
                    
                    if debug_flags.get("log_validation"):
                        await self.store_memory(
                            content=f"Spawned validation-aware agent: {agent}",
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
                    },
                    "debug_flags": debug_flags
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
        content_type = metadata.get("type") if metadata else "general"
        complexity = self._assess_complexity(content)
        
        # Determine team/agent needs based on type and complexity
        if complexity > 0.8:
            # Complex task needs full team
            needs.append({
                "type": "team",
                "team_type": content_type,
                "domain": metadata.get("domain", "general"),
                "capabilities": ["analysis", "research", "synthesis"]
            })
        elif complexity > 0.5:
            # Medium complexity needs specialized agent
            needs.append({
                "type": "agent",
                "agent_type": "specialist",
                "domain": metadata.get("domain", "general"),
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
        # Get available agents
        agents = metadata.get("agents", {}) if metadata else {}
        
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
            content=processed,
            memory_id=memory_id,
            concepts=concepts,
            relationships=relationships
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
