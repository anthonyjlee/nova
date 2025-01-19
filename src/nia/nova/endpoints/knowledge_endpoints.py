"""Knowledge graph endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime

from ..core.dependencies import get_memory_system
from ..core.auth import get_permission
from ..core.error_handling import ServiceError
from nia.core.types.memory_types import Memory, MemoryType

kg_router = APIRouter(
    prefix="",
    tags=["Knowledge Graph"]
)

@kg_router.post("/crossDomain", response_model=Dict[str, Any], dependencies=[Depends(get_permission("write"))])
async def request_cross_domain_access(
    request: Dict[str, Any],
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Request access to cross-domain knowledge."""
    try:
        # Validate source and target domains exist
        source_domain = request.get("source_domain")
        target_domain = request.get("target_domain")
        
        if not source_domain or not target_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target domains are required"
            )
            
        # Store cross-domain request in episodic memory
        memory = Memory(
            content={
                "source_domain": source_domain,
                "target_domain": target_domain,
                "reason": request.get("reason"),
                "status": "pending"
            },
            type=MemoryType.CROSS_DOMAIN_REQUEST,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "importance": 0.8
            }
        )
        await memory_system.episodic.store(memory)
        
        # Create cross-domain relationship in semantic layer
        await memory_system.semantic.store_knowledge({
            "relationships": [{
                "from": f"domain:{source_domain}",
                "to": f"domain:{target_domain}",
                "type": "CROSS_DOMAIN_ACCESS",
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }]
        })
        
        return {
            "success": True,
            "requestId": memory.id,
            "status": "pending"
        }
    except Exception as e:
        raise ServiceError(str(e))

@kg_router.get("/domains", response_model=Dict[str, Any])
async def list_domains(
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """List available knowledge domains."""
    try:
        # Query domains from semantic layer
        domains = await memory_system.semantic.run_query(
            """
            MATCH (d:Domain)
            RETURN d.name as name, d.type as type, d.description as description
            """
        )
        
        # Get cross-domain relationships
        relationships = await memory_system.semantic.run_query(
            """
            MATCH (d1:Domain)-[r:CROSS_DOMAIN_ACCESS]->(d2:Domain)
            RETURN d1.name as source, d2.name as target, r.status as status
            """
        )
        
        return {
            "domains": [
                {
                    "name": d["name"],
                    "type": d["type"],
                    "description": d["description"]
                }
                for d in domains
            ],
            "relationships": [
                {
                    "source": r["source"],
                    "target": r["target"],
                    "status": r["status"]
                }
                for r in relationships
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@kg_router.post("/taskReference", response_model=Dict[str, Any], dependencies=[Depends(get_permission("write"))])
async def link_task_to_concept(
    request: Dict[str, Any],
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Link a task to a concept in the knowledge graph."""
    try:
        task_id = request.get("task_id")
        concept_id = request.get("concept_id")
        
        if not task_id or not concept_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task ID and concept ID are required"
            )
            
        # Create relationship in semantic layer
        await memory_system.semantic.store_knowledge({
            "relationships": [{
                "from": f"task:{task_id}",
                "to": f"concept:{concept_id}",
                "type": "REFERENCES",
                "metadata": request.get("metadata", {}),
                "timestamp": datetime.now().isoformat()
            }]
        })
        
        return {
            "success": True,
            "taskId": task_id,
            "conceptId": concept_id
        }
    except Exception as e:
        raise ServiceError(str(e))

@kg_router.get("/data", response_model=Dict[str, Any])
async def get_knowledge_data(
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get knowledge graph data."""
    try:
        # Query nodes from semantic layer
        nodes = await memory_system.semantic.run_query(
            """
            MATCH (n)
            RETURN n.id as id, n.name as label, labels(n)[0] as type,
                   n.category as category, n.domain as domain,
                   n.metadata as metadata
            """
        )
        
        # Query relationships
        edges = await memory_system.semantic.run_query(
            """
            MATCH (n1)-[r]->(n2)
            RETURN id(r) as id, type(r) as type, r.label as label,
                   n1.id as source, n2.id as target
            """
        )
        
        return {
            "nodes": [
                {
                    "id": n["id"],
                    "label": n["label"],
                    "type": n["type"],
                    "category": n["category"],
                    "domain": n["domain"],
                    "metadata": n["metadata"]
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": str(e["id"]),
                    "source": e["source"],
                    "target": e["target"],
                    "type": e["type"],
                    "label": e["label"] or e["type"]
                }
                for e in edges
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))

@kg_router.get("/taskConcepts/{task_id}", response_model=Dict[str, Any])
async def get_task_related_concepts(
    task_id: str,
    memory_system: Any = Depends(get_memory_system)
) -> Dict[str, Any]:
    """Get concepts related to a task."""
    try:
        # Query related concepts from semantic layer
        concepts = await memory_system.semantic.run_query(
            """
            MATCH (t:Task {id: $task_id})-[r:REFERENCES]->(c:Concept)
            RETURN c.id as id, c.name as name, c.type as type,
                   r.metadata as metadata, r.timestamp as timestamp
            """,
            {"task_id": task_id}
        )
        
        return {
            "taskId": task_id,
            "concepts": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "type": c["type"],
                    "metadata": c["metadata"],
                    "timestamp": c["timestamp"]
                }
                for c in concepts
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise ServiceError(str(e))
