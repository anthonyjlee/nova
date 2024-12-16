"""
Example showing DAG integration with two-layer memory system.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from nia.memory import MemorySystem
from nia.memory.memory_integration import MemoryIntegration
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
    
    async def initialize(self):
        """Initialize system asynchronously."""
        # Initialize memory system
        await self.memory_system.initialize()
        
        # Initialize memory integration
        self.memory_integration = MemoryIntegration(self.memory_system.memory_store)
        
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
            AgentType.RESEARCH: self.research_agent.process_interaction,
            AgentType.MEMORY: self.meta_agent.process_interaction  # Use meta agent for memory tasks
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
            # Get relevant memories for context
            memories = await self.memory_integration.get_relevant_memories(task)
            
            # Create context with memories
            context = TaskContext(
                inputs=task.inputs,
                parameters=task.parameters,
                memory_context={
                    'episodic': memories['episodic'],
                    'semantic': memories['semantic']
                }
            )
            
            # Start task
            task.start(context)
            
            # Get appropriate handler
            handler = self.agent_handlers.get(task.agent_type)
            if not handler:
                raise ValueError(f"No handler for agent type {task.agent_type}")
            
            # Get content from inputs
            content = task.inputs.get('content', '')
            
            # Execute task with just the content
            result = await handler(content)
            
            # Create task result
            task_result = TaskResult(
                success=True,
                output=result,
                metadata={
                    'agent_type': task.agent_type.name,
                    'execution_time': str(datetime.now() - task.started_at)
                }
            )
            
            # Complete task
            task.complete(task_result)
            
            # Store task execution in episodic memory
            await self.memory_integration.store_task_execution(task, graph, {
                'result': result,
                'success': True,
                'execution_time': str(datetime.now() - task.started_at)
            })
            
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
            
            # Store failed task execution
            await self.memory_integration.store_task_execution(task, graph, {
                'error': error_msg,
                'success': False
            })
    
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
            response = None
            if execution_task.status == TaskStatus.COMPLETED and execution_task.result:
                response = execution_task.result.output
            else:
                response = "Failed to generate response"
            
            # Store graph execution in episodic memory
            await self.memory_integration.store_graph_execution(graph, {
                'response': response,
                'success': execution_task.status == TaskStatus.COMPLETED,
                'importance': 1.0 if "artificial intelligence" in content.lower() else 0.5
            })
            
            # Consolidate memories
            await self.memory_integration.consolidate_memories(graph)
            
            # Mark graph as completed
            self.task_planner.complete_graph(graph_id)
            
            return response
            
        except Exception as e:
            error_msg = f"Failed to process interaction: {str(e)}"
            print(f"Error: {error_msg}")
            if 'graph_id' in locals():
                self.task_planner.fail_graph(graph_id)
            return error_msg

async def main():
    """Run the example."""
    print("Initializing system...")
    
    # Initialize system
    system = DAGMemorySystem()
    await system.initialize()
    
    print("System initialized!")
    
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
