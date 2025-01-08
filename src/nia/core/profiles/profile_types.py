"""Type definitions for user profile system."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, confloat

class BigFiveTraits(BaseModel):
    """Big Five personality traits."""
    openness: confloat(ge=0.0, le=1.0)
    conscientiousness: confloat(ge=0.0, le=1.0)
    extraversion: confloat(ge=0.0, le=1.0)
    agreeableness: confloat(ge=0.0, le=1.0)
    neuroticism: confloat(ge=0.0, le=1.0)

class LearningStyle(BaseModel):
    """Learning style preferences."""
    visual: confloat(ge=0.0, le=1.0)
    auditory: confloat(ge=0.0, le=1.0)
    kinesthetic: confloat(ge=0.0, le=1.0)

class CommunicationPreferences(BaseModel):
    """Communication style preferences."""
    direct: confloat(ge=0.0, le=1.0)
    detailed: confloat(ge=0.0, le=1.0)
    formal: confloat(ge=0.0, le=1.0)

class ApprovalThresholds(BaseModel):
    """Auto-approval thresholds for different operations."""
    task_creation: confloat(ge=0.0, le=1.0)
    resource_access: confloat(ge=0.0, le=1.0)
    domain_crossing: confloat(ge=0.0, le=1.0)

class AutoApprovalSettings(BaseModel):
    """Auto-approval settings for user operations."""
    auto_approve_domains: List[str]
    approval_thresholds: ApprovalThresholds
    restricted_operations: List[str]

class UserProfile(BaseModel):
    """Complete user profile."""
    profile_id: str
    personality: BigFiveTraits
    learning_style: LearningStyle
    communication: CommunicationPreferences
    auto_approval: AutoApprovalSettings
    domains: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "professional": {"confidence": 1.0},
            "personal": {"confidence": 1.0}
        }
    )
    created_at: str
    updated_at: str
    version: str = "1.0.0"

class ProfileUpdate(BaseModel):
    """Profile update request."""
    profile_id: str
    personality: Optional[BigFiveTraits] = None
    learning_style: Optional[LearningStyle] = None
    communication: Optional[CommunicationPreferences] = None
    auto_approval: Optional[AutoApprovalSettings] = None
    domains: Optional[Dict[str, Dict[str, float]]] = None
