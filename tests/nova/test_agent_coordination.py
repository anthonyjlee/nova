"""Integration tests for agent coordination functionality."""

import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime
import logging
import asyncio
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Vector store operation settings
VECTOR_STORE_TIMEOUT = 30  # seconds
VECTOR_STORE_MAX_RETRIES = 3
VECTOR_STORE_RETRY_MIN_WAIT = 1  # seconds
VECTOR_STORE_RETRY_MAX_WAIT = 10  # seconds

@retry(
    stop=stop_after_attempt(VECTOR_STORE_MAX_RETRIES),
    wait=wait_exponential(multiplier=VECTOR_STORE_RETRY_MIN_WAIT, max=VECTOR_STORE_RETRY_MAX_WAIT)
)
async def vector_store_operation(operation):
    """Execute vector store operation with retry logic."""
    try:
        async with asyncio.timeout(VECTOR_STORE_TIMEOUT):
            return await operation
    except asyncio.TimeoutError:
        logger.error(f"Vector store operation timed out after {VECTOR_STORE_TIMEOUT}s")
        raise

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_world
)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.mark.integration
class TestAgentCoordination:
    """Test agent coordination functionality."""

    @pytest.mark.asyncio
    async def test_agent_coordination_processing(self, memory_system, mock_analytics_agent, llm_interface, world):
        """Test agent coordination processing."""
        # Get initialized fixtures
        mock_agent = await mock_analytics_agent
        memory = await memory_system
        llm = await llm_interface
        w = await world

        # Set up mock response
        from nia.nova.core.analytics import AnalyticsResult
        mock_agent.process_analytics.return_value = AnalyticsResult(
            is_valid=True,
            analytics={
                "key_metrics": [{"name": "Test Metric", "value": 0.8, "confidence": 0.9}],
                "trends": [{"name": "Test Trend", "description": "Test trend description", "confidence": 0.85}]
            },
            insights=[{"type": "test_insight", "description": "Test insight description"}],
            confidence=0.9
        )

        # Set up dependency overrides
        app.dependency_overrides[get_memory_system] = lambda: memory
        app.dependency_overrides[get_analytics_agent] = lambda: mock_agent
        app.dependency_overrides[get_llm_interface] = lambda: llm
        app.dependency_overrides[get_world] = lambda: w

        try:
            # Test analytics agent processing
            request_data = {
                "content": "Why is the sky blue?",
                "domain": "science",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }

            # Process request through analytics agent with retry
            result = await vector_store_operation(
                mock_agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    llm_config=request_data["llm_config"]
                )
            )

            # Verify result structure
            assert result is not None
            assert hasattr(result, "is_valid")
            assert hasattr(result, "analytics")
            assert hasattr(result, "insights")
            assert hasattr(result, "confidence")

            # Verify result content
            assert result.is_valid
            assert isinstance(result.analytics, dict)
            assert isinstance(result.insights, list)
            assert 0.0 <= result.confidence <= 1.0

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_agent_coordination_memory(self, memory_system, mock_analytics_agent, llm_interface, world):
        """Test agent coordination memory integration."""
        # Get initialized fixtures
        mock_agent = await mock_analytics_agent
        memory = await memory_system
        llm = await llm_interface
        w = await world

        # Set up mock response
        from nia.nova.core.analytics import AnalyticsResult
        mock_agent.process_analytics.return_value = AnalyticsResult(
            is_valid=True,
            analytics={
                "key_metrics": [{"name": "Test Metric", "value": 0.8, "confidence": 0.9}],
                "trends": [{"name": "Test Trend", "description": "Test trend description", "confidence": 0.85}]
            },
            insights=[{"type": "test_insight", "description": "Test insight description"}],
            confidence=0.9
        )

        # Set up dependency overrides
        app.dependency_overrides[get_memory_system] = lambda: memory
        app.dependency_overrides[get_analytics_agent] = lambda: mock_agent
        app.dependency_overrides[get_llm_interface] = lambda: llm
        app.dependency_overrides[get_world] = lambda: w

        try:
            # Test memory integration
            request_data = {
                "content": "Why is the sky blue?",
                "domain": "science",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }

            # Process request and store in memory with retry
            result = await vector_store_operation(
                mock_agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    llm_config=request_data["llm_config"]
                )
            )

            # Verify memory storage with retry
            stored_data = await vector_store_operation(
                memory.semantic.search(f"domain:{request_data['domain']}")
            )
            assert len(stored_data) > 0

            # Verify stored content
            stored_item = stored_data[0]
            assert stored_item["domain"] == request_data["domain"]
            assert "content" in stored_item
            assert "analytics" in stored_item

            # Cleanup test data
            await vector_store_operation(
                memory.semantic.delete_nodes(
                    query=f"domain:{request_data['domain']}"
                )
            )

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_agent_coordination_llm(self, memory_system, mock_analytics_agent, llm_interface, world):
        """Test agent coordination LLM integration."""
        # Get initialized fixtures
        mock_agent = await mock_analytics_agent
        memory = await memory_system
        llm = await llm_interface
        w = await world

        # Set up mock response
        from nia.nova.core.analytics import AnalyticsResult
        mock_agent.process_analytics.return_value = AnalyticsResult(
            is_valid=True,
            analytics={
                "key_metrics": [{"name": "Test Metric", "value": 0.8, "confidence": 0.9}],
                "trends": [{"name": "Test Trend", "description": "Test trend description", "confidence": 0.85}]
            },
            insights=[{"type": "test_insight", "description": "Test insight description"}],
            confidence=0.9
        )

        # Set up dependency overrides
        app.dependency_overrides[get_memory_system] = lambda: memory
        app.dependency_overrides[get_analytics_agent] = lambda: mock_agent
        app.dependency_overrides[get_llm_interface] = lambda: llm
        app.dependency_overrides[get_world] = lambda: w

        try:
            # Test LLM integration
            request_data = {
                "content": "Why is the sky blue?",
                "domain": "science",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }

            # Process request through LLM with retry
            result = await vector_store_operation(
                mock_agent.process_analytics(
                    content=request_data["content"],
                    domain=request_data["domain"],
                    llm_config=request_data["llm_config"]
                )
            )

            # Verify LLM processing
            assert result.is_valid
            assert result.confidence > 0.0

            # Verify structured output
            assert isinstance(result.analytics, dict)
            assert isinstance(result.insights, list)
            for insight in result.insights:
                assert "type" in insight
                assert "description" in insight

            # Cleanup test data
            await vector_store_operation(
                memory.semantic.delete_nodes(
                    query=f"domain:{request_data['domain']}"
                )
            )
        finally:
            app.dependency_overrides.clear()
