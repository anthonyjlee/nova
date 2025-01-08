"""FastAPI endpoints for profile management."""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from pydantic import BaseModel

from nia.core.profiles.profile_types import (
    UserProfile,
    ProfileUpdate,
    BigFiveTraits,
    LearningStyle,
    CommunicationPreferences,
    AutoApprovalSettings
)
from nia.core.profiles.profile_manager import ProfileManager
from nia.core.profiles.profile_agent import ProfileAgent
from nia.nova.core.dependencies import get_profile_manager

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

class CreateProfileRequest(BaseModel):
    """Profile creation request."""
    profile_id: str
    personality: BigFiveTraits
    learning_style: LearningStyle
    communication: CommunicationPreferences
    auto_approval: AutoApprovalSettings

class AdaptTaskRequest(BaseModel):
    """Task adaptation request."""
    task: dict
    domain: str

class CheckApprovalRequest(BaseModel):
    """Operation approval check request."""
    operation: str
    domain: str
    confidence: float

class UpdateConfidenceRequest(BaseModel):
    """Domain confidence update request."""
    domain: str
    confidence: float
    operation_success: bool

@router.post("/", response_model=UserProfile)
async def create_profile(
    request: CreateProfileRequest,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> UserProfile:
    """Create a new user profile."""
    try:
        return await profile_manager.create_profile(
            profile_id=request.profile_id,
            personality=request.personality,
            learning_style=request.learning_style,
            communication=request.communication,
            auto_approval=request.auto_approval
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{profile_id}", response_model=Optional[UserProfile])
async def get_profile(
    profile_id: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> Optional[UserProfile]:
    """Get a user profile by ID."""
    profile = await profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/{profile_id}", response_model=Optional[UserProfile])
async def update_profile(
    profile_id: str,
    update: ProfileUpdate,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> Optional[UserProfile]:
    """Update an existing user profile."""
    profile = await profile_manager.update_profile(profile_id, update)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> dict:
    """Delete a user profile."""
    success = await profile_manager.delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success", "message": "Profile deleted"}

@router.get("/", response_model=List[UserProfile])
async def list_profiles(
    domain: Optional[str] = None,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> List[UserProfile]:
    """List all user profiles, optionally filtered by domain."""
    return await profile_manager.list_profiles(domain)

@router.post("/{profile_id}/adapt-task")
async def adapt_task(
    profile_id: str,
    request: AdaptTaskRequest,
    profile_agent: ProfileAgent = Depends(get_profile_manager)
) -> dict:
    """Adapt a task based on user profile."""
    try:
        return await profile_agent.adapt_task(profile_id, request.task, request.domain)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{profile_id}/domain-confidence/{domain}")
async def get_domain_confidence(
    profile_id: str,
    domain: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> dict:
    """Get confidence score for domain access."""
    try:
        confidence = await profile_manager.get_domain_confidence(profile_id, domain)
        return {"confidence": confidence}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{profile_id}/check-approval")
async def check_operation_approval(
    profile_id: str,
    request: CheckApprovalRequest,
    profile_agent: ProfileAgent = Depends(get_profile_manager)
) -> dict:
    """Check if operation can be auto-approved."""
    try:
        approved = await profile_agent.check_auto_approval(
            profile_id,
            request.operation,
            request.domain,
            request.confidence
        )
        return {"approved": approved}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{profile_id}/update-confidence")
async def update_domain_confidence(
    profile_id: str,
    request: UpdateConfidenceRequest,
    profile_agent: ProfileAgent = Depends(get_profile_manager)
) -> dict:
    """Update domain confidence based on operation outcome."""
    try:
        await profile_agent.update_domain_confidence(
            profile_id,
            request.domain,
            request.confidence,
            request.operation_success
        )
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
