"""Unit tests for profile system components."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from nia.core.profiles.profile_types import (
    UserProfile,
    ProfileUpdate,
    BigFiveTraits,
    LearningStyle,
    CommunicationPreferences,
    AutoApprovalSettings,
    ApprovalThresholds
)
from nia.core.profiles.profile_manager import ProfileManager

@pytest.fixture
def mock_neo4j_store():
    """Create mock Neo4j store."""
    store = AsyncMock()
    store.query = AsyncMock()
    return store

@pytest.fixture
def profile_manager(mock_neo4j_store):
    """Create profile manager with mock store."""
    return ProfileManager(store=mock_neo4j_store)

@pytest.fixture
def sample_profile_data():
    """Create sample profile data."""
    return {
        "profile_id": "test_user",
        "personality": BigFiveTraits(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.6,
            agreeableness=0.9,
            neuroticism=0.3
        ),
        "learning_style": LearningStyle(
            visual=0.8,
            auditory=0.4,
            kinesthetic=0.6
        ),
        "communication": CommunicationPreferences(
            direct=0.7,
            detailed=0.8,
            formal=0.4
        ),
        "auto_approval": AutoApprovalSettings(
            auto_approve_domains=["professional"],
            approval_thresholds=ApprovalThresholds(
                task_creation=0.8,
                resource_access=0.9,
                domain_crossing=0.95
            ),
            restricted_operations=["delete", "modify_personal"]
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

@pytest.mark.asyncio
class TestProfileManager:
    """Test profile manager functionality."""

    async def test_create_profile(self, profile_manager, sample_profile_data, mock_neo4j_store):
        """Test profile creation."""
        # Setup mock
        mock_neo4j_store.query.return_value = []  # No existing profile

        # Create profile
        profile = await profile_manager.create_profile(
            profile_id=sample_profile_data["profile_id"],
            personality=sample_profile_data["personality"],
            learning_style=sample_profile_data["learning_style"],
            communication=sample_profile_data["communication"],
            auto_approval=sample_profile_data["auto_approval"]
        )

        # Verify profile
        assert profile.profile_id == sample_profile_data["profile_id"]
        assert profile.personality == sample_profile_data["personality"]
        assert profile.learning_style == sample_profile_data["learning_style"]
        assert profile.communication == sample_profile_data["communication"]
        assert profile.auto_approval == sample_profile_data["auto_approval"]

        # Verify store call
        mock_neo4j_store.query.assert_called_with(
            """
            CREATE (p:Profile)
            SET p = $profile
            """,
            {"profile": profile.dict()}
        )

    async def test_get_profile(self, profile_manager, sample_profile_data, mock_neo4j_store):
        """Test profile retrieval."""
        # Setup mock
        mock_neo4j_store.query.return_value = [{"p": sample_profile_data}]

        # Get profile
        profile = await profile_manager.get_profile(sample_profile_data["profile_id"])

        # Verify profile
        assert profile is not None
        assert profile.profile_id == sample_profile_data["profile_id"]
        assert profile.personality == sample_profile_data["personality"]
        assert profile.learning_style == sample_profile_data["learning_style"]

        # Verify store call
        mock_neo4j_store.query.assert_called_with(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            RETURN p
            """,
            {"profile_id": sample_profile_data["profile_id"]}
        )

    async def test_update_profile(self, profile_manager, sample_profile_data, mock_neo4j_store):
        """Test profile update."""
        # Setup mock
        mock_neo4j_store.query.side_effect = [
            [{"p": sample_profile_data}],  # First call for get_profile
            None  # Second call for update
        ]

        # Create update
        update = ProfileUpdate(
            profile_id=sample_profile_data["profile_id"],
            communication=CommunicationPreferences(
                direct=0.9,
                detailed=0.7,
                formal=0.8
            )
        )

        # Update profile
        updated = await profile_manager.update_profile(
            sample_profile_data["profile_id"],
            update
        )

        # Verify update
        assert updated is not None
        assert updated.profile_id == sample_profile_data["profile_id"]
        assert updated.communication == update.communication
        assert updated.personality == sample_profile_data["personality"]

    async def test_delete_profile(self, profile_manager, sample_profile_data, mock_neo4j_store):
        """Test profile deletion."""
        # Setup mock
        mock_neo4j_store.query.return_value = [{"deleted": 1}]

        # Delete profile
        result = await profile_manager.delete_profile(sample_profile_data["profile_id"])

        # Verify deletion
        assert result is True

        # Verify store call
        mock_neo4j_store.query.assert_called_with(
            """
            MATCH (p:Profile {profile_id: $profile_id})
            DELETE p
            RETURN count(p) as deleted
            """,
            {"profile_id": sample_profile_data["profile_id"]}
        )

    async def test_check_auto_approval(self, profile_manager, sample_profile_data, mock_neo4j_store):
        """Test auto-approval checking."""
        # Setup mock
        mock_neo4j_store.query.return_value = [{"p": sample_profile_data}]

        # Check auto-approval for different scenarios
        result = await profile_manager.check_auto_approval(
            sample_profile_data["profile_id"],
            "task_creation",
            "professional",
            0.9  # Above threshold
        )
        assert result is True

        result = await profile_manager.check_auto_approval(
            sample_profile_data["profile_id"],
            "delete",  # Restricted operation
            "professional",
            0.9
        )
        assert result is False

        result = await profile_manager.check_auto_approval(
            sample_profile_data["profile_id"],
            "task_creation",
            "personal",  # Non-auto-approved domain
            0.9
        )
        assert result is False

    async def test_domain_confidence(self, profile_manager, sample_profile_data, mock_neo4j_store):
        """Test domain confidence operations."""
        # Setup mock
        mock_neo4j_store.query.return_value = [{"p": sample_profile_data}]

        # Get confidence
        confidence = await profile_manager.get_domain_confidence(
            sample_profile_data["profile_id"],
            "professional"
        )
        assert confidence == 1.0

        # Update confidence
        success = await profile_manager.update_domain_confidence(
            sample_profile_data["profile_id"],
            "professional",
            0.8
        )
        assert success is True

        # Verify store calls
        assert mock_neo4j_store.query.call_count >= 2
