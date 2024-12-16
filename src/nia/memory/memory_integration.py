"""
Memory integration layer for DAG and two-layer memory system.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .persistence import MemoryStore
from ..dag import TaskGraph, TaskNode, TaskType, TaskStatus

logger = logging.getLogger(__name__)

class MemoryIntegration:
    """Integrates DAG execution with two-layer memory system."""
    
    def __init__(self, memory_store: MemoryStore):
        """Initialize memory integration."""
        self.memory_store = memory_store
    
    async def store_task_execution(
        self,
        task: TaskNode,
        graph: TaskGraph,
        result: Optional[Dict] = None
    ) -> None:
        """Store task execution in episodic memory."""
        try:
            # Store task execution trace
            await self.memory_store.store_memory(
                memory_type="episodic",
                content={
                    'task_id': task.task_id,
                    'task_type': task.task_type.name,
                    'description': task.description,
                    'status': task.status.name,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'result': result,
                    'graph_context': {
                        'graph_id': graph.name,
                        'dependencies': list(task.dependencies),
                        'dependents': list(task.dependents)
                    },
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'task_type': task.task_type.name,
                    'agent_type': task.agent_type.name,
                    'status': task.status.name,
                    'importance': 1.0 if task.task_type in [TaskType.ANALYSIS, TaskType.SYNTHESIS] else 0.5
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing task execution: {str(e)}")
    
    async def store_graph_execution(
        self,
        graph: TaskGraph,
        final_result: Optional[Dict] = None
    ) -> None:
        """Store graph execution in episodic memory."""
        try:
            # Get task execution order
            execution_order = [
                task_id for task_id in graph.execution_order
                if graph.tasks[task_id].status == TaskStatus.COMPLETED
            ]
            
            # Store graph execution trace
            await self.memory_store.store_memory(
                memory_type="episodic",
                content={
                    'graph_id': graph.name,
                    'description': graph.description,
                    'execution_order': execution_order,
                    'completed_tasks': list(graph.completed_tasks),
                    'failed_tasks': list(graph.failed_tasks),
                    'final_result': final_result,
                    'timestamp': datetime.now().isoformat()
                },
                metadata={
                    'graph_type': "interaction",
                    'success': len(graph.failed_tasks) == 0,
                    'importance': 1.0 if final_result and final_result.get('importance', 0.5) > 0.5 else 0.5
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing graph execution: {str(e)}")
    
    async def extract_semantic_knowledge(
        self,
        graph: TaskGraph,
        final_result: Optional[Dict] = None
    ) -> None:
        """Extract and store semantic knowledge from graph execution."""
        try:
            # Collect insights from reflection tasks
            insights = []
            patterns = []
            beliefs = []
            
            for task_id, task in graph.tasks.items():
                if task.status == TaskStatus.COMPLETED and task.result:
                    result = task.result.output
                    if isinstance(result, dict):
                        # Collect insights from reflection tasks
                        if task.task_type == TaskType.REFLECTION:
                            if 'key_insights' in result:
                                insights.extend(result['key_insights'])
                            if 'patterns' in result:
                                patterns.extend(result['patterns'])
                        
                        # Collect beliefs from belief tasks
                        elif task.task_type == TaskType.ANALYSIS and task.agent_type == AgentType.BELIEF:
                            if 'core_belief' in result:
                                beliefs.append(result['core_belief'])
            
            # Store semantic knowledge
            if insights or patterns or beliefs:
                await self.memory_store.store_memory(
                    memory_type="semantic",
                    content={
                        'insights': insights,
                        'patterns': patterns,
                        'beliefs': beliefs,
                        'source_graph': graph.name,
                        'timestamp': datetime.now().isoformat()
                    },
                    metadata={
                        'knowledge_type': "learned_concepts",
                        'importance': 1.0 if final_result and final_result.get('importance', 0.5) > 0.5 else 0.5
                    }
                )
            
        except Exception as e:
            logger.error(f"Error extracting semantic knowledge: {str(e)}")
    
    async def get_relevant_memories(
        self,
        task: TaskNode,
        limit: int = 5
    ) -> Dict[str, List[Dict]]:
        """Get relevant memories for a task."""
        try:
            # Get task-specific memory filters
            episodic_filter = {'task_type': task.task_type.name}
            semantic_filter = {'knowledge_type': "learned_concepts"}
            
            # Search both memory layers
            episodic_memories = await self.memory_store.search_similar_memories(
                content=task.description,
                limit=limit,
                filter_dict=episodic_filter,
                memory_type="episodic"
            )
            
            semantic_memories = await self.memory_store.search_similar_memories(
                content=task.description,
                limit=limit,
                filter_dict=semantic_filter,
                memory_type="semantic"
            )
            
            return {
                'episodic': episodic_memories,
                'semantic': semantic_memories
            }
            
        except Exception as e:
            logger.error(f"Error getting relevant memories: {str(e)}")
            return {
                'episodic': [],
                'semantic': []
            }
    
    async def update_semantic_knowledge(
        self,
        task_results: List[Dict],
        graph: TaskGraph
    ) -> None:
        """Update semantic knowledge based on task results."""
        try:
            # Collect all insights and patterns
            all_insights = []
            all_patterns = []
            
            for result in task_results:
                if isinstance(result, dict):
                    if 'insights' in result:
                        all_insights.extend(result['insights'])
                    if 'patterns' in result:
                        all_patterns.extend(result['patterns'])
            
            if all_insights or all_patterns:
                # Store updated semantic knowledge
                await self.memory_store.store_memory(
                    memory_type="semantic",
                    content={
                        'insights': all_insights,
                        'patterns': all_patterns,
                        'source_graph': graph.name,
                        'update_type': "knowledge_refinement",
                        'timestamp': datetime.now().isoformat()
                    },
                    metadata={
                        'knowledge_type': "refined_concepts",
                        'importance': 0.8  # Slightly lower than new knowledge
                    }
                )
            
        except Exception as e:
            logger.error(f"Error updating semantic knowledge: {str(e)}")
    
    async def consolidate_memories(self, graph: TaskGraph) -> None:
        """Consolidate memories after graph execution."""
        try:
            # Get all completed task results
            task_results = []
            for task_id in graph.completed_tasks:
                task = graph.tasks[task_id]
                if task.result and task.result.output:
                    task_results.append(task.result.output)
            
            # Extract and store semantic knowledge
            await self.extract_semantic_knowledge(graph)
            
            # Update existing semantic knowledge
            await self.update_semantic_knowledge(task_results, graph)
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {str(e)}")
