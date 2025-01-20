"""User profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..core.dependencies import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_world
)
from nia.nova.core.auth.token import get_permission
from ..core.error_handling import ServiceError

# Models
class LearningStyle(BaseModel):
    """Learning style preferences."""
    visual: float = Field(..., ge=0.0, le=1.0)
    auditory: float = Field(..., ge=0.0, le=1.0)
    kinesthetic: float = Field(..., ge=0.0, le=1.0)

class BigFiveTraits(BaseModel):
    """Big Five personality traits."""
    openness: float = Field(..., ge=0.0, le=1.0)
    conscientiousness: float = Field(..., ge=0.0, le=1.0)
    extraversion: float = Field(..., ge=0.0, le=1.0)
    agreeableness: float = Field(..., ge=0.0, le=1.0)
    neuroticism: float = Field(..., ge=0.0, le=1.0)

class CommunicationStyle(BaseModel):
    """Communication style preferences."""
    direct: float = Field(..., ge=0.0, le=1.0)
    detailed: float = Field(..., ge=0.0, le=1.0)
    formal: float = Field(..., ge=0.0, le=1.0)

class PsychometricQuestionnaire(BaseModel):
    """Psychometric questionnaire submission."""
    big_five: BigFiveTraits
    learning_style: LearningStyle
    communication: CommunicationStyle

class AutoApprovalSettings(BaseModel):
    """Auto-approval settings for tasks and operations."""
    auto_approve_domains: List[str] = Field(default_factory=list)
    approval_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "task_creation": 0.8,
            "resource_access": 0.9,
            "domain_crossing": 0.95
        }
    )
    restricted_operations: List[str] = Field(default_factory=list)

    @validator("approval_thresholds")
    def validate_thresholds(cls, v):
        """Validate threshold values are between 0 and 1."""
        for key, value in v.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Threshold {key} must be between 0.0 and 1.0")
        return v

class UserProfile(BaseModel):
    """Complete user profile."""
    id: str
    psychometrics: Optional[PsychometricQuestionnaire] = None
    auto_approval: Optional[AutoApprovalSettings] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Router
user_router = APIRouter(
    prefix="",
    tags=["User Management"],
    responses={404: {"description": "Not found"}}
)

@user_router.get("/user", response_model=Dict[str, Any])
async def get_current_user(
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
):
    """Get current user."""
    try:
        # For now return a mock user
        return {
            "id": "default",
            "name": "Default User",
            "email": "user@example.com",
            "accessLevel": "user",
            "domain": "personal",
            "workspace": "personal",
            "status": "online",
            "apiKey": "valid-test-key",
            "preferences": {
                "theme": "dark",
                "taskFormat": "default",
                "communicationStyle": "balanced",
                "interfaceMode": "standard",
                "notifications": true,
                "autoApprove": false
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.post("/questionnaire", response_model=Dict[str, Any])
async def submit_questionnaire(
    request: PsychometricQuestionnaire,
    _: None = Depends(get_permission("write")),
    analytics_agent: Any = Depends(get_analytics_agent),
    memory_system: Any = Depends(get_memory_system)
):
    """Submit psychometric questionnaire."""
    try:
        result = await analytics_agent.process_analytics(
            content="Submit questionnaire",
            domain="personal",
            questionnaire=request.dict()
        )

        if not result or not result.is_valid:
            raise ServiceError("Failed to process questionnaire")

        return {
            "success": True,
            "profile_id": result.analytics["profile_creation"]["profile_id"],
            "insights": {
                "personality": result.analytics["personality_insights"],
                "learning": result.analytics["learning_preferences"],
                "communication": result.analytics["communication_style"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/profile/{profile_id}", response_model=UserProfile)
async def get_profile(
    profile_id: str,
    _: None = Depends(get_permission("read")),
    memory_system: Any = Depends(get_memory_system)
):
    """Get user profile."""
    try:
        result = await memory_system.query_episodic({
            "content": {},
            "filter": {
                "metadata.profile_id": profile_id,
                "metadata.type": "user_profile"
            },
            "layer": "episodic"
        })

        if not result:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = result[0]["content"]["data"]
        return UserProfile(**profile_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.post("/profile/{profile_id}/auto-approval", response_model=Dict[str, Any])
async def update_auto_approval(
    profile_id: str,
    settings: AutoApprovalSettings,
    _: None = Depends(get_permission("write")),
    analytics_agent: Any = Depends(get_analytics_agent),
    memory_system: Any = Depends(get_memory_system)
):
    """Update auto-approval settings."""
    try:
        result = await analytics_agent.process_analytics(
            content="Update auto-approval settings",
            domain="professional",
            profile_id=profile_id,
            settings=settings.dict()
        )

        if not result or not result.is_valid:
            raise ServiceError("Failed to update settings")

        return {
            "success": True,
            "settings": result.analytics["settings_update"]["current_settings"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/profile/{profile_id}/adaptations", response_model=Dict[str, Any])
async def get_profile_adaptations(
    profile_id: str,
    task_type: Optional[str] = None,
    _: None = Depends(get_permission("read")),
    analytics_agent: Any = Depends(get_analytics_agent)
):
    """Get profile-based adaptations."""
    try:
        result = await analytics_agent.process_analytics(
            content="Complex technical task",
            domain="professional",
            profile_id=profile_id,
            task={
                "type": task_type or "analysis",
                "complexity": "high",
                "technical_depth": "detailed"
            }
        )

        if not result or not result.is_valid:
            raise ServiceError("Failed to get adaptations")

        return {
            "adaptations": result.analytics["task_adaptation"]["adaptations"],
            "profile_applied": result.analytics["task_adaptation"]["profile_applied"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
