"""Graph visualization endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional

from nia.memory.types import TaskOutput, OutputType, TaskStatus
from nia.core.types import GraphNode, GraphEdge, GraphLayout

router = APIRouter(prefix="/graph", tags=["graph"])

async def get_graph_store():
    """Get graph store dependency."""
    from nia.memory.graph_store import GraphStore
    store = GraphStore()
    return store

@router.get("/tasks")
async def get_task_graph(store = Depends(get_graph_store)):
    """Get task dependency graph."""
    tasks = await store.get_tasks()
    
    nodes = [
        GraphNode(
            id=task["id"],
            label=task["name"],
            type="task",
            metadata={"status": task["status"].value}
        )
        for task in tasks
    ]
    
    edges = [
        GraphEdge(
            from_=dep,
            to=task["id"],
            type="depends_on"
        )
        for task in tasks
        for dep in task["dependencies"]
    ]
    
    return {"nodes": nodes, "edges": edges}

@router.get("/tasks/{task_id}/outputs")
async def get_task_outputs(task_id: str, store = Depends(get_graph_store)):
    """Get task output visualization."""
    outputs = await store.get_task_outputs(task_id)
    
    nodes = [
        GraphNode(id=task_id, label=f"Task {task_id}", type="task")
    ]
    
    for i, output in enumerate(outputs):
        nodes.append(
            GraphNode(
                id=f"output{i+1}",
                label=f"{output.type.value.title()} Output",
                type="output",
                metadata={
                    "output_type": output.type.value,
                    **output.metadata
                }
            )
        )
    
    edges = [
        GraphEdge(
            from_=task_id,
            to=f"output{i+1}",
            type="produces"
        )
        for i in range(len(outputs))
    ]
    
    return {"nodes": nodes, "edges": edges}

@router.get("/tasks/statistics")
async def get_task_statistics(store = Depends(get_graph_store)):
    """Get task statistics visualization."""
    stats = await store.get_task_statistics()
    
    nodes = [
        GraphNode(
            id="stats",
            label="Task Statistics",
            type="stats",
            metadata={"total": stats["total_tasks"]}
        ),
        GraphNode(
            id="completed",
            label="Completed",
            type="status",
            metadata={"count": stats["completed"]}
        ),
        GraphNode(
            id="in_progress",
            label="In Progress", 
            type="status",
            metadata={"count": stats["in_progress"]}
        ),
        GraphNode(
            id="pending",
            label="Pending",
            type="status", 
            metadata={"count": stats["pending"]}
        ),
        GraphNode(
            id="outputs",
            label="Output Types",
            type="outputs"
        )
    ]
    
    # Add output type nodes
    for output_type, count in stats["output_types"].items():
        nodes.append(
            GraphNode(
                id=output_type,
                label=output_type.title(),
                type="output_type",
                metadata={"count": count}
            )
        )
    
    edges = [
        GraphEdge(from_="stats", to="completed", type="has_status"),
        GraphEdge(from_="stats", to="in_progress", type="has_status"),
        GraphEdge(from_="stats", to="pending", type="has_status"),
        GraphEdge(from_="stats", to="outputs", type="has_outputs")
    ]
    
    # Add output type edges
    for output_type in stats["output_types"]:
        edges.append(
            GraphEdge(from_="outputs", to=output_type, type="output_type")
        )
    
    return {"nodes": nodes, "edges": edges}

@router.get("/tasks/layout")
async def get_task_layout(layout: str = "hierarchical", store = Depends(get_graph_store)):
    """Get task graph layout."""
    return await store.get_graph_layout(layout)

@router.get("/search")
async def search_task_graph(query: str, types: Optional[List[str]] = None, store = Depends(get_graph_store)):
    """Search task graph."""
    return await store.search_graph(query, types)

@router.get("/filter")
async def filter_task_graph(status: Optional[str] = None, store = Depends(get_graph_store)):
    """Filter task graph."""
    return await store.filter_graph(status=status)
