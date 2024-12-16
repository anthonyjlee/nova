"""
Example usage of the DAG system.
"""

import asyncio
from datetime import datetime
from nia.dag import (
    TaskGraph,
    TaskNode,
    TaskType,
    AgentType,
    TaskStatus,
    TaskResult,
    TaskContext
)

def create_sample_graph() -> TaskGraph:
    """Create a sample task graph."""
    # Create graph
    graph = TaskGraph(
        name="Test Graph",
        description="A sample task graph for testing"
    )
    
    # Create tasks
    analysis = TaskNode(
        task_id="analyze_input",
        task_type=TaskType.ANALYSIS,
        agent_type=AgentType.META,
        description="Analyze user input",
        inputs={"user_input": "Sample input"}
    )
    
    planning = TaskNode(
        task_id="plan_response",
        task_type=TaskType.PLANNING,
        agent_type=AgentType.META,
        description="Plan response strategy"
    )
    
    memory = TaskNode(
        task_id="check_memory",
        task_type=TaskType.MEMORY,
        agent_type=AgentType.MEMORY,
        description="Check memory for context"
    )
    
    execution = TaskNode(
        task_id="execute_response",
        task_type=TaskType.EXECUTION,
        agent_type=AgentType.META,
        description="Execute planned response"
    )
    
    reflection = TaskNode(
        task_id="reflect",
        task_type=TaskType.REFLECTION,
        agent_type=AgentType.REFLECTION,
        description="Reflect on execution"
    )
    
    # Add tasks to graph
    graph.add_task(analysis)
    graph.add_task(planning)
    graph.add_task(memory)
    graph.add_task(execution)
    graph.add_task(reflection)
    
    # Add dependencies
    graph.add_dependency("plan_response", "analyze_input")  # Planning depends on analysis
    graph.add_dependency("plan_response", "check_memory")   # Planning depends on memory
    graph.add_dependency("execute_response", "plan_response")  # Execution depends on planning
    graph.add_dependency("reflect", "execute_response")  # Reflection depends on execution
    
    return graph

async def simulate_task_execution(task: TaskNode) -> None:
    """Simulate task execution."""
    print(f"\nExecuting task: {task.task_id} ({task.task_type.name})")
    
    # Create context
    context = TaskContext(
        inputs=task.inputs,
        parameters=task.parameters
    )
    
    # Start task
    task.start(context)
    
    # Simulate work
    await asyncio.sleep(1)
    
    # Complete task
    result = TaskResult(
        success=True,
        output=f"Completed {task.task_id}",
        metadata={
            "execution_time": "1s",
            "agent": task.agent_type.name
        }
    )
    task.complete(result)

async def main():
    """Run the example."""
    print("Creating task graph...")
    graph = create_sample_graph()
    
    # Validate graph
    print("\nValidating graph...")
    errors = graph.validate()
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"- {error}")
        return
    print("Graph is valid!")
    
    # Show execution order
    print("\nTask execution order:")
    for task_id in graph.get_task_order():
        task = graph.tasks[task_id]
        deps = ", ".join(task.dependencies) if task.dependencies else "none"
        print(f"- {task_id} (dependencies: {deps})")
    
    # Simulate execution
    print("\nSimulating execution...")
    ready_tasks = graph.get_ready_tasks()
    while ready_tasks:
        # Execute ready tasks
        await asyncio.gather(*(
            simulate_task_execution(graph.tasks[task_id])
            for task_id in ready_tasks
        ))
        
        # Update task states
        for task_id in ready_tasks:
            task = graph.tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                graph.completed_tasks.add(task_id)
                # Remove completed task from dependencies
                for dependent_id in task.dependents:
                    dependent = graph.tasks[dependent_id]
                    dependent.dependencies.remove(task_id)
        
        # Get next ready tasks
        ready_tasks = graph.get_task_order()
    
    # Show results
    print("\nExecution complete!")
    print("\nTask states:")
    for task_id, task in graph.tasks.items():
        print(f"- {task_id}: {task.status.name}")
        if task.result:
            print(f"  Output: {task.result.output}")
            print(f"  Metadata: {task.result.metadata}")

if __name__ == "__main__":
    asyncio.run(main())
