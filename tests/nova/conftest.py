"""Test configuration for Nova's FastAPI server."""

import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

from tinytroupe.agent import TinyPerson

@pytest.fixture(autouse=True)
async def setup_test_environment(event_loop):
    """Set up test environment with proper event loop handling."""
    asyncio.set_event_loop(event_loop)
    
    # Reset TinyTroupe agent registry
    TinyPerson._agents = {}
    
    # Create mock response
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": """
{
    "analytics": {
        "key_metrics": [
            {
                "name": "Test Metric",
                "value": 0.8,
                "confidence": 0.9
            }
        ],
        "trends": [
            {
                "name": "Test Trend",
                "description": "Test trend description",
                "confidence": 0.85
            }
        ]
    },
    "insights": [
        {
            "type": "test_insight",
            "description": "Test insight description",
            "confidence": 0.8,
            "recommendations": ["Test recommendation"]
        }
    ]
}
"""
                }
            }
        ]
    }

    async def mock_analyze(*args, **kwargs):
        try:
            return await asyncio.wait_for(
                asyncio.create_task(mock_response_coro()),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Mock analyze timed out")
            return {
                "choices": [{
                    "message": {
                        "content": '{"error": "timeout"}'
                    }
                }]
            }

    async def mock_get_structured_completion(*args, **kwargs):
        try:
            return await asyncio.wait_for(
                asyncio.create_task(mock_response_coro()),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Mock completion timed out")
            return {
                "choices": [{
                    "message": {
                        "content": '{"error": "timeout"}'
                    }
                }]
            }

    async def mock_response_coro():
        return mock_response

    try:
        # Apply patches
        with patch("nia.nova.core.llm.LMStudioLLM.analyze", new=AsyncMock(side_effect=mock_analyze)), \
             patch("nia.nova.core.llm.LMStudioLLM.get_structured_completion", new=AsyncMock(side_effect=mock_get_structured_completion)):
            yield
    finally:
        # Clean up tasks with timeout
        try:
            pending = asyncio.all_tasks(event_loop)
            for task in pending:
                if not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=1.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

@pytest.fixture(autouse=True)
async def reset_connections():
    """Reset database connections before each test."""
    from nia.core.neo4j import reset_neo4j_driver
    from nia.core.vector import reset_vector_store
    
    try:
        await reset_neo4j_driver()
        await reset_vector_store()
        yield
    finally:
        # Ensure connections are reset even if test fails
        try:
            await reset_neo4j_driver()
            await reset_vector_store()
        except Exception as e:
            logger.error(f"Error resetting connections: {str(e)}")

@pytest.fixture
async def mock_analytics_agent():
    """Create a mock analytics agent with proper error handling."""
    agent = AsyncMock()
    
    async def process_with_timeout(*args, **kwargs):
        try:
            return await asyncio.wait_for(
                asyncio.create_task(agent.process_analytics(*args, **kwargs)),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Mock analytics processing timed out")
            from nia.nova.core.analytics import AnalyticsResult
            return AnalyticsResult(
                is_valid=False,
                analytics={},
                insights=[{"type": "error", "description": "Processing timed out"}],
                confidence=0.0
            )
    
    agent.process_analytics.side_effect = process_with_timeout
    return agent
