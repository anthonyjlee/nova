"""
Example showing DAG integration with memory system.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from nia.memory import MemorySystem
from nia.memory.agents import (
    MetaAgent,
    BeliefAgent,
    DesireAgent,
    EmotionAgent,
    ReflectionAgent,
    ResearchAgent
)
from nia.dag import (
    TaskPlanner,
    TaskType,
    AgentType,
    TaskStatus,
    TaskResult,
    TaskContext
)

class DAGMemorySystem:
    """Memory system with DAG-based task management."""
    
    def __init__(self):
        """Initialize system."""
        # Initialize memory system
        self.memory_system = MemorySystem()
        
        # Get agents
        self.meta_agent = self.memory_system.meta_agent
        self.belief_agent = self.memory_system.get_agent("BeliefAgent")
        self.desire_agent = self.memory_system.get_agent("DesireAgent")
        self.emotion_agent = self.memory_system.get_agent("EmotionAgent")
        self.reflection_agent = self.memory_system.get_agent("ReflectionAgent")
        self.research_agent = self.memory_system.get_agent("ResearchAgent")
        
        # Initialize task planner
        self.task_planner = TaskPlanner()
        
        # Map agent types to handlers
        self.agent_handlers = {
            AgentType.META: self.meta_agent.process_interaction,
            AgentType.BELIEF: self.belief_agent.process_interaction,
            AgentType.DESIRE: self.desire_agent.process_interaction,
            AgentType.EMOTION: self.emotion_agent.process_interaction,
            AgentType.REFLECTION: self.reflection_agent.process_interaction,
            AgentType.RESEARCH: self.research_agent.process_interaction
        }
    
    async def execute_task(self, task_id: str, graph_id: str) -> None:
        """Execute a single task."""
        # Get graph and task
        graph = self.task_planner.get_graph(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        task = graph.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        print(f"\nExecuting task: {task.task_id} ({task.task_type.name})")
        
        try:
            # Create context
            context = TaskContext(
                inputs=task.inputs,
                parameters=task.parameters
            )
            
            # Start task
            task.start(context)
            
            # Get appropriate handler
            handler = self.agent_handlers.get(task.agent_type)
            if not handler:
                raise ValueError(f"No handler for agent type {task.agent_type}")
            
            # Execute task
            result = await handler(
                content=task.inputs.get('content', ''),
                **task.inputs
            )
            
            # Complete task
            task_result = TaskResult(
                success=True,
                output=result,
                metadata={
                    'agent_type': task.agent_type.name,
                    'execution_time': str(datetime.now() - task.started_at)
                }
            )
            task.complete(task_result)
            
        except Exception as e:
            # Handle failure
            error_msg = f"Task {task_id} failed: {str(e)}"
            print(f"Error: {error_msg}")
            
            task_result = TaskResult(
                success=False,
                output=None,
                error=error_msg,
                metadata={
                    'agent_type': task.agent_type.name,
                    'error_type': type(e).__name__
                }
            )
            task.complete(task_result)
    
    async def process_interaction(self, content: str, context: Dict[str, Any] = None) -> str:
        """Process an interaction using DAG-based execution."""
        try:
            # Create interaction graph
            graph = self.task_planner.create_interaction_graph(
                content=content,
                context=context
            )
            graph_id = graph.name
            
            print(f"\nCreated interaction graph: {graph_id}")
            print("\nTask execution order:")
            for task_id in graph.get_task_order():
                task = graph.tasks[task_id]
                deps = ", ".join(task.dependencies) if task.dependencies else "none"
                print(f"- {task_id} (dependencies: {deps})")
            
            # Execute tasks
            execution_order = graph.get_task_order()
            completed = set()
            
            while execution_order:
                # Get ready tasks
                ready_tasks = [
                    task_id for task_id in execution_order
                    if all(dep in completed for dep in graph.tasks[task_id].dependencies)
                ]
                
                if not ready_tasks:
                    break
                
                # Execute ready tasks in parallel
                await asyncio.gather(*(
                    self.execute_task(task_id, graph_id)
                    for task_id in ready_tasks
                ))
                
                # Update completed tasks
                completed.update(ready_tasks)
                
                # Remove completed tasks from execution order
                execution_order = [
                    task_id for task_id in execution_order
                    if task_id not in completed
                ]
            
            # Get final response
            execution_task = graph.tasks["execute_response"]
            if execution_task.status == TaskStatus.COMPLETED and execution_task.result:
                response = execution_task.result.output
            else:
                response = "Failed to generate response"
            
            # Mark graph as completed
            self.task_planner.complete_graph(graph_id)
            
            return response
            
        except Exception as e:
            error_msg = f"Failed to process interaction: {str(e)}"
            print(f"Error: {error_msg}")
            if graph_id:
                self.task_planner.fail_graph(graph_id)
            return error_msg

async def main():
    """Run the example."""
    # Initialize system
    system = DAGMemorySystem()
    
    # Test interactions
    interactions = [
        "Hello! How are you today?",
        "What do you know about artificial intelligence?",
        "Can you help me learn Python programming?"
    ]
    
    for interaction in interactions:
        print(f"\n=== Processing: {interaction} ===")
        response = await system.process_interaction(interaction)
        print(f"\nFinal response: {response}")
        print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(main())
