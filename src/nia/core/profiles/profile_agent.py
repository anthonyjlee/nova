"""Profile agent for handling profile-based adaptations."""

import logging
from typing import Dict, Any, Optional

from nia.agents.base import BaseAgent
from nia.core.profiles.profile_manager import ProfileManager
from nia.core.profiles.profile_types import (
    UserProfile,
    BigFiveTraits,
    LearningStyle,
    CommunicationPreferences,
    AutoApprovalSettings
)

logger = logging.getLogger(__name__)

class ProfileAgent(BaseAgent):
    """Agent for managing user profiles and adaptations."""

    def __init__(self, profile_manager: ProfileManager):
        """Initialize profile agent.
        
        Args:
            profile_manager: Profile management system
        """
        super().__init__(agent_type="profile")
        self.profile_manager = profile_manager

    async def adapt_task(
        self,
        profile_id: str,
        task: Dict[str, Any],
        domain: str
    ) -> Dict[str, Any]:
        """Adapt task based on user profile.
        
        Args:
            profile_id: User profile identifier
            task: Task configuration
            domain: Task domain

        Returns:
            Adapted task configuration

        Raises:
            ValueError: If profile not found
        """
        # Get user profile
        profile = await self.profile_manager.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        # Apply personality-based adaptations
        task = await self._adapt_for_personality(task, profile.personality)
        
        # Apply learning style adaptations
        task = await self._adapt_for_learning(task, profile.learning_style)
        
        # Apply communication adaptations
        task = await self._adapt_for_communication(task, profile.communication)

        # Add domain confidence
        confidence = await self.profile_manager.get_domain_confidence(profile_id, domain)
        task["domain_confidence"] = confidence

        return task

    async def _adapt_for_personality(
        self,
        task: Dict[str, Any],
        personality: BigFiveTraits
    ) -> Dict[str, Any]:
        """Apply personality-based adaptations.
        
        Args:
            task: Task configuration
            personality: User's personality traits

        Returns:
            Adapted task configuration
        """
        adapted = task.copy()

        # Adjust task granularity based on conscientiousness (>= 0.7 for detailed)
        if personality.conscientiousness >= 0.7:
            adapted["granularity"] = "detailed"
        elif personality.conscientiousness < 0.3:
            adapted["granularity"] = "high-level"
        else:
            adapted["granularity"] = "balanced"

        # Adjust exploration based on openness
        if personality.openness > 0.7:
            adapted["exploration_encouraged"] = True
            adapted["alternative_approaches"] = True
        else:
            adapted["exploration_encouraged"] = False
            adapted["alternative_approaches"] = False

        # Adjust collaboration based on extraversion
        if personality.extraversion > 0.7:
            adapted["collaboration_style"] = "interactive"
        else:
            adapted["collaboration_style"] = "independent"

        return adapted

    async def _adapt_for_learning(
        self,
        task: Dict[str, Any],
        learning: LearningStyle
    ) -> Dict[str, Any]:
        """Apply learning style adaptations.
        
        Args:
            task: Task configuration
            learning: User's learning style

        Returns:
            Adapted task configuration
        """
        adapted = task.copy()

        # Determine primary learning style
        styles = {
            "visual": learning.visual,
            "auditory": learning.auditory,
            "kinesthetic": learning.kinesthetic
        }
        primary_style = max(styles.items(), key=lambda x: x[1])[0]

        # Adjust content presentation
        if primary_style == "visual":
            adapted["visualization_preference"] = "high"
            adapted["diagram_complexity"] = "detailed"
        elif primary_style == "auditory":
            adapted["include_audio"] = True
            adapted["verbal_explanations"] = "detailed"
        else:  # kinesthetic
            adapted["interactive_elements"] = True
            adapted["hands_on_examples"] = True

        return adapted

    async def _adapt_for_communication(
        self,
        task: Dict[str, Any],
        communication: CommunicationPreferences
    ) -> Dict[str, Any]:
        """Apply communication style adaptations.
        
        Args:
            task: Task configuration
            communication: User's communication preferences

        Returns:
            Adapted task configuration
        """
        adapted = task.copy()

        # Adjust communication style (>= 0.7 for direct)
        if communication.direct >= 0.7:
            adapted["communication_style"] = "direct"
            adapted["include_context"] = False
        else:
            adapted["communication_style"] = "detailed"
            adapted["include_context"] = True

        # Adjust formality
        if communication.formal > 0.7:
            adapted["tone"] = "formal"
            adapted["technical_level"] = "professional"
        else:
            adapted["tone"] = "casual"
            adapted["technical_level"] = "conversational"

        return adapted

    async def check_operation_approval(
        self,
        profile_id: str,
        operation: str,
        domain: str,
        confidence: float
    ) -> bool:
        """Check if operation can be auto-approved.
        
        Args:
            profile_id: User profile identifier
            operation: Operation type
            domain: Target domain
            confidence: Operation confidence score

        Returns:
            True if operation can be auto-approved
        """
        try:
            return await self.profile_manager.check_auto_approval(
                profile_id,
                operation,
                domain,
                confidence
            )
        except ValueError:
            logger.error(f"Failed to check approval for profile {profile_id}")
            return False

    async def update_domain_confidence(
        self,
        profile_id: str,
        domain: str,
        confidence: float,
        operation_success: bool
    ) -> None:
        """Update domain confidence based on operation outcome.
        
        Args:
            profile_id: User profile identifier
            domain: Domain to update
            confidence: Current confidence score
            operation_success: Whether operation succeeded
        """
        try:
            # Adjust confidence based on operation outcome
            if operation_success:
                # Increase confidence, max 1.0
                new_confidence = min(confidence + 0.1, 1.0)
            else:
                # Decrease confidence, min 0.0, use round to avoid floating point issues
                new_confidence = round(max(confidence - 0.2, 0.0), 1)

            await self.profile_manager.update_domain_confidence(
                profile_id,
                domain,
                new_confidence
            )
        except ValueError:
            logger.error(f"Failed to update confidence for profile {profile_id}")
