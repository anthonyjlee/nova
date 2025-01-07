"""Swarm metrics agent implementation."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from ...nova.core.orchestration import OrchestrationAgent as NovaOrchestrationAgent
from ...nova.core.analytics import AnalyticsAgent, AnalyticsResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse
from ...swarm.pattern_store import SwarmPatternStore
from ...swarm.graph_integration import SwarmGraphIntegration

logger = logging.getLogger(__name__)

class SwarmMetricsAgent(NovaOrchestrationAgent, TinyTroupeAgent):
    """Tracks swarm performance metrics."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize metrics agent."""
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
            agent_type="metrics"
        )
        
        # Initialize metrics-specific components
        self.pattern_store = SwarmPatternStore()
        self.graph_integration = SwarmGraphIntegration(self.pattern_store)
        
        # Initialize metrics tracking
        self.performance_metrics = {}  # pattern_id -> metrics
        self.resource_metrics = {}  # resource_id -> metrics
        self.execution_metrics = {}  # execution_id -> metrics
        
        # Initialize metrics-specific attributes
        self._initialize_metrics_attributes()
        
    def _initialize_metrics_attributes(self):
        """Initialize metrics-specific attributes."""
        attributes = {
            "occupation": "Swarm Performance Analyst",
            "desires": [
                "Track performance metrics",
                "Analyze execution patterns",
                "Monitor resource utilization",
                "Detect performance issues",
                "Generate performance insights",
                "Optimize execution flows",
                "Predict resource needs",
                "Identify bottlenecks",
                "Measure pattern efficiency",
                "Provide optimization recommendations"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_metrics": "precise",
                "towards_analysis": "focused",
                "towards_monitoring": "vigilant",
                "towards_optimization": "determined",
                "towards_prediction": "insightful",
                "towards_recommendations": "helpful"
            },
            "capabilities": [
                "metrics_collection",
                "performance_analysis",
                "resource_monitoring",
                "pattern_analysis",
                "execution_tracking",
                "bottleneck_detection",
                "efficiency_measurement",
                "trend_analysis",
                "predictive_analytics",
                "optimization_recommendations"
            ]
        }
        self.define(**attributes)
    
    async def collect_metrics(
        self,
        pattern_id: str,
        time_window: Optional[int] = None  # hours
    ) -> Dict[str, Any]:
        """Collect swarm performance data."""
        try:
            # Build time filter
            time_filter = ""
            parameters = {"pattern_id": pattern_id}
            
            if time_window:
                cutoff = (datetime.now() - timedelta(hours=time_window)).isoformat()
                time_filter = "AND e.created_at >= $cutoff"
                parameters["cutoff"] = cutoff
            
            # Get execution metrics
            query = f"""
            MATCH (p:SwarmPattern {{id: $pattern_id}})-[:HAS_EXECUTION]->(e:PatternExecution)
            WHERE e.status IN ['completed', 'failed']
            {time_filter}
            RETURN e
            ORDER BY e.created_at DESC
            """
            
            result = await self.pattern_store.driver.execute_query(
                query,
                parameters=parameters
            )
            
            if not result:
                return {
                    "pattern_id": pattern_id,
                    "time_window": time_window,
                    "executions": 0,
                    "metrics": {}
                }
            
            # Analyze executions
            executions = []
            aggregated_metrics = {
                "success_rate": [],
                "execution_time": [],
                "task_metrics": {},
                "resource_metrics": {}
            }
            
            for record in result:
                execution = dict(record[0])
                executions.append(execution)
                
                # Calculate success rate
                aggregated_metrics["success_rate"].append(
                    1.0 if execution["status"] == "completed" else 0.0
                )
                
                # Calculate execution time
                start_time = datetime.fromisoformat(execution["created_at"])
                end_time = datetime.fromisoformat(execution["completed_at"])
                duration = (end_time - start_time).total_seconds()
                aggregated_metrics["execution_time"].append(duration)
                
                # Aggregate task metrics
                for task in execution["graph_state"]["nodes"].values():
                    task_type = task["task_type"]
                    if task_type not in aggregated_metrics["task_metrics"]:
                        aggregated_metrics["task_metrics"][task_type] = {
                            "success_rate": [],
                            "execution_time": []
                        }
                    
                    task_metrics = aggregated_metrics["task_metrics"][task_type]
                    task_metrics["success_rate"].append(
                        1.0 if task["status"] == "completed" else 0.0
                    )
                    
                    if task["start_time"] and task["end_time"]:
                        task_start = datetime.fromisoformat(task["start_time"])
                        task_end = datetime.fromisoformat(task["end_time"])
                        task_duration = (task_end - task_start).total_seconds()
                        task_metrics["execution_time"].append(task_duration)
                
                # Aggregate resource metrics
                if "metrics" in execution:
                    for metric, value in execution["metrics"].items():
                        if metric not in aggregated_metrics["resource_metrics"]:
                            aggregated_metrics["resource_metrics"][metric] = []
                        aggregated_metrics["resource_metrics"][metric].append(value)
            
            # Calculate final metrics
            metrics = {
                "success_rate": sum(aggregated_metrics["success_rate"]) / len(executions),
                "avg_execution_time": sum(aggregated_metrics["execution_time"]) / len(executions),
                "task_metrics": {
                    task_type: {
                        "success_rate": sum(metrics["success_rate"]) / len(metrics["success_rate"]),
                        "avg_execution_time": sum(metrics["execution_time"]) / len(metrics["execution_time"])
                    }
                    for task_type, metrics in aggregated_metrics["task_metrics"].items()
                    if metrics["success_rate"] and metrics["execution_time"]
                },
                "resource_metrics": {
                    metric: sum(values) / len(values)
                    for metric, values in aggregated_metrics["resource_metrics"].items()
                }
            }
            
            return {
                "pattern_id": pattern_id,
                "time_window": time_window,
                "executions": len(executions),
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            raise
    
    async def analyze_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_executions: int = 5
    ) -> List[Dict[str, Any]]:
        """Analyze swarm behavior patterns."""
        try:
            # Get patterns with sufficient executions
            conditions = ["count(e) >= $min_executions"]
            parameters = {"min_executions": min_executions}
            
            if pattern_type:
                conditions.append("p.type = $pattern_type")
                parameters["pattern_type"] = pattern_type
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
            MATCH (p:SwarmPattern)-[:HAS_EXECUTION]->(e:PatternExecution)
            WHERE {where_clause}
            WITH p, collect(e) as executions
            RETURN p, executions
            """
            
            result = await self.pattern_store.driver.execute_query(
                query,
                parameters=parameters
            )
            
            patterns = []
            for record in result:
                pattern = dict(record[0])
                executions = [dict(e) for e in record[1]]
                
                # Analyze pattern behavior
                behavior = await self._analyze_pattern_behavior(pattern, executions)
                
                patterns.append({
                    "pattern_id": pattern["id"],
                    "pattern_type": pattern["type"],
                    "num_executions": len(executions),
                    "behavior": behavior
                })
            
            return patterns
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            raise
    
    async def generate_insights(
        self,
        pattern_id: str,
        analysis_type: str = "performance"
    ) -> List[Dict[str, Any]]:
        """Generate performance insights."""
        try:
            insights = []
            
            if analysis_type == "performance":
                # Get recent metrics
                metrics = await self.collect_metrics(
                    pattern_id=pattern_id,
                    time_window=24  # Last 24 hours
                )
                
                # Analyze success rate
                success_rate = metrics["metrics"]["success_rate"]
                if success_rate < 0.8:
                    insights.append({
                        "type": "warning",
                        "category": "success_rate",
                        "message": f"Low success rate ({success_rate:.2%})",
                        "recommendation": "Review error patterns and task configurations"
                    })
                
                # Analyze execution time
                avg_time = metrics["metrics"]["avg_execution_time"]
                if avg_time > 300:  # 5 minutes
                    insights.append({
                        "type": "optimization",
                        "category": "execution_time",
                        "message": f"High average execution time ({avg_time:.1f}s)",
                        "recommendation": "Consider parallelizing tasks or optimizing configurations"
                    })
                
                # Analyze task performance
                for task_type, task_metrics in metrics["metrics"]["task_metrics"].items():
                    if task_metrics["success_rate"] < 0.9:
                        insights.append({
                            "type": "warning",
                            "category": "task_performance",
                            "message": f"Low success rate for {task_type} tasks ({task_metrics['success_rate']:.2%})",
                            "recommendation": f"Review {task_type} task implementation and error handling"
                        })
            
            elif analysis_type == "resource":
                # Get resource metrics
                metrics = await self.collect_metrics(pattern_id=pattern_id)
                
                resource_metrics = metrics["metrics"]["resource_metrics"]
                if "memory_usage" in resource_metrics:
                    memory_usage = resource_metrics["memory_usage"]
                    if memory_usage > 0.8:  # 80%
                        insights.append({
                            "type": "warning",
                            "category": "resource_usage",
                            "message": f"High memory usage ({memory_usage:.2%})",
                            "recommendation": "Consider optimizing memory usage or scaling resources"
                        })
            
            elif analysis_type == "pattern":
                # Get pattern behavior analysis
                pattern = await self.pattern_store.get_pattern(pattern_id)
                executions = await self._get_pattern_executions(pattern_id)
                
                behavior = await self._analyze_pattern_behavior(pattern, executions)
                
                if behavior.get("bottlenecks"):
                    insights.append({
                        "type": "optimization",
                        "category": "bottlenecks",
                        "message": "Identified execution bottlenecks",
                        "details": behavior["bottlenecks"],
                        "recommendation": "Consider restructuring task dependencies"
                    })
                
                if behavior.get("anti_patterns"):
                    insights.append({
                        "type": "warning",
                        "category": "anti_patterns",
                        "message": "Detected swarm anti-patterns",
                        "details": behavior["anti_patterns"],
                        "recommendation": "Review and refactor pattern implementation"
                    })
            
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            raise
    
    async def _analyze_pattern_behavior(
        self,
        pattern: Dict[str, Any],
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze pattern behavior from executions."""
        try:
            behavior = {
                "bottlenecks": [],
                "anti_patterns": [],
                "execution_patterns": []
            }
            
            # Analyze task dependencies
            config = pattern.get("config", {})
            tasks = config.get("tasks", [])
            
            dependency_map = {}
            for task in tasks:
                task_deps = set(task.get("dependencies", []))
                dependency_map[task["id"]] = task_deps
            
            # Find potential bottlenecks
            for task in tasks:
                dependent_count = sum(
                    1 for deps in dependency_map.values()
                    if task["id"] in deps
                )
                if dependent_count > len(tasks) / 2:
                    behavior["bottlenecks"].append({
                        "task_id": task["id"],
                        "dependent_count": dependent_count,
                        "impact": "high" if dependent_count > len(tasks) * 0.8 else "medium"
                    })
            
            # Detect anti-patterns
            for execution in executions:
                graph_state = execution.get("graph_state", {})
                nodes = graph_state.get("nodes", {})
                
                # Check for long-running tasks
                for node in nodes.values():
                    if node.get("start_time") and node.get("end_time"):
                        start = datetime.fromisoformat(node["start_time"])
                        end = datetime.fromisoformat(node["end_time"])
                        duration = (end - start).total_seconds()
                        
                        if duration > 600:  # 10 minutes
                            behavior["anti_patterns"].append({
                                "type": "long_running_task",
                                "task_id": node["task_id"],
                                "duration": duration
                            })
                
                # Check for excessive dependencies
                for node in nodes.values():
                    if len(node.get("dependencies", [])) > 5:
                        behavior["anti_patterns"].append({
                            "type": "excessive_dependencies",
                            "task_id": node["task_id"],
                            "dependency_count": len(node["dependencies"])
                        })
            
            # Identify execution patterns
            status_sequences = []
            for execution in executions:
                sequence = []
                graph_state = execution.get("graph_state", {})
                nodes = graph_state.get("nodes", {})
                
                for node in sorted(
                    nodes.values(),
                    key=lambda x: x.get("start_time", "")
                ):
                    sequence.append(node["status"])
                
                status_sequences.append(sequence)
            
            # Find common sequences
            sequence_counts = {}
            for sequence in status_sequences:
                key = tuple(sequence)
                if key not in sequence_counts:
                    sequence_counts[key] = 0
                sequence_counts[key] += 1
            
            # Add common patterns
            for sequence, count in sequence_counts.items():
                if count > len(executions) * 0.2:  # 20% threshold
                    behavior["execution_patterns"].append({
                        "sequence": list(sequence),
                        "frequency": count / len(executions)
                    })
            
            return behavior
        except Exception as e:
            logger.error(f"Error analyzing pattern behavior: {str(e)}")
            raise
    
    async def _get_pattern_executions(
        self,
        pattern_id: str
    ) -> List[Dict[str, Any]]:
        """Get pattern executions."""
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})-[:HAS_EXECUTION]->(e:PatternExecution)
            RETURN e
            ORDER BY e.created_at DESC
            """
            
            result = await self.pattern_store.driver.execute_query(
                query,
                parameters={"pattern_id": pattern_id}
            )
            
            return [dict(record[0]) for record in result]
        except Exception as e:
            logger.error(f"Error getting pattern executions: {str(e)}")
            raise
