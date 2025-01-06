"""FastAPI endpoints for memory operations."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.agents.specialized.orchestration_agent import OrchestrationAgent

from .auth import (
    check_rate_limit,
    check_domain_access,
    get_permission
)
from .error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError,
    retry_on_error,
    validate_request
)
from .endpoints import (
    get_memory_system,
    get_orchestration_agent
)

# Create router with dependencies
memory_router = APIRouter(
    prefix="/api/orchestration/memory",
    tags=["memory"],
    dependencies=[Depends(check_rate_limit)]
)

@memory_router.post("/store")
@retry_on_error(max_retries=3)
async def store_memory(
    request: Dict[str, Any],
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Store content in memory system."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        required_fields = ["content", "type"]
        for field in required_fields:
            if field not in request:
                raise ValidationError(f"Request must include '{field}' field")
        
        # Generate memory ID
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"
        
        # Store in both layers
        await memory_system.store(
            memory_id=memory_id,
            content=request["content"],
            memory_type=request["type"],
            importance=request.get("importance", 0.5),
            context={
                "domain": domain or request.get("domain", "professional"),
                **request.get("context", {})
            },
            metadata={
                "domain": domain,
                "memory_type": request["type"],
                "created_at": datetime.now().isoformat()
            } if domain else None
        )
        
        return {
            "memory_id": memory_id,
            "status": "stored",
            "type": request["type"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@memory_router.get("/search")
@retry_on_error(max_retries=3)
async def search_memory(
    query: str,
    domain: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: Optional[int] = 10,
    _: None = Depends(get_permission("read")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Search memory with domain filtering."""
    try:
        # Build search query
        search_query = query
        if domain:
            search_query = f"{search_query} AND domain:{domain}"
        if memory_type:
            search_query = f"{search_query} AND type:{memory_type}"
        
        # Search both layers
        results = await memory_system.search(
            query=search_query,
            limit=limit,
            metadata={
                "domain": domain,
                "memory_type": memory_type
            } if domain else None
        )
        
        return {
            "query": query,
            "matches": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@memory_router.post("/cross-domain")
@retry_on_error(max_retries=3)
async def cross_domain_operation(
    request: Dict[str, Any],
    _: None = Depends(get_permission("write")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    orchestration_agent: OrchestrationAgent = Depends(get_orchestration_agent)
) -> Dict:
    """Request cross-domain memory operation."""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise ValidationError("Request must be a JSON object")
        
        required_fields = ["from_domain", "to_domain", "operation"]
        for field in required_fields:
            if field not in request:
                raise ValidationError(f"Request must include '{field}' field")
        
        # Generate operation ID
        operation_id = f"op_{uuid.uuid4().hex[:8]}"
        
        # Create approval request
        approval_result = await orchestration_agent.create_task(
            task_id=operation_id,
            task_data={
                "type": "cross_domain_approval",
                "from_domain": request["from_domain"],
                "to_domain": request["to_domain"],
                "operation": request["operation"],
                "status": "pending_approval",
                "created_at": datetime.now().isoformat()
            },
            domain=request["to_domain"],
            metadata={
                "operation_type": "cross_domain",
                "requires_approval": True
            }
        )
        
        return {
            "operation_id": operation_id,
            "status": "pending_approval",
            "from_domain": request["from_domain"],
            "to_domain": request["to_domain"],
            "operation": request["operation"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@memory_router.get("/consolidate")
@retry_on_error(max_retries=3)
async def consolidate_memory(
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Trigger memory consolidation."""
    try:
        # Run consolidation
        consolidation_result = await memory_system.consolidate(
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "consolidated_count": consolidation_result.get("consolidated_count", 0),
            "pruned_count": consolidation_result.get("pruned_count", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))

@memory_router.delete("/prune")
@retry_on_error(max_retries=3)
async def prune_memory(
    domain: Optional[str] = None,
    _: None = Depends(get_permission("write")),
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> Dict:
    """Prune knowledge graph."""
    try:
        # Run pruning
        pruning_result = await memory_system.prune(
            domain=domain,
            metadata={"domain": domain} if domain else None
        )
        
        return {
            "pruned_nodes": pruning_result.get("pruned_nodes", 0),
            "pruned_relationships": pruning_result.get("pruned_relationships", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))
