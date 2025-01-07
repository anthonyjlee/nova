"""Graph visualization endpoints."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query

from nia.visualization.graph_renderer import GraphRenderer
from nia.swarm.pattern_store import SwarmPatternStore
from nia.swarm.graph_integration import SwarmGraphIntegration
from nia.nova.core.auth import check_rate_limit, get_permission
from nia.nova.core.error_handling import ServiceError, retry_on_error

logger = logging.getLogger(__name__)

# Create router with dependencies
visualization_router = APIRouter(
    prefix="/api/visualization",
    tags=["visualization"],
    dependencies=[Depends(check_rate_limit)]
)

# Service dependencies
async def get_graph_renderer():
    """Get graph renderer instance."""
    return GraphRenderer()

async def get_pattern_store():
    """Get pattern store instance."""
    store = SwarmPatternStore(
        neo4j_uri="bolt://localhost:7687"
    )
    try:
        await store.connect()
        yield store
    finally:
        await store.close()

@visualization_router.get("/dag/{task_id}")
@retry_on_error(max_retries=3)
async def get_dag_visualization(
    task_id: str,
    config: Optional[Dict[str, Any]] = None,
    _: None = Depends(get_permission("read")),
    pattern_store: SwarmPatternStore = Depends(get_pattern_store),
    renderer: GraphRenderer = Depends(get_graph_renderer)
) -> Dict[str, Any]:
    """Get DAG visualization for task."""
    try:
        # Get task execution
        execution = await pattern_store.get_pattern_execution(task_id)
        if not execution:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Task {task_id} not found"
                }
            )
        
        # Extract nodes and edges from execution
        graph_state = execution.get("graph_state", {})
        nodes = []
        edges = []
        
        # Convert nodes
        for node_id, node_data in graph_state.get("nodes", {}).items():
            nodes.append({
                "id": node_id,
                **node_data
            })
        
        # Convert edges
        for source, targets in graph_state.get("edges", {}).items():
            for target in targets:
                edges.append({
                    "from": source,
                    "to": target
                })
        
        # Render visualization
        visualization = await renderer.render_dag(
            nodes=nodes,
            edges=edges,
            config=config
        )
        
        return {
            "task_id": task_id,
            "visualization": visualization,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@visualization_router.get("/pattern/{pattern_id}")
@retry_on_error(max_retries=3)
async def get_pattern_visualization(
    pattern_id: str,
    config: Optional[Dict[str, Any]] = None,
    _: None = Depends(get_permission("read")),
    pattern_store: SwarmPatternStore = Depends(get_pattern_store),
    renderer: GraphRenderer = Depends(get_graph_renderer)
) -> Dict[str, Any]:
    """Get pattern visualization."""
    try:
        # Get pattern
        pattern = await pattern_store.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Pattern {pattern_id} not found"
                }
            )
        
        # Render visualization
        visualization = await renderer.render_pattern(
            pattern=pattern,
            config=config
        )
        
        return {
            "pattern_id": pattern_id,
            "visualization": visualization,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@visualization_router.get("/integrated/{pattern_id}/{execution_id}")
@retry_on_error(max_retries=3)
async def get_integrated_visualization(
    pattern_id: str,
    execution_id: str,
    config: Optional[Dict[str, Any]] = None,
    _: None = Depends(get_permission("read")),
    pattern_store: SwarmPatternStore = Depends(get_pattern_store),
    renderer: GraphRenderer = Depends(get_graph_renderer)
) -> Dict[str, Any]:
    """Get integrated pattern and execution visualization."""
    try:
        # Get pattern and execution
        pattern = await pattern_store.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Pattern {pattern_id} not found"
                }
            )
        
        execution = await pattern_store.get_pattern_execution(execution_id)
        if not execution:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Execution {execution_id} not found"
                }
            )
        
        # Render visualization
        visualization = await renderer.render_integrated_view(
            pattern=pattern,
            execution=execution,
            config=config
        )
        
        return {
            "pattern_id": pattern_id,
            "execution_id": execution_id,
            "visualization": visualization,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@visualization_router.get("/patterns")
@retry_on_error(max_retries=3)
async def get_pattern_list_visualization(
    pattern_type: Optional[str] = Query(None),
    limit: int = Query(10, gt=0, le=100),
    _: None = Depends(get_permission("read")),
    pattern_store: SwarmPatternStore = Depends(get_pattern_store),
    renderer: GraphRenderer = Depends(get_graph_renderer)
) -> Dict[str, Any]:
    """Get visualization of pattern relationships."""
    try:
        # Get patterns
        patterns = await pattern_store.search_patterns(
            pattern_type=pattern_type,
            metadata_filters=None
        )
        
        # Limit number of patterns
        patterns = patterns[:limit]
        
        # Create nodes for patterns
        nodes = []
        edges = []
        
        for pattern in patterns:
            # Add pattern node
            nodes.append({
                "id": pattern["id"],
                "label": pattern.get("type", "unknown"),
                "type": "pattern",
                "data": {
                    "pattern_type": pattern.get("type"),
                    "created_at": pattern.get("created_at"),
                    "updated_at": pattern.get("updated_at")
                }
            })
            
            # Add relationship edges
            for rel in pattern.get("relationships", []):
                edges.append({
                    "from": pattern["id"],
                    "to": rel["pattern_id"],
                    "type": rel["type"]
                })
        
        # Render visualization
        visualization = await renderer.render_pattern(
            pattern={
                "config": {
                    "tasks": nodes
                }
            },
            config={
                "layout": "force",
                "node_spacing": 200,
                "edge_length": 300
            }
        )
        
        return {
            "patterns": len(patterns),
            "visualization": visualization,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@visualization_router.get("/executions/{pattern_id}")
@retry_on_error(max_retries=3)
async def get_execution_history_visualization(
    pattern_id: str,
    limit: int = Query(5, gt=0, le=20),
    _: None = Depends(get_permission("read")),
    pattern_store: SwarmPatternStore = Depends(get_pattern_store),
    renderer: GraphRenderer = Depends(get_graph_renderer)
) -> Dict[str, Any]:
    """Get visualization of pattern execution history."""
    try:
        # Get pattern and recent executions
        pattern = await pattern_store.get_pattern(pattern_id)
        if not pattern:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Pattern {pattern_id} not found"
                }
            )
        
        executions = await pattern_store.get_pattern_history(pattern_id)
        executions = executions[:limit]
        
        # Create timeline visualization
        nodes = []
        edges = []
        
        # Add pattern node
        nodes.append({
            "id": pattern_id,
            "label": pattern.get("type", "unknown"),
            "type": "pattern",
            "data": pattern
        })
        
        # Add execution nodes
        for execution in executions:
            exec_id = execution["id"]
            nodes.append({
                "id": exec_id,
                "label": f"Execution {exec_id[-8:]}",
                "type": "execution",
                "status": execution["status"],
                "data": execution
            })
            
            # Link to pattern
            edges.append({
                "from": pattern_id,
                "to": exec_id,
                "type": "execution_of"
            })
        
        # Render visualization
        visualization = await renderer.render_dag(
            nodes=nodes,
            edges=edges,
            config={
                "rankdir": "LR",  # Left to right
                "node_spacing": 100,
                "rank_spacing": 50
            }
        )
        
        return {
            "pattern_id": pattern_id,
            "executions": len(executions),
            "visualization": visualization,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))
