"""Integration tests for user profile system."""

import pytest
from fastapi.testclient import TestClient
import logging
from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_world
)
from tests.nova.test_utils import (
    with_vector_store_retry,
    TestContext,
    VectorStoreError
)

logger = logging.getLogger(__name__)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.mark.integration
class TestUserProfile:
    """Test user profile functionality."""

    @pytest.mark.asyncio
    async def test_psychometric_questionnaire(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test psychometric questionnaire submission and analysis."""
        request_data = {
            "content": "Submit questionnaire",
            "domain": "personal",
            "questionnaire": {
                "big_five": {
                    "openness": 0.8,
                    "conscientiousness": 0.7,
                    "extraversion": 0.6,
                    "agreeableness": 0.9,
                    "neuroticism": 0.3
                },
                "learning_style": {
                    "visual": 0.8,
                    "auditory": 0.4,
                    "kinesthetic": 0.6
                },
                "communication": {
                    "direct": 0.7,
                    "detailed": 0.8,
                    "formal": 0.4
                }
            }
        }

        # Get memory system from fixture
        mem_sys = await memory_system
        
        # Get dependencies
        agent = await mock_analytics_agent
        interface = await llm_interface
        
        # Set up dependency overrides
        app.dependency_overrides[get_memory_system] = lambda: mem_sys
        app.dependency_overrides[get_analytics_agent] = lambda: agent
        app.dependency_overrides[get_llm_interface] = lambda: interface
        app.dependency_overrides[get_world] = lambda: world

        async with TestContext(mem_sys, request_data["domain"]):
            # Test questionnaire submission
            @with_vector_store_retry
            async def process_questionnaire():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    questionnaire=request_data["questionnaire"]
                )

            result = await process_questionnaire()

            # Verify questionnaire processing
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "profile_creation" in result.analytics
            assert result.analytics["profile_creation"]["success"]
            assert "personality_insights" in result.analytics
            assert "learning_preferences" in result.analytics
            assert "communication_style" in result.analytics

    @pytest.mark.asyncio
    async def test_profile_based_adaptation(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test system adaptation based on user profile."""
        request_data = {
            "content": "Complex technical task",
            "domain": "professional",
            "profile_id": "test_user",
            "task": {
                "type": "analysis",
                "complexity": "high",
                "technical_depth": "detailed"
            }
        }

        # Get memory system from fixture
        mem_sys = await memory_system
        
        # Get dependencies
        agent = await mock_analytics_agent
        interface = await llm_interface
        
        # Set up dependency overrides
        app.dependency_overrides[get_memory_system] = lambda: mem_sys
        app.dependency_overrides[get_analytics_agent] = lambda: agent
        app.dependency_overrides[get_llm_interface] = lambda: interface
        app.dependency_overrides[get_world] = lambda: world

        async with TestContext(mem_sys, request_data["domain"]):
            # Test profile-based adaptation
            @with_vector_store_retry
            async def process_task():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    profile_id=request_data["profile_id"],
                    task=request_data["task"]
                )

            result = await process_task()

            # Verify profile-based adaptations
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "task_adaptation" in result.analytics
            assert result.analytics["task_adaptation"]["profile_applied"]
            
            # Verify specific adaptations
            adaptations = result.analytics["task_adaptation"]["adaptations"]
            assert "granularity" in adaptations
            assert "communication_style" in adaptations
            assert "visualization_preference" in adaptations

    @pytest.mark.asyncio
    async def test_auto_approval_settings(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test auto-approval settings management."""
        request_data = {
            "content": "Update auto-approval settings",
            "domain": "professional",
            "profile_id": "test_user",
            "settings": {
                "auto_approve_domains": ["professional"],
                "approval_thresholds": {
                    "task_creation": 0.8,
                    "resource_access": 0.9,
                    "domain_crossing": 0.95
                },
                "restricted_operations": [
                    "delete",
                    "modify_personal"
                ]
            }
        }

        # Get memory system from fixture
        mem_sys = await memory_system
        
        # Get dependencies
        agent = await mock_analytics_agent
        interface = await llm_interface
        
        # Set up dependency overrides
        app.dependency_overrides[get_memory_system] = lambda: mem_sys
        app.dependency_overrides[get_analytics_agent] = lambda: agent
        app.dependency_overrides[get_llm_interface] = lambda: interface
        app.dependency_overrides[get_world] = lambda: world

        async with TestContext(mem_sys, request_data["domain"]):
            # Test settings update
            @with_vector_store_retry
            async def update_settings():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    profile_id=request_data["profile_id"],
                    settings=request_data["settings"]
                )

            result = await update_settings()

            # Verify settings update
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "settings_update" in result.analytics
            assert result.analytics["settings_update"]["success"]
            
            # Verify specific settings
            settings = result.analytics["settings_update"]["current_settings"]
            assert "auto_approve_domains" in settings
            assert "approval_thresholds" in settings
            assert "restricted_operations" in settings
