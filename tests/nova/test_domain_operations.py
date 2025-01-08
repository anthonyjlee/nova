"""Integration tests for domain operations and boundary enforcement."""

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
class TestDomainOperations:
    """Test domain operation functionality."""

    @pytest.mark.asyncio
    async def test_cross_domain_request(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test cross-domain operation request and approval."""
        request_data = {
            "content": "Access personal calendar for work meeting",
            "source_domain": "professional",
            "target_domain": "personal",
            "operation": {
                "type": "read",
                "resource": "calendar",
                "justification": "Schedule team meeting"
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

        async with TestContext(mem_sys, request_data["source_domain"]):
            # Test cross-domain request
            @with_vector_store_retry
            async def process_request():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["source_domain"],
                    cross_domain={
                        "target": request_data["target_domain"],
                        "operation": request_data["operation"]
                    }
                )

            result = await process_request()

            # Verify cross-domain request handling
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "cross_domain_request" in result.analytics
            assert result.analytics["cross_domain_request"]["requires_approval"]
            assert not result.analytics["cross_domain_request"]["auto_approved"]

    @pytest.mark.asyncio
    async def test_domain_boundary_enforcement(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test domain boundary enforcement."""
        request_data = {
            "content": "Direct personal data access attempt",
            "domain": "professional",
            "target": {
                "domain": "personal",
                "data": "contacts"
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
            # Test boundary enforcement
            @with_vector_store_retry
            async def process_attempt():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    target=request_data["target"]
                )

            result = await process_attempt()

            # Verify boundary enforcement
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "access_violation" in result.analytics
            assert result.analytics["access_violation"]["blocked"]
            assert "domain_boundary" in result.analytics["access_violation"]["reason"]

    @pytest.mark.asyncio
    async def test_domain_inheritance(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test domain inheritance for derived tasks."""
        request_data = {
            "content": "Create subtask",
            "domain": "professional",
            "task": {
                "type": "analysis",
                "subtasks": [
                    {"id": "parse", "type": "parsing"},
                    {"id": "analyze", "type": "analysis"},
                    {"id": "validate", "type": "validation"}
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
            # Test domain inheritance
            @with_vector_store_retry
            async def process_task():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    task=request_data["task"]
                )

            result = await process_task()

            # Verify domain inheritance
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "task_creation" in result.analytics
            assert result.analytics["task_creation"]["success"]
            
            # Verify subtask domains
            subtasks = result.analytics["task_creation"]["subtasks"]
            for subtask in subtasks:
                assert subtask["domain"] == request_data["domain"]
                assert subtask["inherited_domain"]
