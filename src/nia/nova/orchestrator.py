"""Nova orchestrator implementation using TinyTroupe."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .core.meta import MetaAgent, MetaResult
from ..world.environment import NIAWorld
from ..memory.two_layer import TwoLayerMemorySystem
from ..memory.types.memory_types import Memory, EpisodicMemory, TaskOutput, MemoryType
from ..agents.base import BaseAgent

logger = logging.getLogger(__name__)

class Nova(MetaAgent):
    """Nova orchestrator for coordinating agents."""
    
    def __init__(
        self,
        name: str = "Nova",
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        llm: Optional['LLMInterface'] = None
    ):
        """Initialize Nova orchestrator."""
        self.name = name  # Set name first
        self.memory_system = memory_system  # Store memory system
        
        # Initialize MetaAgent with memory system components
        super().__init__(
            llm=llm,
            store=memory_system.semantic.driver if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            agents={}  # Will be populated as agents are spawned
        )
        
        self.world = world or NIAWorld(memory_system=memory_system)
        self._initialize_tinytroupe_attributes()
        
        # Register with world if name is unique
        if self.world:
            existing_names = [agent.name for agent in self.world.agents] if hasattr(self.world, 'agents') else []
            if self.name not in existing_names:
                self.world.add_agent(self)
            else:
                # Generate unique name by appending number
                i = 1
                while f"{self.name}_{i}" in existing_names:
                    i += 1
                self.name = f"{self.name}_{i}"
                self.world.add_agent(self)
            
    def _initialize_tinytroupe_attributes(self):
        """Initialize TinyTroupe-specific attributes."""
        self.occupation = "Meta Orchestrator"
        self.desires = [
            "Coordinate agents effectively",
            "Maintain system coherence",
            "Enable emergent behavior",
            "Preserve conversation during tasks"
        ]
        self.emotions = {
            "baseline": "focused",
            "towards_agents": "supportive"
        }
        
    async def recall_memories(
        self,
        query: Dict,
        limit: int = 10
    ) -> List[Memory]:
        """Recall memories from the memory system."""
        if self.memory_system:
            return await self.memory_system.query_memories(query, limit=limit)
        return []

    async def store_memory(
        self,
        content: Any,
        importance: float = 0.7,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        """Store memory in the memory system."""
        if self.memory_system:
            await self.memory_system.episodic.store_memory(
                EpisodicMemory(
                    content=str(content) if not isinstance(content, str) else content,
                    type=MemoryType.EPISODIC,
                    timestamp=datetime.now().isoformat(),
                    importance=importance,
                    context=context or {},
                    metadata=metadata or {}
                )
            )

    async def spawn_agent(
        self,
        agent_type: str,
        name: Optional[str] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None,
        debug_flags: Optional[Dict] = None
    ) -> BaseAgent:
        """Spawn a new agent with validation and monitoring."""
        try:
            # Start monitoring
            monitor_task = None
            if debug_flags and debug_flags.get("monitor_agents"):
                monitor_task = await self.world.execute_action(
                    self,
                    "start_monitoring",
                    agent_id=name or f"{agent_type}_{len(self.world.agents)}",
                    metadata={
                        "type": "agent_spawn",
                        "agent_type": agent_type,
                        "domain": domain,
                        "debug_flags": debug_flags
                    }
                )

            # Validate agent configuration
            schema_result = await self.world.execute_action(
                self,
                "validate_schema",
                content={
                    "type": agent_type,
                    "name": name,
                    "attributes": attributes,
                    "domain": domain
                },
                schema_type="agent_config",
                metadata={"debug_flags": debug_flags}
            )

            if not schema_result.is_valid:
                if debug_flags and debug_flags.get("strict_mode"):
                    raise ValueError(f"Agent configuration validation failed: {schema_result.issues}")
                await self.world.execute_action(
                    self,
                    "send_alert",
                    type="validation_warning",
                    message=f"Agent configuration validation warning: {schema_result.issues}",
                    severity="medium"
                )

            # Generate name if not provided
            if name is None:
                name = f"{agent_type}_{len(self.world.agents)}"

            # Create agent with validation context
            agent = BaseAgent(
                name=name,
                memory_system=self.memory_system,
                world=self.world,
                attributes={
                    **(attributes or {}),
                    "validation_result": schema_result.dict() if hasattr(schema_result, "dict") else None,
                    "debug_flags": debug_flags
                }
            )

            # Register with world
            self.world.add_agent(agent)

            # Register domain if provided
            if domain:
                self.world.register_domain(domain, [agent.name])

            # Log agent creation with validation context
            await self.store_memory(
                content={
                    "type": "agent_creation",
                    "agent": name,
                    "agent_type": agent_type,
                    "domain": domain,
                    "validation": schema_result.dict() if hasattr(schema_result, "dict") else None,
                    "monitor_task": monitor_task
                },
                importance=0.7,
                context={"type": "system"}
            )

            if debug_flags and debug_flags.get("log_validation"):
                await self.world.execute_action(
                    self,
                    "log_debug",
                    message=f"Agent {name} created with validation result: {schema_result.dict() if hasattr(schema_result, 'dict') else None}"
                )

            return agent

        except Exception as e:
            error_msg = f"Error spawning agent: {str(e)}"
            logger.error(error_msg)

            if debug_flags and debug_flags.get("log_validation"):
                await self.world.execute_action(
                    self,
                    "log_debug",
                    message=error_msg,
                    level="error"
                )

            # Send alert for spawn failure
            await self.world.execute_action(
                self,
                "send_alert",
                type="agent_spawn_error",
                message=error_msg,
                severity="high"
            )

            raise
        
    async def handle_conversation(
        self,
        message: str,
        source: Optional[str] = None,
        target: Optional[str] = None,
        debug_flags: Optional[Dict] = None
    ) -> Dict:
        """Handle conversation between agents with validation and monitoring."""
        try:
            # Start monitoring
            monitor_task = None
            if debug_flags and debug_flags.get("monitor_conversations"):
                monitor_task = await self.world.execute_action(
                    self,
                    "start_monitoring",
                    task_type="conversation",
                    metadata={
                        "message": message,
                        "source": source,
                        "target": target,
                        "debug_flags": debug_flags
                    }
                )

            # Validate conversation schema
            schema_result = await self.world.execute_action(
                self,
                "validate_schema",
                content={
                    "message": message,
                    "source": source,
                    "target": target
                },
                schema_type="conversation",
                metadata={"debug_flags": debug_flags}
            )

            if not schema_result.is_valid:
                if debug_flags and debug_flags.get("strict_mode"):
                    raise ValueError(f"Conversation validation failed: {schema_result.issues}")
                await self.world.execute_action(
                    self,
                    "send_alert",
                    type="validation_warning",
                    message=f"Conversation validation warning: {schema_result.issues}",
                    severity="medium"
                )

            # Process through MetaAgent with validation context
            result = await self.process_interaction(
                message,
                metadata={
                    "validation_result": schema_result.dict() if hasattr(schema_result, "dict") else None,
                    "debug_flags": debug_flags,
                    "monitor_task": monitor_task
                }
            )

            # Then handle through world if needed
            if target:
                await self.world.execute_action(
                    self,
                    "converse",
                    message=result.response,
                    target=target,
                    metadata={
                        "validation_result": schema_result.dict() if hasattr(schema_result, "dict") else None,
                        "debug_flags": debug_flags
                    }
                )

            # Stop monitoring
            if monitor_task:
                await self.world.execute_action(
                    self,
                    "stop_monitoring",
                    task_id=monitor_task["id"],
                    metadata={
                        "success": True,
                        "response": result.dict() if hasattr(result, "dict") else str(result)
                    }
                )

            return {
                "type": "conversation",
                "message": result.response,
                "source": source or self.name,
                "target": target,
                "result": result,
                "validation": schema_result.dict() if hasattr(schema_result, "dict") else None,
                "monitor_task": monitor_task
            }

        except Exception as e:
            error_msg = f"Error handling conversation: {str(e)}"
            logger.error(error_msg)

            if debug_flags and debug_flags.get("log_validation"):
                await self.world.execute_action(
                    self,
                    "log_debug",
                    message=error_msg,
                    level="error"
                )

            # Send alert for conversation failure
            await self.world.execute_action(
                self,
                "send_alert",
                type="conversation_error",
                message=error_msg,
                severity="high"
            )

            raise
        
    async def start_task(
        self,
        task: Dict,
        domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Start a new task with validation."""
        try:
            # Get debug flags
            debug_flags = metadata.get("debug_flags", {}) if metadata else {}
            
            # Validate task schema
            validation_agent = await self.spawn_agent(
                agent_type="validation",
                name="task_validator",
                attributes={"role": "validator"}
            )
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content="Starting task validation",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            validation_result = await self.world.execute_action(
                validation_agent,
                "validate_and_store",
                content=task,
                validation_type="task",
                target_domain=domain
            )
            
            if not validation_result.is_valid:
                if debug_flags.get("strict_mode"):
                    raise ValueError(f"Task validation failed: {validation_result.issues}")
                else:
                    await self.store_memory(
                        content=f"Task validation warning: {validation_result.issues}",
                        importance=0.9,
                        context={"type": "validation_warning"}
                    )
                    
            task_id = str(hash(f"{task}_{datetime.now().isoformat()}"))
            
            # Store task in memory with validation context
            await self.store_memory(
                content={
                    "type": "task_start",
                    "task_id": task_id,
                    "task": task,
                    "domain": domain,
                    "validation": validation_result.dict() if hasattr(validation_result, "dict") else None,
                    "debug_flags": debug_flags
                },
                importance=0.8,
                context={"type": "task"}
            )
        
            # Get or create domain agents with validation awareness
            agents = []
            if domain:
                existing_agents = self.world.get_domain_agents(domain)
                if existing_agents:
                    agents = [self.world.get_agent(name) for name in existing_agents]
                else:
                    # Spawn new agent for domain with validation capabilities
                    agent = await self.spawn_agent(
                        agent_type="TaskAgent",
                        domain=domain,
                        attributes={
                            "task_id": task_id,
                            "task": task,
                            "validation_result": validation_result.dict() if hasattr(validation_result, "dict") else None,
                            "debug_flags": debug_flags
                        }
                    )
                    agents = [agent]
                
            # Assign task to agents with validation context
            for agent in agents:
                await self.world.execute_action(
                    agent,
                    "process_task",
                    task_id=task_id,
                    task=task,
                    metadata={
                        "validation_result": validation_result.dict() if hasattr(validation_result, "dict") else None,
                        "debug_flags": debug_flags
                    }
                )
                
            return task_id
            
        except Exception as e:
            error_msg = f"Error starting task: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
            raise
        
    async def pause_tasks(self):
        """Pause task execution while maintaining conversations."""
        await self.world.pause_tasks()
        
    async def resume_tasks(self):
        """Resume task execution."""
        await self.world.resume_tasks()
        
    async def detect_emergent_tasks(self, conversation: str) -> List[Dict]:
        """Detect potential emergent tasks from conversation."""
        # Get recent context
        recent_memories = await self.recall_memories(
            query={"time_range": {"minutes": 30}},
            limit=10
        )
        
        # Look for task indicators
        tasks = []
        indicators = ["need to", "should", "must", "let's", "we could"]
        
        for indicator in indicators:
            if indicator in conversation.lower():
                # Extract task details
                task = {
                    "type": "emergent",
                    "source": "conversation",
                    "description": conversation,
                    "context": [m.content for m in recent_memories],
                    "importance": 0.7
                }
                tasks.append(task)
                
                # Store potential task
                await self.store_memory(
                    content={
                        "type": "emergent_task",
                        "task": task
                    },
                    importance=0.7,
                    context={"type": "task_detection"}
                )
                
        return tasks
        
    async def get_task_status(
        self,
        task_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Get status of a task with validation."""
        try:
            # Get debug flags
            debug_flags = metadata.get("debug_flags", {}) if metadata else {}
            
            # Query task memories with validation context
            memories = await self.recall_memories(
                query={
                    "filter": {
                        "content.task_id": task_id
                    }
                }
            )
            
            if not memories:
                return {"status": "unknown"}
                
            # Analyze task progression with validation
            latest = max(memories, key=lambda m: m.timestamp)
            
            # Get validation patterns
            validation_patterns = self._extract_validation_patterns(memories)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=f"Task validation patterns: {validation_patterns}",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            status = self._determine_task_status(latest)
            
            # Record validation-specific reflections
            if validation_patterns:
                recurring_patterns = [p for p in validation_patterns if p.get("frequency", 0) > 2]
                if recurring_patterns:
                    await self.store_memory(
                        content=f"Recurring validation patterns in task {task_id}: {recurring_patterns}",
                        importance=0.8,
                        context={"type": "validation_pattern"}
                    )
                    
                critical_patterns = [p for p in validation_patterns if p.get("severity") == "high"]
                if critical_patterns:
                    await self.store_memory(
                        content=f"Critical validation patterns in task {task_id}: {critical_patterns}",
                        importance=0.9,
                        context={"type": "validation_pattern"}
                    )
            
            return {
                "status": status,
                "last_update": latest.timestamp,
                "memories": len(memories),
                "validation_patterns": validation_patterns,
                "validation_status": self._determine_validation_status(validation_patterns)
            }
            
        except Exception as e:
            error_msg = f"Error getting task status: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
            raise
        
    def _determine_task_status(self, memory: Memory) -> str:
        """Determine task status from memory with validation awareness."""
        content = memory.content
        if isinstance(content, dict):
            # Check validation status
            validation_result = content.get("validation", {})
            if validation_result and not validation_result.get("is_valid", True):
                return "validation_error"
                
            # Check task status
            if content.get("type") == "task_complete":
                # Only mark as completed if validation passed
                if validation_result and validation_result.get("is_valid", True):
                    return "completed"
                return "completed_with_warnings"
            elif content.get("type") == "task_error":
                return "error"
            elif content.get("type") == "task_start":
                return "in_progress"
        return "unknown"
        
    def _extract_validation_patterns(self, memories: List[Memory]) -> List[Dict[str, Any]]:
        """Extract validation patterns from task memories."""
        patterns = []
        issue_counts = {}
        
        for memory in memories:
            content = memory.content
            if isinstance(content, dict):
                validation = content.get("validation", {})
                if validation and isinstance(validation, dict):
                    for issue in validation.get("issues", []):
                        if isinstance(issue, dict):
                            key = f"{issue.get('type')}:{issue.get('description')}"
                            if key in issue_counts:
                                issue_counts[key]["frequency"] += 1
                            else:
                                issue_counts[key] = {
                                    "type": issue.get("type"),
                                    "description": issue.get("description"),
                                    "severity": issue.get("severity", "low"),
                                    "frequency": 1
                                }
                                
        # Convert counts to patterns
        for pattern in issue_counts.values():
            if pattern["frequency"] > 1:  # Only include recurring patterns
                patterns.append(pattern)
                
        return patterns
        
    def _determine_validation_status(self, patterns: List[Dict[str, Any]]) -> str:
        """Determine overall validation status from patterns."""
        if not patterns:
            return "valid"
            
        # Check for critical patterns
        critical_patterns = [p for p in patterns if p.get("severity") == "high"]
        if critical_patterns:
            return "critical_issues"
            
        # Check for recurring patterns
        recurring_patterns = [p for p in patterns if p.get("frequency", 0) > 2]
        if recurring_patterns:
            return "recurring_issues"
            
        return "minor_issues"
