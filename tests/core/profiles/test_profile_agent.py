"""Unit tests for profile agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from nia.core.profiles.profile_agent import ProfileAgent
from nia.core.profiles.profile_types import (
    UserProfile,
    BigFiveTraits,
    LearningStyle,
    CommunicationPreferences,
    AutoApprovalSettings,
    ApprovalThresholds
)

@pytest.fixture
def mock_profile_manager():
    """Create mock profile manager."""
    manager = AsyncMock()
    return manager

@pytest.fixture
def profile_agent(mock_profile_manager):
    """Create profile agent with mock manager."""
    return ProfileAgent(profile_manager=mock_profile_manager)

@pytest.fixture
def sample_profile():
    """Create sample user profile."""
    return UserProfile(
        profile_id="test_user",
        personality=BigFiveTraits(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.6,
            agreeableness=0.9,
            neuroticism=0.3
        ),
        learning_style=LearningStyle(
            visual=0.8,
            auditory=0.4,
            kinesthetic=0.6
        ),
        communication=CommunicationPreferences(
            direct=0.7,
            detailed=0.8,
            formal=0.4
        ),
        auto_approval=AutoApprovalSettings(
            auto_approve_domains=["professional"],
            approval_thresholds=ApprovalThresholds(
                task_creation=0.8,
                resource_access=0.9,
                domain_crossing=0.95
            ),
            restricted_operations=["delete", "modify_personal"]
        ),
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )

@pytest.fixture
def sample_task():
    """Create sample task configuration."""
    return {
        "type": "analysis",
        "complexity": "high",
        "technical_depth": "detailed",
        "visualization": "enabled",
        "communication": "standard"
    }

@pytest.mark.asyncio
class TestProfileAgent:
    """Test profile agent functionality."""

    async def test_adapt_task_personality(self, profile_agent, mock_profile_manager, sample_profile, sample_task):
        """Test task adaptation based on personality."""
        # Setup mock
        mock_profile_manager.get_profile.return_value = sample_profile
        mock_profile_manager.get_domain_confidence.return_value = 0.9

        # Adapt task
        adapted = await profile_agent.adapt_task(
            profile_id=sample_profile.profile_id,
            task=sample_task,
            domain="professional"
        )

        # Verify personality-based adaptations
        assert adapted["granularity"] == "detailed"  # Based on high conscientiousness
        assert adapted["exploration_encouraged"] is True  # Based on high openness
        assert adapted["alternative_approaches"] is True
        assert adapted["collaboration_style"] == "independent"  # Based on moderate extraversion

    async def test_adapt_task_learning(self, profile_agent, mock_profile_manager, sample_profile, sample_task):
        """Test task adaptation based on learning style."""
        # Setup mock
        mock_profile_manager.get_profile.return_value = sample_profile
        mock_profile_manager.get_domain_confidence.return_value = 0.9

        # Adapt task
        adapted = await profile_agent.adapt_task(
            profile_id=sample_profile.profile_id,
            task=sample_task,
            domain="professional"
        )

        # Verify learning style adaptations
        assert adapted["visualization_preference"] == "high"  # Based on high visual preference
        assert adapted["diagram_complexity"] == "detailed"
        assert "include_audio" not in adapted  # Low auditory preference
        assert "interactive_elements" not in adapted  # Moderate kinesthetic preference

    async def test_adapt_task_communication(self, profile_agent, mock_profile_manager, sample_profile, sample_task):
        """Test task adaptation based on communication preferences."""
        # Setup mock
        mock_profile_manager.get_profile.return_value = sample_profile
        mock_profile_manager.get_domain_confidence.return_value = 0.9

        # Adapt task
        adapted = await profile_agent.adapt_task(
            profile_id=sample_profile.profile_id,
            task=sample_task,
            domain="professional"
        )

        # Verify communication adaptations
        assert adapted["communication_style"] == "direct"  # Based on high directness
        assert adapted["include_context"] is False
        assert adapted["tone"] == "casual"  # Based on low formality
        assert adapted["technical_level"] == "conversational"

    async def test_check_operation_approval(self, profile_agent, mock_profile_manager, sample_profile):
        """Test operation approval checking."""
        # Setup mock
        mock_profile_manager.check_auto_approval.side_effect = [True, False]

        # Test approved operation
        result = await profile_agent.check_operation_approval(
            profile_id=sample_profile.profile_id,
            operation="task_creation",
            domain="professional",
            confidence=0.9
        )
        assert result is True

        # Test rejected operation
        result = await profile_agent.check_operation_approval(
            profile_id=sample_profile.profile_id,
            operation="delete",
            domain="professional",
            confidence=0.9
        )
        assert result is False

    async def test_update_domain_confidence(self, profile_agent, mock_profile_manager, sample_profile):
        """Test domain confidence updates."""
        # Setup mock
        mock_profile_manager.update_domain_confidence.return_value = True

        # Test successful operation
        await profile_agent.update_domain_confidence(
            profile_id=sample_profile.profile_id,
            domain="professional",
            confidence=0.8,
            operation_success=True
        )
        mock_profile_manager.update_domain_confidence.assert_called_with(
            sample_profile.profile_id,
            "professional",
            0.9  # Increased confidence
        )

        # Test failed operation
        await profile_agent.update_domain_confidence(
            profile_id=sample_profile.profile_id,
            domain="professional",
            confidence=0.8,
            operation_success=False
        )
        mock_profile_manager.update_domain_confidence.assert_called_with(
            sample_profile.profile_id,
            "professional",
            0.6  # Decreased confidence
        )

    async def test_profile_not_found(self, profile_agent, mock_profile_manager, sample_task):
        """Test handling of missing profile."""
        # Setup mock
        mock_profile_manager.get_profile.return_value = None

        # Test task adaptation
        with pytest.raises(ValueError):
            await profile_agent.adapt_task(
                profile_id="nonexistent",
                task=sample_task,
                domain="professional"
            )

        # Test confidence update
        await profile_agent.update_domain_confidence(
            profile_id="nonexistent",
            domain="professional",
            confidence=0.8,
            operation_success=True
        )
        # Should log error but not raise exception
