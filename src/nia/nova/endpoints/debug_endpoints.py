"""Debug endpoints for managing debug flags and settings."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/debug", tags=["debug"])

# In-memory debug flags storage
debug_flags = {
    'logValidation': False,
    'logWebSocket': False,
    'logStorage': False,
    'strictMode': False
}

class DebugFlagUpdate(BaseModel):
    """Debug flag update request model."""
    flag: str
    enabled: bool

@router.post("/flags")
async def update_debug_flag(update: DebugFlagUpdate):
    """Update a debug flag's state."""
    if update.flag not in debug_flags:
        raise HTTPException(status_code=400, detail=f"Unknown debug flag: {update.flag}")
    
    debug_flags[update.flag] = update.enabled
    return {"status": "success", "flag": update.flag, "enabled": update.enabled}

@router.get("/flags")
async def get_debug_flags():
    """Get current state of all debug flags."""
    return debug_flags
