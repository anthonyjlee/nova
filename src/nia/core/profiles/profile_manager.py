"""Profile management system implementation."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from nia.core.profiles.profile_types import (
    UserProfile,
    ProfileUpdate,
    BigFiveTraits,
    LearningStyle,
    CommunicationPreferences,
    AutoApprovalSettings
)
from nia.core.neo4j.neo4j_store import Neo4jMemoryStore

logger = logging.getLogger(__name__)

class ProfileManager:
    """Manages user profiles in Neo4j."""

    def __init__(self, store: Neo4jMemoryStore):
        """Initialize profile manager.
        
        Args:
            store: Neo4j store for profile persistence
        """
        self.store = store

    async def create_profile(
        self,
        profile_id: str,
        personality: BigFiveTraits,
        learning_style: LearningStyle,
        communication: CommunicationPreferences,
        auto_approval: AutoApprovalSettings
    ) -> UserProfile:
        """Create new user profile.
        
        Args:
            profile_id: Unique identifier for profile
            personality: Big Five personality traits
            learning_style: Learning style preferences
            communication: Communication preferences
            auto_approval: Auto-approval settings

        Returns:
            Created user profile

        Raises:
            ValueError: If profile already exists
        """
        # Check if profile exists
        existing = await self.store.query(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            RETURN p
            """,
            {"profile_id": profile_id}
        )
        if existing:
            raise ValueError(f"Profile {profile_id} already exists")

        # Create profile
        now = datetime.now(timezone.utc).isoformat()
        profile = UserProfile(
            profile_id=profile_id,
            personality=personality,
            learning_style=learning_style,
            communication=communication,
            auto_approval=auto_approval,
            created_at=now,
            updated_at=now
        )

        # Store in Neo4j with minimal data
        await self.store.query(
            """
            CREATE (p:Profile)
            SET p = $profile
            """,
            {"profile": profile.dict(minimal=True)}
        )

        return profile

    async def get_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Get user profile by ID.
        
        Args:
            profile_id: Profile identifier

        Returns:
            User profile if found, None otherwise
        """
        result = await self.store.query(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            RETURN p
            """,
            {"profile_id": profile_id}
        )
        if not result:
            return None

        profile_data = result[0]["p"]
        # Reconstruct full profile from minimal data
        return UserProfile(
            profile_id=profile_data["profile_id"],
            personality=BigFiveTraits(**profile_data["personality"]),
            learning_style=LearningStyle(**profile_data["learning_style"]),
            communication=CommunicationPreferences(**profile_data["communication"]),
            auto_approval=AutoApprovalSettings(**profile_data["auto_approval"]),
            domains=profile_data.get("domains", {
                "professional": {"confidence": 1.0},
                "personal": {"confidence": 1.0}
            }),
            created_at=profile_data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=profile_data.get("updated_at", datetime.now(timezone.utc).isoformat())
        )

    async def update_profile(
        self,
        profile_id: str,
        update: ProfileUpdate
    ) -> Optional[UserProfile]:
        """Update existing user profile.
        
        Args:
            profile_id: Profile identifier
            update: Profile update data

        Returns:
            Updated profile if found, None otherwise
        """
        # Get current profile
        current = await self.get_profile(profile_id)
        if not current:
            return None

        # Apply updates
        update_dict = update.dict(exclude_unset=True)
        profile_dict = current.dict()
        profile_dict.update(update_dict)
        profile_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Create updated profile
        updated_profile = UserProfile(**profile_dict)

        # Update in Neo4j with minimal data
        await self.store.query(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            SET p = $profile
            """,
            {
                "profile_id": profile_id,
                "profile": updated_profile.dict(minimal=True)
            }
        )

        return updated_profile

    async def delete_profile(self, profile_id: str) -> bool:
        """Delete user profile.
        
        Args:
            profile_id: Profile identifier

        Returns:
            True if profile was deleted, False if not found
        """
        result = await self.store.query(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            DELETE p
            RETURN count(p) as deleted
            """,
            {"profile_id": profile_id}
        )
        return result[0]["deleted"] > 0

    async def list_profiles(
        self,
        domain: Optional[str] = None
    ) -> List[UserProfile]:
        """List user profiles, optionally filtered by domain.
        
        Args:
            domain: Optional domain to filter by

        Returns:
            List of matching profiles
        """
        query = """
        MATCH (p:Profile)
        WHERE $domain IS NULL OR $domain IN keys(p.domains)
        RETURN p
        """
        result = await self.store.query(query, {"domain": domain})
        return [await self.get_profile(r["p"]["profile_id"]) for r in result]

    async def get_domain_confidence(
        self,
        profile_id: str,
        domain: str
    ) -> float:
        """Get confidence score for domain access.
        
        Args:
            profile_id: Profile identifier
            domain: Domain to check

        Returns:
            Confidence score between 0 and 1

        Raises:
            ValueError: If profile not found
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        return profile.domains.get(domain, {}).get("confidence", 0.0)

    async def update_domain_confidence(
        self,
        profile_id: str,
        domain: str,
        confidence: float
    ) -> bool:
        """Update confidence score for domain access.
        
        Args:
            profile_id: Profile identifier
            domain: Domain to update
            confidence: New confidence score

        Returns:
            True if updated, False if profile not found
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            return False

        # Update domain confidence
        if domain not in profile.domains:
            profile.domains[domain] = {}
        profile.domains[domain]["confidence"] = confidence
        profile.updated_at = datetime.now(timezone.utc).isoformat()

        # Update in Neo4j with minimal data
        await self.store.query(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            SET p = $profile
            """,
            {
                "profile_id": profile_id,
                "profile": profile.dict(minimal=True)
            }
        )

        return True

    async def check_auto_approval(
        self,
        profile_id: str,
        operation: str,
        domain: str,
        confidence: float
    ) -> bool:
        """Check if operation can be auto-approved.
        
        Args:
            profile_id: Profile identifier
            operation: Operation type
            domain: Target domain
            confidence: Operation confidence score

        Returns:
            True if operation can be auto-approved

        Raises:
            ValueError: If profile not found
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        # Check if operation is restricted
        if operation in profile.auto_approval.restricted_operations:
            return False

        # Check if domain is auto-approved
        if domain not in profile.auto_approval.auto_approve_domains:
            return False

        # Check confidence threshold
        threshold = profile.auto_approval.approval_thresholds
        if operation == "task_creation":
            return confidence >= threshold.task_creation
        elif operation == "resource_access":
            return confidence >= threshold.resource_access
        elif operation == "domain_crossing":
            return confidence >= threshold.domain_crossing
        else:
            return False
