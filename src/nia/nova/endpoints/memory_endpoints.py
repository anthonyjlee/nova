"""FastAPI endpoints for memory operations."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.core.types.memory_types import Memory, EpisodicMemory, MemoryType

from nia.core.auth import (
    check_rate_limit,
    check_domain_access,
    get_permission
)
from nia.core.error_handling import (
    NovaError,
    ValidationError,
    ResourceNotFoundError,
    ServiceError,
    retry_on_error,
    validate_request
)
from nia.core.dependencies import (
    get_memory_system,
    get_orchestration_agent
)

# Create router with dependencies
memory_router = APIRouter(
    prefix="",
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
        
        # Create memory object
        memory = Memory(
            content=request["content"],
            type=request["type"],
            importance=request.get("importance", 0.5),
            context={
                "domain": domain or request.get("domain", "professional"),
                **request.get("context", {})
            },
            metadata={
                "domain": domain,
                "memory_type": request["type"],
                "created_at": datetime.now(timezone.utc).isoformat()
            } if domain else {},
            timestamp=datetime.now(timezone.utc)
        )
        
        # Store memory
        await memory_system.store_experience(memory)
        
        return {
            "memory_id": memory.id,
            "status": "stored",
            "type": request["type"],
            "timestamp": datetime.now(timezone.utc).isoformat()
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
        # Build query dict
        query_dict = {
            "content": query,
            "filter": {
                "domain": domain,
                "type": memory_type
            } if domain or memory_type else {}
        }
        
        # Search episodic memory
        results = await memory_system.query_episodic(query_dict)
        
        return {
            "query": query,
            "matches": results,
            "total": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat()
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
                "created_at": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
        await memory_system.consolidate_memories()
        
        # Return basic result since consolidate_memories doesn't return stats
        return {
            "consolidated_count": 0,  # Not tracked
            "pruned_count": 0,  # Not tracked
            "timestamp": datetime.now(timezone.utc).isoformat()
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
        # Create memory for pruning operation
        pruning_memory = Memory(
            content="Pruning memory graph",
            type=MemoryType.SEMANTIC,  # Use SEMANTIC type for system operations
            importance=1.0,
            context={"domain": domain} if domain else {},
            metadata={
                "operation": "prune",
                "domain": domain
            },
            timestamp=datetime.now(timezone.utc)
        )
        await memory_system.store_experience(pruning_memory)
        
        # Return basic result since actual pruning isn't implemented
        return {
            "pruned_nodes": 0,
            "pruned_relationships": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise ServiceError(str(e))
