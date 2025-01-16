"""TinyTroupe orchestration agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.orchestration import OrchestrationAgent as NovaOrchestrationAgent
from ...nova.core.analytics import AnalyticsAgent, AnalyticsResult
from ...nova.core.validation import ValidationResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

from .task_management import TaskManagement

class OrchestrationAgent(NovaOrchestrationAgent, TinyTroupeAgent, TaskManagement):
    """Orchestration agent with TinyTroupe, memory, and task management capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize orchestration agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
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
            agent_type="orchestration"
        )
        
        # Initialize TinyTroupe capabilities after memory system is ready
        if memory_system and hasattr(memory_system, 'semantic'):
            self.learn_concept = memory_system.semantic.store_concept
        else:
            self.learn_concept = None
        
        # Initialize analytics agent
        self.analytics = AnalyticsAgent(domain=self.domain)
        
        # Initialize orchestration-specific attributes
        self._initialize_orchestration_attributes()
        
        # Initialize task flow tracking
        self.active_flows = {}  # flow_id -> flow_state
        self.flow_patterns = {}  # pattern_id -> pattern_config
        self.execution_monitors = {}  # task_id -> monitor_state
        self.resource_allocations = {}  # resource_id -> allocation_state
        self.dependency_graph = {}  # task_id -> dependencies
        self.swarm_validations = {}  # swarm_id -> validation_state
        
    def _initialize_orchestration_attributes(self):
        """Initialize orchestration-specific attributes."""
        attributes = {
            "occupation": "Advanced Agent Orchestrator",
            "desires": [
                "Coordinate agents effectively",
                "Optimize agent interactions",
                "Ensure task completion",
                "Maintain orchestration quality",
                "Optimize task flows",
                "Manage resource allocation",
                "Monitor execution progress",
                "Handle dependencies efficiently",
                "Adapt to changing conditions",
                "Ensure system resilience",
                "Validate swarm configurations",
                "Track validation patterns"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_agents": "focused",
                "towards_domain": "mindful",
                "towards_flows": "attentive",
                "towards_resources": "efficient",
                "towards_execution": "vigilant",
                "towards_adaptation": "responsive",
                "towards_validation": "precise"
            },
            "capabilities": [
                "agent_orchestration",
                "flow_coordination",
                "decision_making",
                "pattern_orchestration",
                "flow_optimization",
                "resource_management",
                "execution_monitoring",
                "dependency_handling",
                "adaptive_planning",
                "resilience_management",
                "swarm_validation",
                "pattern_validation"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced flow and validation awareness."""
        try:
            # Get debug flags
            debug_flags = metadata.get("debug_flags", {}) if metadata else {}
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Validate swarm configuration if present
            if swarm_config := content.get("swarm_config"):
                if debug_flags.get("log_validation"):
                    await self.store_memory(
                        content="Starting swarm configuration validation",
                        importance=0.8,
                        context={"type": "validation_log"}
                    )
                    
                validation_result = await self._validate_swarm_config(
                    swarm_config,
                    debug_flags
                )
                
                if not validation_result.is_valid:
                    if debug_flags.get("strict_mode"):
                        raise ValueError(f"Swarm validation failed: {validation_result.issues}")
                    else:
                        await self.store_memory(
                            content=f"Swarm validation warning: {validation_result.issues}",
                            importance=0.9,
                            context={"type": "validation_warning"}
                        )
                        
                metadata["validation_result"] = validation_result.dict() if hasattr(validation_result, "dict") else None
            
            # Update flow tracking with analytics and validation
            if flow_id := content.get("flow_id"):
                await self._update_flow_state(flow_id, content, debug_flags)
                
                # Get flow analytics with validation context
                analytics_result = await self._get_flow_analytics(
                    flow_id,
                    metadata={"validation_result": metadata.get("validation_result")}
                )
                
                # Update flow state based on analytics and validation
                if analytics_result and analytics_result.is_valid:
                    await self._apply_analytics_insights(
                        flow_id,
                        analytics_result,
                        debug_flags
                    )
                    
            # Process through memory system
            response = await super().process(content, metadata)
            
            # Update validation patterns
            if validation_result := metadata.get("validation_result"):
                await self._update_validation_patterns(validation_result, debug_flags)
                
            return response
            
        except Exception as e:
            error_msg = f"Error in orchestration processing: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
            raise
            
    async def _validate_swarm_config(
        self,
        swarm_config: Dict[str, Any],
        debug_flags: Dict[str, bool]
    ) -> ValidationResult:
        """Validate swarm configuration."""
        try:
            # Validate swarm structure
            structure_issues = []
            if not isinstance(swarm_config.get("agents"), list):
                structure_issues.append({
                    "type": "structure",
                    "severity": "high",
                    "description": "Swarm must have an agents list"
                })
                
            if not isinstance(swarm_config.get("patterns"), dict):
                structure_issues.append({
                    "type": "structure",
                    "severity": "high",
                    "description": "Swarm must have patterns configuration"
                })
                
            # Validate agent configurations
            agent_issues = []
            for agent in swarm_config.get("agents", []):
                if not isinstance(agent.get("capabilities"), list):
                    agent_issues.append({
                        "type": "agent_config",
                        "severity": "medium",
                        "description": f"Agent {agent.get('name')} missing capabilities"
                    })
                    
                if not agent.get("role"):
                    agent_issues.append({
                        "type": "agent_config",
                        "severity": "medium",
                        "description": f"Agent {agent.get('name')} missing role"
                    })
                    
            # Validate pattern configurations
            pattern_issues = []
            for pattern_id, pattern in swarm_config.get("patterns", {}).items():
                if not isinstance(pattern.get("conditions"), dict):
                    pattern_issues.append({
                        "type": "pattern_config",
                        "severity": "medium",
                        "description": f"Pattern {pattern_id} missing conditions"
                    })
                    
                if not isinstance(pattern.get("actions"), list):
                    pattern_issues.append({
                        "type": "pattern_config",
                        "severity": "medium",
                        "description": f"Pattern {pattern_id} missing actions"
                    })
                    
            # Combine all issues
            all_issues = structure_issues + agent_issues + pattern_issues
            
            # Store validation result
            swarm_id = swarm_config.get("id", str(hash(str(swarm_config))))
            self.swarm_validations[swarm_id] = {
                "timestamp": datetime.now().isoformat(),
                "is_valid": len(all_issues) == 0,
                "issues": all_issues,
                "debug_flags": debug_flags
            }
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=f"Swarm validation result for {swarm_id}: {len(all_issues)} issues",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            return ValidationResult(
                is_valid=len(all_issues) == 0,
                issues=all_issues,
                metadata={
                    "swarm_id": swarm_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            error_msg = f"Error validating swarm config: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
            return ValidationResult(
                is_valid=False,
                issues=[{
                    "type": "validation_error",
                    "severity": "high",
                    "description": str(e)
                }],
                metadata={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    async def _update_validation_patterns(
        self,
        validation_result: Dict[str, Any],
        debug_flags: Dict[str, bool]
    ):
        """Update validation patterns based on validation results."""
        try:
            # Extract patterns from validation issues
            patterns = []
            for issue in validation_result.get("issues", []):
                pattern = {
                    "type": issue.get("type"),
                    "severity": issue.get("severity", "low"),
                    "description": issue.get("description"),
                    "frequency": 1,
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat()
                }
                
                # Check if pattern exists
                existing = next(
                    (p for p in patterns if 
                     p["type"] == pattern["type"] and
                     p["description"] == pattern["description"]),
                    None
                )
                
                if existing:
                    existing["frequency"] += 1
                    existing["last_seen"] = pattern["last_seen"]
                else:
                    patterns.append(pattern)
                    
            # Store patterns
            if patterns:
                await self.store_memory(
                    content={
                        "type": "validation_patterns",
                        "patterns": patterns,
                        "timestamp": datetime.now().isoformat()
                    },
                    importance=0.8,
                    context={"type": "validation_tracking"}
                )
                
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=f"Updated validation patterns: {len(patterns)} patterns",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            # Record reflections for significant patterns
            recurring_patterns = [p for p in patterns if p["frequency"] > 2]
            if recurring_patterns:
                await self.record_reflection(
                    f"Recurring validation patterns detected: {recurring_patterns}",
                    domain=self.domain
                )
                
            critical_patterns = [p for p in patterns if p["severity"] == "high"]
            if critical_patterns:
                await self.record_reflection(
                    f"Critical validation patterns detected: {critical_patterns}",
                    domain=self.domain
                )
                
        except Exception as e:
            error_msg = f"Error updating validation patterns: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )

    async def _update_flow_state(
        self,
        flow_id: str,
        content: Dict[str, Any],
        debug_flags: Dict[str, bool]
    ):
        """Update flow state tracking with analytics and validation integration."""
        try:
            if flow_id not in self.active_flows:
                self.active_flows[flow_id] = {
                    "status": "active",
                    "start_time": datetime.now().isoformat(),
                    "steps_completed": 0,
                    "current_phase": "initialization",
                    "metrics": {},
                    "needs_attention": False,
                    "analytics": {
                        "last_update": None,
                        "performance": {},
                        "predictions": {},
                        "optimizations": []
                    },
                    "validation": {
                        "last_check": None,
                        "issues": [],
                        "patterns": [],
                        "status": "pending"
                    }
                }
                
                if debug_flags.get("log_validation"):
                    await self.store_memory(
                        content=f"Initialized flow {flow_id} with validation tracking",
                        importance=0.8,
                        context={"type": "validation_log"}
                    )
                    
            flow_state = self.active_flows[flow_id]
            
            # Update basic state
            if status := content.get("flow_status"):
                flow_state["status"] = status
                
            if phase := content.get("flow_phase"):
                flow_state["current_phase"] = phase
                
            # Update metrics
            if metrics := content.get("flow_metrics", {}):
                flow_state["metrics"].update(metrics)
                
            # Update completion tracking
            if content.get("step_completed"):
                flow_state["steps_completed"] += 1
                
            # Check for attention needs
            flow_state["needs_attention"] = any([
                content.get("needs_attention", False),
                content.get("has_blockers", False),
                content.get("resource_constraints", False)
            ])
            
            # Update validation state
            if validation_result := content.get("validation_result"):
                flow_state["validation"] = {
                    "last_check": datetime.now().isoformat(),
                    "issues": validation_result.get("issues", []),
                    "patterns": validation_result.get("patterns", []),
                    "status": "valid" if validation_result.get("is_valid") else "invalid"
                }
                
            # Apply relevant flow patterns
            for pattern_id, pattern in self.flow_patterns.items():
                if self._matches_pattern(content, pattern):
                    await self._apply_flow_pattern(flow_id, pattern_id, pattern)
                    
        except Exception as e:
            error_msg = f"Error updating flow state: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
    async def _apply_analytics_insights(
        self,
        flow_id: str,
        analytics: AnalyticsResult,
        debug_flags: Dict[str, bool]
    ):
        """Apply analytics insights to flow state with validation awareness."""
        try:
            flow_state = self.active_flows.get(flow_id)
            if not flow_state:
                return
                
            # Update analytics state
            flow_state["analytics"] = {
                "last_update": datetime.now().isoformat(),
                "performance": analytics.analytics.get("analytics", {}),
                "predictions": {},
                "optimizations": []
            }
            
            # Apply insights with validation awareness
            for insight in analytics.insights:
                if insight.get("type") == "performance":
                    flow_state["analytics"]["performance"].update(
                        insight.get("metrics", {})
                    )
                elif insight.get("type") == "prediction":
                    flow_state["analytics"]["predictions"][
                        insight.get("metric", "unknown")
                    ] = insight.get("value", 0.0)
                elif insight.get("type") == "optimization":
                    flow_state["analytics"]["optimizations"].append({
                        "type": insight.get("optimization_type"),
                        "description": insight.get("description"),
                        "confidence": insight.get("confidence", 0.0),
                        "validation_status": "pending"
                    })
                elif insight.get("type") == "validation":
                    flow_state["validation"]["patterns"].append({
                        "type": insight.get("pattern_type"),
                        "description": insight.get("description"),
                        "severity": insight.get("severity", "low"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
            # Update attention needs based on analytics and validation
            needs_attention = analytics.confidence < 0.5
            if flow_state["validation"]["status"] == "invalid":
                needs_attention = True
                
            if needs_attention:
                flow_state["needs_attention"] = True
                await self.record_reflection(
                    f"Flow {flow_id} needs attention due to analytics/validation issues",
                    domain=self.domain
                )
                
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=f"Applied analytics insights to flow {flow_id} with validation",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
        except Exception as e:
            error_msg = f"Error applying analytics insights: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )

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
                f"OrchestrationAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
