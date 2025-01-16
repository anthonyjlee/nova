"""Meta agent implementation."""

from typing import Dict, List, Optional, Any
from datetime import datetime

from ..base import BaseAgent
from ..tiny_person import TinyPerson
from ..tinytroupe_agent import TinyTroupeAgent, TinyFactory
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import Memory, EpisodicMemory, AgentResponse

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
        
    async def spawn_agent(
        self,
        agent_type: str,
        domain: str,
        capabilities: List[str],
        supervisor_id: Optional[str] = None,
        attributes: Optional[Dict] = None
    ) -> str:
        """Spawn a new agent through TinyFactory.
        
        Args:
            agent_type: Type of agent to spawn
            domain: Operating domain for agent
            capabilities: List of agent capabilities
            supervisor_id: Optional ID of supervising agent
            attributes: Optional additional attributes
            
        Returns:
            str: ID of spawned agent
            
        Raises:
            ValueError: If agent configuration is invalid
        """
        # Validate capabilities against predefined skills
        invalid_capabilities = [cap for cap in capabilities if cap not in self.PREDEFINED_SKILLS]
        if invalid_capabilities:
            raise ValueError(f"Invalid capabilities: {invalid_capabilities}")
            
        # Create agent config
        agent_config = {
            "name": f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "agent_type": agent_type,
            "domain": domain,
            "skills": capabilities,
            "knowledge_vertical": attributes.get("knowledge_vertical") if attributes else None
        }
        
        # Validate agent configuration
        validate_agent_config(agent_config)
        
        # Get agent prompt
        prompt = get_agent_prompt(
            agent_type=agent_type,
            domain=domain,
            skills=capabilities
        )
        
        # Store spawn request in memory
        await self.store_memory(
            content=f"Spawning {agent_type} agent for domain {domain}",
            importance=0.8,
            context={
                "type": "agent_spawn",
                "agent_type": agent_type,
                "domain": domain,
                "capabilities": capabilities,
                "config": agent_config
            }
        )
        
        # Spawn agent through factory with validated config and prompt
        agent_id = self.factory.create_agent(
            agent_type=agent_type,
            domain=domain,
            capabilities=capabilities,
            supervisor_id=supervisor_id,
            attributes={
                **(attributes or {}),
                "config": agent_config,
                "prompt": prompt
            }
        )
        
        # Store spawn result
        await self.store_memory(
            content=f"Spawned agent {agent_id} of type {agent_type}",
            importance=0.8,
            context={
                "type": "agent_spawn",
                "agent_id": agent_id,
                "agent_type": agent_type,
                "domain": domain
            }
        )
        
        return agent_id
        
    async def create_team(
        self,
        team_type: str,
        domain: str,
        capabilities: List[str],
        team_size: int = 3
    ) -> Dict[str, str]:
        """Create a team of agents for a specific purpose.
        
        Args:
            team_type: Type of team to create
            domain: Operating domain for team
            capabilities: Required team capabilities
            team_size: Number of agents in team
            
        Returns:
            Dict mapping role names to agent IDs
        """
        team_id = f"team_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create supervisor agent
        supervisor_id = await self.spawn_agent(
            agent_type="supervisor",
            domain=domain,
            capabilities=["team_coordination"] + capabilities,
            attributes={
                "team_id": team_id,
                "team_type": team_type
            }
        )
        
        # Create worker agents
        worker_ids = []
        for i in range(team_size - 1):
            worker_id = await self.spawn_agent(
                agent_type="worker",
                domain=domain,
                capabilities=capabilities,
                supervisor_id=supervisor_id,
                attributes={
                    "team_id": team_id,
                    "worker_number": i + 1
                }
            )
            worker_ids.append(worker_id)
            
        # Create swarm pattern config
        pattern_config = {
            "tasks": [
                {
                    "id": "supervision",
                    "agent_id": supervisor_id,
                    "type": "supervisor",
                    "capabilities": ["team_coordination"] + capabilities
                }
            ],
            "dependencies": []
        }
        
        # Add worker tasks and dependencies
        for i, worker_id in enumerate(worker_ids):
            worker_task = {
                "id": f"worker_{i+1}",
                "agent_id": worker_id,
                "type": "worker",
                "capabilities": capabilities
            }
            pattern_config["tasks"].append(worker_task)
            
            # Add dependency on supervisor
            pattern_config["dependencies"].append({
                "from": "supervision",
                "to": f"worker_{i+1}",
                "type": "supervises"
            })
            
        # Register pattern with SwarmRegistry
        registry_agent = await self.spawn_agent(
            agent_type="swarm_registry",
            domain="swarm_management",
            capabilities=["pattern_management"],
            attributes={"role": "registry"}
        )
        
        pattern_result = await self.world.execute_action(
            self,
            "register_pattern",
            agent_id=registry_agent,
            pattern_type=team_type,
            config=pattern_config,
            metadata={
                "domain": domain,
                "team_id": team_id,
                "created_at": datetime.now().isoformat()
            }
        )
        
        if pattern_result and pattern_result.get("registration_status") == "success":
            # Store team info with pattern ID
            team_info = {
                "id": team_id,
                "type": team_type,
                "domain": domain,
                "supervisor": supervisor_id,
                "workers": worker_ids,
                "capabilities": capabilities,
                "pattern_id": pattern_result["pattern_id"],
                "created_at": datetime.now().isoformat()
            }
            
            self._active_teams[team_id] = team_info
            
            await self.store_memory(
                content=f"Created team {team_id} of type {team_type}",
                importance=0.8,
                context={
                    "type": "team_creation",
                    "team_info": team_info
                }
            )
        
        return {
            "supervisor": supervisor_id,
            "workers": worker_ids
        }
        
    async def process_interaction(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process an interaction through the cognitive architecture.
        
        Args:
            content: Interaction content
            metadata: Optional interaction metadata
            
        Returns:
            AgentResponse containing processing results
        """
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
                
            schema_result = await self.world.execute_action(
                self,
                "validate_schema",
                agent_id=schema_agent,
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
                    "validation": schema_result.dict()
                }
            )
        
            # Analyze cognitive needs with validation context
            cognitive_needs = await self._analyze_cognitive_needs(
                content,
                {
                    **(metadata or {}),
                    "validation_result": schema_result.dict()
                }
            )
        
            # Spawn/coordinate agents with validation awareness
            for need in cognitive_needs:
                if need["type"] == "team":
                    # Create validation-aware team
                    team = await self.create_team(
                        team_type=need["team_type"],
                        domain=need["domain"],
                        capabilities=[*need["capabilities"], "schema_validation"],
                        metadata={
                            "validation_result": schema_result.dict(),
                            "debug_flags": debug_flags
                        }
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
                            "validation_result": schema_result.dict(),
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
                    "validation_result": schema_result.dict(),
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
                    "validation": schema_result.dict()
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
                    "validation": schema_result.dict() if 'schema_result' in locals() else None
                }
            )
            
            raise
        
    async def _analyze_cognitive_needs(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict]
    ) -> List[Dict]:
        """Analyze cognitive needs for processing content.
        
        Args:
            content: Content to analyze
            metadata: Optional metadata
            
        Returns:
            List of cognitive needs (teams/agents to create)
        """
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
        """Process content through cognitive architecture.
        
        Args:
            content: Content to process
            metadata: Optional metadata
            
        Returns:
            AgentResponse with processing results
        """
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

    # Import required skills and validation
    from ...config.agent_config import (
        PREDEFINED_SKILLS,
        validate_agent_config,
        get_agent_prompt,
        validate_domain_config
    )

    # Task states with validation rules
    TASK_STATES = {
        "pending": {
            "transitions": ["in_progress", "blocked"],
            "validation": lambda task: True  # Any task can start
        },
        "in_progress": {
            "transitions": ["completed", "blocked", "paused_for_human"],
            "validation": lambda task: task.get("assignee") is not None  # Must have assignee
        },
        "blocked": {
            "transitions": ["in_progress"],
            "validation": lambda task: len(task.get("blocked_by", [])) > 0  # Must have blockers
        },
        "paused_for_human": {
            "transitions": ["in_progress", "blocked"],
            "validation": lambda task: task.get("requires_human", False)  # Must need human input
        },
        "completed": {
            "transitions": [],  # Terminal state
            "validation": lambda task: all(subtask.get("completed", False) 
                                        for subtask in task.get("sub_tasks", []))  # All subtasks done
        }
    }

    async def validate_task_transition(
        self,
        task: Dict[str, Any],
        new_state: str
    ) -> bool:
        """Validate if a task can transition to a new state.
        
        Args:
            task: Task to validate
            new_state: Desired new state
            
        Returns:
            bool indicating if transition is valid
        """
        current_state = task.get("status", "pending")
        
        # Check if transition is allowed
        if new_state not in self.TASK_STATES[current_state]["transitions"]:
            return False
            
        # Check if validation rule passes
        return self.TASK_STATES[new_state]["validation"](task)

    async def detect_and_handle_task(
        self,
        content: Dict[str, Any],
        thread_id: str
    ) -> Optional[str]:
        """Detect and handle potential task in conversation.
        
        Args:
            content: Conversation content
            thread_id: Thread ID where task was detected
            
        Returns:
            Optional task ID if task was created
        """
        # Store detection attempt
        await self.store_memory(
            content=f"Analyzing content for tasks in thread {thread_id}",
            importance=0.7,
            context={
                "type": "task_detection",
                "thread_id": thread_id
            }
        )

        # Create task agent for detection
        task_agent = await self.spawn_agent(
            agent_type="task",
            domain="professional",
            capabilities=["task_analysis", "dependency_tracking", "domain_validation"],
            attributes={
                "thread_id": thread_id,
                "role": "task_detection"
            }
        )
        
        # Analyze task using TaskAgent
        task_result = await self.world.execute_action(
            self,
            "analyze_and_store",
            agent_id=task_agent,
            content=content
        )
        
        if not task_result or not task_result.get("tasks"):
            return None
            
        # Extract task info from analysis
        task_info = {
            "title": task_result["tasks"][0].get("title", content.get("title", "Untitled Task")),
            "description": task_result["tasks"][0].get("description", str(content.get("content", ""))),
            "confidence": task_result.get("confidence", 0.7),
            "patterns": task_result.get("patterns", []),
            "metadata": {
                "dependencies": task_result.get("dependencies", {}),
                "domain": task_result.get("domain", "professional")
            }
        }
        
        # Create task via API
        task_response = await self.world.execute_action(
            self,
            "create_task",
            task={
                "title": task_info["title"],
                "description": task_info["description"],
                "type": "task",
                "status": "pending",
                "thread_id": thread_id,
                "metadata": {
                    "source": "conversation",
                    "detected_at": datetime.now().isoformat(),
                    "confidence": task_info["confidence"],
                    "patterns": task_info["patterns"],
                    "dependencies": task_info["metadata"]["dependencies"],
                    "domain": task_info["metadata"]["domain"]
                }
            }
        )
        
        if task_response and "task_id" in task_response:
            # Create thread manager for task team
            thread_manager = await self.spawn_agent(
                agent_type="thread_management",
                domain=task_info["metadata"]["domain"],
                capabilities=["thread_management"],
                attributes={"role": "thread_manager"}
            )
            
            # Create team thread with proper synchronization
            thread_id = str(uuid.uuid4())
            thread_data = await self.world.execute_action(
                self,
                "create_thread",
                agent_id=thread_manager,
                thread_id=thread_id,
                task_id=task_response["task_id"],
                domain=task_info["metadata"]["domain"],
                metadata={
                    "type": "task-team",
                    "title": f"Task: {task_info['title']}",
                    "source_thread": thread_id,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if thread_data:
                # Add required agents to thread
                await self._add_task_team_agents(
                    thread_id=thread_id,
                    task_id=task_response["task_id"]
                )
                
                # Post initial thread message
                await self.world.execute_action(
                    self,
                    "post_message",
                    agent_id=thread_manager,
                    thread_id=thread_id,
                    message_id=str(uuid.uuid4()),
                    content=f"Task team thread created for: {task_info['title']}",
                    metadata={
                        "type": "system",
                        "task_id": task_response["task_id"]
                    }
                )
                
            return task_response["task_id"]
            
        return None

    def _combine_task_analyses(
        self,
        analyses: List[Dict[str, Any]],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine analyses from multiple agents into task info.
        
        Args:
            analyses: List of agent analyses
            content: Original content for context
            
        Returns:
            Combined task information
        """
        # Initialize with defaults
        combined = {
            "title": content.get("title", "Untitled Task"),
            "description": str(content.get("content", "")),
            "confidence": 0.0,
            "patterns": [],
            "metadata": {}
        }
        
        # Track votes and confidences
        pattern_votes = {}
        total_confidence = 0.0
        
        # Combine all analyses
        for analysis in analyses:
            # Update confidence (weighted average)
            confidence = analysis.get("confidence", 0.5)
            total_confidence += confidence
            
            # Collect patterns with voting
            for pattern in analysis.get("patterns", []):
                pattern_votes[pattern] = pattern_votes.get(pattern, 0) + confidence
                
            # Take title/description from highest confidence analysis
            if confidence > combined.get("confidence", 0.0):
                if "title" in analysis:
                    combined["title"] = analysis["title"]
                if "description" in analysis:
                    combined["description"] = analysis["description"]
                combined["confidence"] = confidence
                
            # Merge metadata
            if "metadata" in analysis:
                combined["metadata"].update(analysis["metadata"])
                
        # Average confidence across all analyses
        if analyses:
            combined["confidence"] = total_confidence / len(analyses)
            
        # Include patterns that have strong consensus (>50% weighted votes)
        total_votes = sum(pattern_votes.values())
        if total_votes > 0:
            combined["patterns"] = [
                pattern for pattern, votes in pattern_votes.items()
                if votes / total_votes > 0.5
            ]
            
        return combined
        
        
    async def _analyze_task_requirements(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze task to determine required capabilities.
        
        Args:
            task: Task description and requirements
            
        Returns:
            Dict containing required capabilities and constraints
        """
        # Extract task type and complexity
        task_type = task.get("type", "general")
        complexity = self._assess_complexity(task)
        
        # Determine required capabilities
        capabilities = ["base"]
        if complexity > 0.8:
            capabilities.extend(["analysis", "research", "synthesis"])
        elif complexity > 0.5:
            capabilities.extend(["analysis", "synthesis"])
            
        # Add task-specific capabilities
        if "research" in task_type.lower():
            capabilities.append("research")
        if "analysis" in task_type.lower():
            capabilities.append("analysis")
            
        return {
            "type": task_type,
            "complexity": complexity,
            "capabilities": list(set(capabilities)),
            "constraints": task.get("constraints", {})
        }
        
    def _determine_team_composition(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine optimal team composition for requirements.
        
        Args:
            requirements: Task requirements and constraints
            
        Returns:
            Dict specifying team composition
        """
        # Base team size on complexity
        complexity = requirements["complexity"]
        if complexity > 0.8:
            team_size = 5  # Large team for complex tasks
        elif complexity > 0.5:
            team_size = 3  # Medium team for moderate tasks
        else:
            team_size = 2  # Small team for simple tasks
            
        return {
            "type": requirements["type"],
            "size": team_size,
            "capabilities": requirements["capabilities"]
        }

    async def _add_task_team_agents(
        self,
        thread_id: str,
        task_id: str
    ) -> None:
        """Add required agents to a task team thread.
        
        Args:
            thread_id: Thread ID for task team
            task_id: Associated task ID
        """
        # Core task team agents
        required_agents = [
            {
                "type": "orchestration",
                "capabilities": ["task_management", "team_coordination"]
            },
            {
                "type": "analysis",
                "capabilities": ["task_analysis", "requirement_analysis"]
            },
            {
                "type": "research",
                "capabilities": ["information_gathering", "context_analysis"]
            },
            {
                "type": "validation",
                "capabilities": ["quality_control", "requirement_validation"]
            }
        ]
        
        # Add each required agent to thread
        for agent_spec in required_agents:
            await self.world.execute_action(
                self,
                "add_thread_agent",
                thread_id=thread_id,
                agent_type=agent_spec["type"],
                capabilities=agent_spec["capabilities"],
                metadata={
                    "task_id": task_id,
                    "role": agent_spec["type"]
                }
            )
            
        # Store team creation in memory
        await self.store_memory(
            content=f"Added task team agents to thread {thread_id} for task {task_id}",
            importance=0.8,
            context={
                "type": "team_creation",
                "thread_id": thread_id,
                "task_id": task_id,
            "agents": required_agents
        }
    )

    async def handle_task_transition(
        self,
        task_id: str,
        new_state: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Handle task state transition.
        
        Args:
            task_id: ID of task to transition
            new_state: New task state
            metadata: Optional transition metadata
        """
        # Validate state transition via API
        transition_response = await self.world.execute_action(
            self,
            "transition_task",
            task_id=task_id,
            new_state=new_state,
            metadata=metadata
        )
        
        if transition_response and transition_response.get("success"):
            # Get task team thread
            task_info = await self.world.execute_action(
                self,
                "get_task",
                task_id=task_id
            )
            
            if task_info and "thread_id" in task_info:
                # Notify team of transition
                await self.world.execute_action(
                    self,
                    "send_thread_message",
                    thread_id=task_info["thread_id"],
                    content={
                        "type": "task_transition",
                        "task_id": task_id,
                        "from_state": task_info.get("status"),
                        "to_state": new_state,
                        "metadata": metadata
                    }
                )
                
            # Store transition in memory
            await self.store_memory(
                content=f"Task {task_id} transitioned to {new_state}",
                importance=0.8,
                context={
                    "type": "task_transition",
                    "task_id": task_id,
                    "from_state": task_info.get("status") if task_info else None,
                    "to_state": new_state,
                    "metadata": metadata
                }
            )
            
            # Update task tracking
            if task_id in self._active_tasks:
                self._active_tasks[task_id]["status"] = new_state
                self._active_tasks[task_id]["updated_at"] = datetime.now().isoformat()

    async def create_task_group(
        self,
        title: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Create a new task group.
        
        Args:
            title: Group title
            description: Optional group description
            metadata: Optional group metadata
            
        Returns:
            Optional group ID if created
        """
        # Create group via API
        group_response = await self.world.execute_action(
            self,
            "create_task_group",
            task={
                "title": title,
                "description": description,
                "type": "group",
                "status": "active",
                "metadata": metadata or {}
            }
        )
        
        if group_response and "task_id" in group_response:
            # Store group creation
            await self.store_memory(
                content=f"Created task group: {title}",
                importance=0.8,
                context={
                    "type": "group_creation",
                    "group_id": group_response["task_id"],
                    "title": title,
                    "metadata": metadata
                }
            )
            
            return group_response["task_id"]
            
        return None
        
    async def add_task_to_group(
        self,
        task_id: str,
        group_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Add a task to a group.
        
        Args:
            task_id: Task to add
            group_id: Group to add to
            metadata: Optional relationship metadata
            
        Returns:
            bool indicating success
        """
        # Add task to group via API
        response = await self.world.execute_action(
            self,
            "add_group_task",
            group_id=group_id,
            task_id=task_id,
            metadata=metadata
        )
        
        if response and response.get("success"):
            # Store group addition
            await self.store_memory(
                content=f"Added task {task_id} to group {group_id}",
                importance=0.7,
                context={
                    "type": "group_update",
                    "group_id": group_id,
                    "task_id": task_id,
                    "metadata": metadata
                }
            )
            
            # Update task tracking
            if task_id in self._active_tasks:
                self._active_tasks[task_id]["group_id"] = group_id
                self._active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
                
            return True
            
        return False

    async def add_task_comment(
        self,
        task_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Add a comment to a task.
        
        Args:
            task_id: Task to comment on
            content: Comment content
            metadata: Optional comment metadata
            
        Returns:
            Optional comment ID if created
        """
        # Add comment via API
        comment_response = await self.world.execute_action(
            self,
            "add_task_comment",
            task_id=task_id,
            comment={
                "content": content,
                "author": self.name,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
        )
        
        if comment_response and "comment_id" in comment_response:
            # Get task team thread
            task_info = await self.world.execute_action(
                self,
                "get_task",
                task_id=task_id
            )
            
            if task_info and "thread_id" in task_info:
                # Notify team of comment
                await self.world.execute_action(
                    self,
                    "send_thread_message",
                    thread_id=task_info["thread_id"],
                    content={
                        "type": "task_comment",
                        "task_id": task_id,
                        "comment_id": comment_response["comment_id"],
                        "content": content,
                        "author": self.name,
                        "metadata": metadata
                    }
                )
                
            # Store comment in memory
            await self.store_memory(
                content=f"Added comment to task {task_id}: {content}",
                importance=0.7,
                context={
                    "type": "task_comment",
                    "task_id": task_id,
                    "comment_id": comment_response["comment_id"],
                    "content": content,
                    "metadata": metadata
                }
            )
            
            return comment_response["comment_id"]
            
        return None

    async def get_task_comments(
        self,
        task_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get comments for a task.
        
        Args:
            task_id: Task to get comments for
            limit: Optional limit on number of comments
            
        Returns:
            List of comment objects
        """
        # Get comments via API
        comments_response = await self.world.execute_action(
            self,
            "get_task_comments",
            task_id=task_id,
            limit=limit
        )
        
        if comments_response and "comments" in comments_response:
            return comments_response["comments"]
            
        return []
