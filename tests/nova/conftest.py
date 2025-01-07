"""Test configuration for Nova's FastAPI server."""

import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch

logger = logging.getLogger(__name__)

@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()

from tinytroupe.agent import TinyPerson

@pytest.fixture(autouse=True)
async def setup_test_environment(event_loop):
    """Set up test environment with proper event loop handling."""
    # Reset TinyTroupe agent registry
    TinyPerson._agents = {}
    
    # Initialize Neo4j driver with the running event loop
    from neo4j import AsyncGraphDatabase
    from nia.core.neo4j.base_store import _drivers
    
    # Clear any existing drivers
    for key in list(_drivers.keys()):
        driver = _drivers[key]
        await driver.close()
        del _drivers[key]
    
    # Create new driver
    driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password"),
        max_connection_lifetime=3600
    )
    await driver.verify_connectivity()
    _drivers["bolt://localhost:7687:neo4j"] = driver
    
    try:
        yield
    finally:
        # Clean up driver
        for key in list(_drivers.keys()):
            driver = _drivers[key]
            await driver.close()
            del _drivers[key]
    
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

    async def mock_get_embedding(*args, **kwargs):
        # Return mock embedding vector of correct dimension
        return [0.1] * 384  # 384 is the expected embedding dimension

    async def mock_get_embeddings(*args, **kwargs):
        # Return mock embedding vectors for batch
        texts = args[1] if len(args) > 1 else kwargs.get('texts', [])
        return [[0.1] * 384 for _ in texts]

    try:
        # Apply patches
        with patch("nia.nova.core.llm.LMStudioLLM.analyze", new=AsyncMock(side_effect=mock_analyze)), \
             patch("nia.nova.core.llm.LMStudioLLM.get_structured_completion", new=AsyncMock(side_effect=mock_get_structured_completion)), \
             patch("nia.core.vector.embeddings.EmbeddingService.get_embedding", new=AsyncMock(side_effect=mock_get_embedding)), \
             patch("nia.core.vector.embeddings.EmbeddingService.get_embeddings", new=AsyncMock(side_effect=mock_get_embeddings)):
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

@pytest.fixture
async def world():
    """Create world instance for testing."""
    from nia.world.environment import NIAWorld
    return NIAWorld()

@pytest.fixture
async def memory_system(request):
    """Create real memory system for testing."""
    from nia.core.vector.vector_store import VectorStore
    from nia.core.vector.embeddings import EmbeddingService
    from nia.memory.two_layer import TwoLayerMemorySystem
    
    # Create vector store with connection details
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        embedding_service=embedding_service,
        host="localhost",
        port=6333
    )
    
    memory = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store=vector_store,
        llm=None
    )
    
    # Initialize connections
    await memory.initialize()
    
    # Create test collections with unique names for isolation
    if hasattr(memory.episodic.store, 'ensure_collection'):
        await memory.episodic.store.ensure_collection("test_demo_episodic")
    
    # Clean up on test completion
    async def cleanup():
        await cleanup_memory(memory)
    request.addfinalizer(lambda: asyncio.get_event_loop().run_until_complete(cleanup()))
    
    return memory

async def cleanup_memory(memory):
    """Clean up memory system resources."""
    try:
        # Clean up Neo4j test data
        await memory.semantic.run_query(
            "MATCH (n) WHERE n.domain = 'test' DETACH DELETE n"
        )
        
        # Clean up vector store test data
        if hasattr(memory.episodic.store, 'delete_collection'):
            await memory.episodic.store.delete_collection()
        
        # Close connections
        await memory.cleanup()
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
