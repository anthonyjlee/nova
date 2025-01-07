"""Integration layer between DAG and Neo4j graphs."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from nia.swarm.dag import SwarmDAG
from nia.swarm.pattern_store import SwarmPatternStore

logger = logging.getLogger(__name__)

class SwarmGraphIntegration:
    """Integrates DAG and Neo4j graphs."""
    
    def __init__(self, pattern_store: SwarmPatternStore):
        """Initialize integration layer."""
        self.pattern_store = pattern_store
    
    async def instantiate_pattern(
        self,
        pattern_id: str,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> SwarmDAG:
        """Create DAG from stored pattern."""
        try:
            # Get pattern from store
            pattern = await self.pattern_store.get_pattern(pattern_id)
            if not pattern:
                raise ValueError(f"Pattern {pattern_id} not found")
            
            # Create new DAG instance
            dag = SwarmDAG()
            
            # Apply configuration overrides
            pattern_config = {
                **(pattern.get("config", {})),
                **(config_overrides or {})
            }
            
            # Create task nodes based on pattern
            task_mapping = {}  # pattern_task_id -> dag_task_id
            
            # First pass: Create all task nodes
            for task in pattern_config.get("tasks", []):
                task_id = await dag.add_task_node(
                    task_type=task["type"],
                    config=task["config"]
                )
                task_mapping[task["id"]] = task_id
            
            # Second pass: Set up dependencies
            for task in pattern_config.get("tasks", []):
                if "dependencies" in task:
                    for dep_id in task["dependencies"]:
                        await dag.set_dependency(
                            dependency_id=task_mapping[dep_id],
                            dependent_id=task_mapping[task["id"]]
                        )
            
            return dag
        except Exception as e:
            logger.error(f"Error instantiating pattern: {str(e)}")
            raise
    
    async def persist_execution(
        self,
        dag: SwarmDAG,
        pattern_id: str,
        execution_id: Optional[str] = None
    ) -> str:
        """Store execution results in Neo4j."""
        try:
            # Generate execution ID if not provided
            if not execution_id:
                execution_id = f"exec_{uuid.uuid4().hex[:8]}"
            
            # Get pattern
            pattern = await self.pattern_store.get_pattern(pattern_id)
            if not pattern:
                raise ValueError(f"Pattern {pattern_id} not found")
            
            # Get DAG state
            graph_state = await dag.get_graph_state()
            
            # Create execution record
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})
            CREATE (e:PatternExecution {
                id: $execution_id,
                graph_state: $graph_state,
                created_at: $created_at,
                completed_at: $completed_at,
                status: $status,
                metrics: $metrics
            })
            CREATE (p)-[:HAS_EXECUTION]->(e)
            """
            
            # Calculate execution metrics
            metrics = await self._calculate_execution_metrics(dag)
            
            # Determine execution status
            all_completed = all(
                node["status"] == "completed"
                for node in graph_state["nodes"].values()
            )
            any_failed = any(
                node["status"] == "failed"
                for node in graph_state["nodes"].values()
            )
            
            status = "completed" if all_completed else "failed" if any_failed else "partial"
            
            await self.pattern_store.driver.execute_query(
                query,
                parameters={
                    "pattern_id": pattern_id,
                    "execution_id": execution_id,
                    "graph_state": graph_state,
                    "created_at": graph_state["nodes"][list(graph_state["nodes"].keys())[0]]["start_time"],
                    "completed_at": datetime.now().isoformat(),
                    "status": status,
                    "metrics": metrics
                }
            )
            
            return execution_id
        except Exception as e:
            logger.error(f"Error persisting execution: {str(e)}")
            raise
    
    async def analyze_performance(
        self,
        pattern_id: str,
        num_executions: int = 10
    ) -> Dict[str, Any]:
        """Compare pattern vs execution performance."""
        try:
            query = """
            MATCH (p:SwarmPattern {id: $pattern_id})-[:HAS_EXECUTION]->(e:PatternExecution)
            WHERE e.status = 'completed'
            RETURN e
            ORDER BY e.created_at DESC
            LIMIT $limit
            """
            
            result = await self.pattern_store.driver.execute_query(
                query,
                parameters={
                    "pattern_id": pattern_id,
                    "limit": num_executions
                }
            )
            
            if not result:
                return {
                    "pattern_id": pattern_id,
                    "num_executions": 0,
                    "average_duration": 0,
                    "success_rate": 0,
                    "performance_metrics": {}
                }
            
            # Analyze executions
            total_duration = 0
            success_count = 0
            aggregated_metrics = {}
            
            for record in result:
                execution = dict(record[0])
                
                # Calculate duration
                start_time = datetime.fromisoformat(execution["created_at"])
                end_time = datetime.fromisoformat(execution["completed_at"])
                duration = (end_time - start_time).total_seconds()
                total_duration += duration
                
                # Count successes
                if execution["status"] == "completed":
                    success_count += 1
                
                # Aggregate metrics
                metrics = execution["metrics"]
                for key, value in metrics.items():
                    if key not in aggregated_metrics:
                        aggregated_metrics[key] = []
                    aggregated_metrics[key].append(value)
            
            # Calculate averages
            num_executions = len(result)
            average_metrics = {
                key: sum(values) / len(values)
                for key, values in aggregated_metrics.items()
            }
            
            return {
                "pattern_id": pattern_id,
                "num_executions": num_executions,
                "average_duration": total_duration / num_executions,
                "success_rate": success_count / num_executions,
                "performance_metrics": average_metrics
            }
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            raise
    
    async def optimize_pattern(
        self,
        pattern_id: str,
        optimization_target: str = "execution_time"
    ) -> Dict[str, Any]:
        """Optimize pattern based on execution history."""
        try:
            # Get pattern and recent executions
            pattern = await self.pattern_store.get_pattern(pattern_id)
            if not pattern:
                raise ValueError(f"Pattern {pattern_id} not found")
            
            analysis = await self.analyze_performance(pattern_id)
            
            # Generate optimization suggestions
            optimizations = []
            
            if optimization_target == "execution_time":
                # Look for parallel execution opportunities
                pattern_config = pattern.get("config", {})
                tasks = pattern_config.get("tasks", [])
                
                # Find independent tasks that could be parallelized
                dependency_map = {}
                for task in tasks:
                    task_deps = set(task.get("dependencies", []))
                    dependency_map[task["id"]] = task_deps
                
                # Find tasks with no dependencies between them
                for i, task1 in enumerate(tasks):
                    for task2 in tasks[i+1:]:
                        if (
                            task1["id"] not in dependency_map[task2["id"]] and
                            task2["id"] not in dependency_map[task1["id"]]
                        ):
                            optimizations.append({
                                "type": "parallelization",
                                "tasks": [task1["id"], task2["id"]],
                                "description": f"Tasks {task1['id']} and {task2['id']} can be executed in parallel"
                            })
            
            elif optimization_target == "resource_usage":
                # Look for resource consolidation opportunities
                pattern_config = pattern.get("config", {})
                tasks = pattern_config.get("tasks", [])
                
                # Group tasks by type
                task_types = {}
                for task in tasks:
                    task_type = task["type"]
                    if task_type not in task_types:
                        task_types[task_type] = []
                    task_types[task_type].append(task["id"])
                
                # Suggest merging similar tasks
                for task_type, task_ids in task_types.items():
                    if len(task_ids) > 1:
                        optimizations.append({
                            "type": "consolidation",
                            "task_type": task_type,
                            "tasks": task_ids,
                            "description": f"Consider consolidating {len(task_ids)} tasks of type {task_type}"
                        })
            
            # Create optimized version if optimizations found
            if optimizations:
                # Create new version with optimization metadata
                new_version = f"v{len(await self.pattern_store.get_pattern_history(pattern_id)) + 1}"
                
                await self.pattern_store.create_pattern_version(
                    pattern_id=pattern_id,
                    version=new_version,
                    config=pattern.get("config", {}),
                    metadata={
                        "optimizations": optimizations,
                        "analysis": analysis
                    }
                )
            
            return {
                "pattern_id": pattern_id,
                "optimizations": optimizations,
                "analysis": analysis,
                "optimization_target": optimization_target
            }
        except Exception as e:
            logger.error(f"Error optimizing pattern: {str(e)}")
            raise
    
    async def _calculate_execution_metrics(self, dag: SwarmDAG) -> Dict[str, float]:
        """Calculate execution metrics from DAG state."""
        try:
            graph_state = await dag.get_graph_state()
            
            metrics = {
                "total_tasks": len(graph_state["nodes"]),
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_edges": sum(len(edges) for edges in graph_state["edges"].values()),
                "average_dependencies": 0
            }
            
            # Calculate task status metrics
            for node in graph_state["nodes"].values():
                if node["status"] == "completed":
                    metrics["completed_tasks"] += 1
                elif node["status"] == "failed":
                    metrics["failed_tasks"] += 1
            
            # Calculate dependency metrics
            total_dependencies = sum(
                len(node["dependencies"])
                for node in graph_state["nodes"].values()
            )
            if metrics["total_tasks"] > 0:
                metrics["average_dependencies"] = total_dependencies / metrics["total_tasks"]
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise
