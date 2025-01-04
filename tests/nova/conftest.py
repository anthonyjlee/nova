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
    # Set the event loop
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
        return mock_response

    async def mock_get_structured_completion(*args, **kwargs):
        return mock_response

    # Apply patches
    with patch("nia.nova.core.llm.LMStudioLLM.analyze", new=AsyncMock(side_effect=mock_analyze)), \
         patch("nia.nova.core.llm.LMStudioLLM.get_structured_completion", new=AsyncMock(side_effect=mock_get_structured_completion)):
        yield

    # Clean up any remaining connections
    try:
        for task in asyncio.all_tasks(event_loop):
            if not task.done():
                logger.debug(f"Cancelling task: {task.get_name()}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

@pytest.fixture(autouse=True)
async def reset_connections():
    """Reset database connections before each test."""
    from nia.memory.neo4j import reset_neo4j_driver
    from nia.memory.vector import reset_vector_store
    
    try:
        await reset_neo4j_driver()
        await reset_vector_store()
        yield
    finally:
        await reset_neo4j_driver()
        await reset_vector_store()
