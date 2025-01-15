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

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            return {
                "openness": float(self.openness),
                "conscientiousness": float(self.conscientiousness)
            }
        return super().dict()

class LearningStyle(BaseModel):
    """Learning style preferences."""
    visual: confloat(ge=0.0, le=1.0)
    auditory: confloat(ge=0.0, le=1.0)
    kinesthetic: confloat(ge=0.0, le=1.0)

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            return {
                "visual": float(self.visual),
                "auditory": float(self.auditory)
            }
        return super().dict()

class CommunicationPreferences(BaseModel):
    """Communication style preferences."""
    direct: confloat(ge=0.0, le=1.0)
    detailed: confloat(ge=0.0, le=1.0)
    formal: confloat(ge=0.0, le=1.0)

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            return {
                "direct": float(self.direct),
                "detailed": float(self.detailed)
            }
        return super().dict()

class ApprovalThresholds(BaseModel):
    """Auto-approval thresholds for different operations."""
    task_creation: confloat(ge=0.0, le=1.0)
    resource_access: confloat(ge=0.0, le=1.0)
    domain_crossing: confloat(ge=0.0, le=1.0)

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            return {
                "task_creation": float(self.task_creation),
                "resource_access": float(self.resource_access)
            }
        return super().dict()

class AutoApprovalSettings(BaseModel):
    """Auto-approval settings for user operations."""
    auto_approve_domains: List[str]
    approval_thresholds: ApprovalThresholds
    restricted_operations: List[str]

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            return {
                "auto_approve_domains": self.auto_approve_domains[:3],  # Limit domains
                "approval_thresholds": self.approval_thresholds.dict(minimal=True)
            }
        d = super().dict()
        if self.approval_thresholds:
            d["approval_thresholds"] = self.approval_thresholds.dict(minimal=minimal)
        return d

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

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            return {
                "profile_id": self.profile_id,
                "personality": self.personality.dict(minimal=True),
                "learning_style": self.learning_style.dict(minimal=True),
                "communication": self.communication.dict(minimal=True),
                "auto_approval": self.auto_approval.dict(minimal=True),
                "domains": {k: {"confidence": v["confidence"]} 
                          for k, v in list(self.domains.items())[:2]}  # Limit domains
            }
        d = super().dict()
        if self.personality:
            d["personality"] = self.personality.dict(minimal=minimal)
        if self.learning_style:
            d["learning_style"] = self.learning_style.dict(minimal=minimal)
        if self.communication:
            d["communication"] = self.communication.dict(minimal=minimal)
        if self.auto_approval:
            d["auto_approval"] = self.auto_approval.dict(minimal=minimal)
        return d

class ProfileUpdate(BaseModel):
    """Profile update request."""
    profile_id: str
    personality: Optional[BigFiveTraits] = None
    learning_style: Optional[LearningStyle] = None
    communication: Optional[CommunicationPreferences] = None
    auto_approval: Optional[AutoApprovalSettings] = None
    domains: Optional[Dict[str, Dict[str, float]]] = None

    def dict(self, minimal: bool = False) -> Dict:
        """Convert to dictionary with optional minimal data."""
        if minimal:
            d = {"profile_id": self.profile_id}
            if self.personality:
                d["personality"] = self.personality.dict(minimal=True)
            if self.learning_style:
                d["learning_style"] = self.learning_style.dict(minimal=True)
            if self.communication:
                d["communication"] = self.communication.dict(minimal=True)
            if self.auto_approval:
                d["auto_approval"] = self.auto_approval.dict(minimal=True)
            if self.domains:
                d["domains"] = {k: {"confidence": v["confidence"]} 
                              for k, v in list(self.domains.items())[:2]}  # Limit domains
            return d
        d = super().dict()
        if self.personality:
            d["personality"] = self.personality.dict(minimal=minimal)
        if self.learning_style:
            d["learning_style"] = self.learning_style.dict(minimal=minimal)
        if self.communication:
            d["communication"] = self.communication.dict(minimal=minimal)
        if self.auto_approval:
            d["auto_approval"] = self.auto_approval.dict(minimal=minimal)
        return d
