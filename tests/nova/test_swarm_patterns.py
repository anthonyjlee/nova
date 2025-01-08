"""Integration tests for swarm pattern functionality."""

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
class TestSwarmPatterns:
    """Test swarm pattern functionality."""

    @pytest.mark.asyncio
    async def test_majority_voting(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test majority voting swarm pattern."""
        request_data = {
            "content": "Test majority voting",
            "domain": "test_science",
            "swarm_config": {
                "type": "majority_voting",
                "threshold": 0.6,
                "voting_timeout": 30.0,
                "allow_revotes": False
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
            # Test voting mechanism
            @with_vector_store_retry
            async def process_voting():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    swarm_config=request_data["swarm_config"]
                )

            result = await process_voting()

            # Verify voting results
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "voting_results" in result.analytics
            assert result.analytics["voting_results"]["threshold_met"]

    @pytest.mark.asyncio
    async def test_round_robin(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test round robin swarm pattern."""
        request_data = {
            "content": "Test round robin",
            "domain": "test_science",
            "swarm_config": {
                "type": "round_robin",
                "rotation_interval": 1.0,
                "fair_scheduling": True
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
            # Test task rotation
            @with_vector_store_retry
            async def process_rotation():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    swarm_config=request_data["swarm_config"]
                )

            result = await process_rotation()

            # Verify rotation results
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "rotation_metrics" in result.analytics
            assert result.analytics["rotation_metrics"]["fair_distribution"]

    @pytest.mark.asyncio
    async def test_graph_workflow(
        self,
        memory_system,
        mock_analytics_agent,
        llm_interface,
        world
    ):
        """Test graph workflow swarm pattern."""
        request_data = {
            "content": "Test graph workflow",
            "domain": "test_science",
            "swarm_config": {
                "type": "graph_workflow",
                "nodes": [
                    {"id": "parse", "agent": "parsing"},
                    {"id": "analyze", "agent": "analysis"},
                    {"id": "validate", "agent": "validation"}
                ],
                "edges": [
                    {"from": "parse", "to": "analyze"},
                    {"from": "analyze", "to": "validate"}
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
            # Test graph execution
            @with_vector_store_retry
            async def process_graph():
                return await agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    swarm_config=request_data["swarm_config"]
                )

            result = await process_graph()

            # Verify graph execution results
            assert result is not None
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert "graph_metrics" in result.analytics
            assert result.analytics["graph_metrics"]["execution_complete"]
            assert len(result.analytics["graph_metrics"]["node_results"]) == 3
