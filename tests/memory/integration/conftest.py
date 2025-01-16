"""Tests for Nova endpoints."""

import pytest
import logging
import asyncio
from fastapi import FastAPI
import httpx
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

# Import pytest-asyncio event loop fixture
pytest_plugins = ('pytest_asyncio',)

from nia.nova.core.nova_endpoints import nova_router
from nia.world.world import World, NIAWorld
from nia.agents.tiny_factory import TinyFactory
from nia.agents.specialized.meta_agent import MetaAgent
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.memory.vector_store import VectorStore
from nia.core.feature_flags import FeatureFlags
from nia.core.neo4j.base_store import Neo4jBaseStore

# Configure logging
LOGS_DIR = Path("logs/tests")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"test_nova_endpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configure logger - file only, no console output
logger = logging.getLogger("test-nova-endpoints")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent propagation to root logger

@pytest_asyncio.fixture
async def mock_vector_store() -> AsyncMock:
    """Mock vector store fixture."""
    mock = AsyncMock(spec=VectorStore)
    mock.initialize = AsyncMock(return_value=None)
    mock.store_vector = AsyncMock(return_value=None)
    mock.search_vectors = AsyncMock(return_value=[])
    mock.inspect_collection = AsyncMock(return_value=None)
    mock.id = "vector-store-id"
    mock.name = "vector-store"
    mock.type = "vector-store"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "memory"
    mock.capabilities = ["vector-store"]
    mock.metadata = {}
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    return mock

@pytest_asyncio.fixture
async def mock_world() -> AsyncMock:
    """Mock world fixture."""
    mock = AsyncMock(spec=World)
    mock.initialize = AsyncMock(return_value=None)
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    mock.execute_action = AsyncMock(return_value={"status": "success"})
    mock.id = "world-id"
    mock.name = "world"
    mock.type = "world"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "world"
    mock.capabilities = ["world"]
    mock.metadata = {}
    return mock

@pytest_asyncio.fixture
async def mock_tiny_factory() -> AsyncMock:
    """Mock tiny factory fixture."""
    mock = AsyncMock(spec=TinyFactory)
    mock.initialize = AsyncMock(return_value=None)
    mock.create_agent = AsyncMock(return_value=MagicMock(
        id="test-agent-id",
        name="test-agent",
        type="test",
        status="active",
        episodic=True,
        domain="test-domain",
        capabilities=["test"],
        metadata={},
        initialize=AsyncMock(return_value=None),
        process=AsyncMock(return_value={"content": "test", "metadata": {}}),
        get_state=AsyncMock(return_value={}),
        update_state=AsyncMock(return_value=None)
    ))
    mock.id = "tiny-factory-id"
    mock.name = "tiny-factory"
    mock.type = "factory"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "factory"
    mock.capabilities = ["factory"]
    mock.metadata = {}
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    return mock

@pytest_asyncio.fixture
async def mock_meta_agent_with_deps(mock_world: AsyncMock, mock_tiny_factory: AsyncMock) -> AsyncMock:
    """Create meta agent fixture with dependencies."""
    mock = AsyncMock(spec=MetaAgent)
    mock.initialize = AsyncMock(return_value=None)
    mock.process_interaction = AsyncMock(return_value={
        "content": "test response",
        "metadata": {
            "agent_actions": [],
            "initialization_sequence": [],
            "initialization_errors": {}
        }
    })
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    mock.id = "meta-agent-id"
    mock.name = "meta-agent"
    mock.type = "meta"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "professional"
    mock.capabilities = ["team_coordination", "cognitive_processing", "task_management"]
    mock.metadata = {
        "agent_actions": [],
        "initialization_sequence": [],
        "initialization_errors": {}
    }
    mock.memory_system = None
    mock.world = mock_world
    mock.attributes = None
    mock.factory = mock_tiny_factory
    mock.initialization_sequence = []
    mock.agent_dependencies = {}
    mock.initialization_errors = {}
    await mock.initialize()
    return mock

@pytest_asyncio.fixture
async def mock_meta_agent_no_deps() -> AsyncMock:
    """Create meta agent fixture without dependencies."""
    mock = AsyncMock(spec=MetaAgent)
    mock.initialize = AsyncMock(return_value=None)
    mock.process_interaction = AsyncMock(return_value={"content": "test response", "metadata": {"agent_actions": [], "initialization_sequence": [], "initialization_errors": {}}})
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    mock.id = "meta-agent-no-deps-id"
    mock.name = "meta-agent-no-deps"
    mock.type = "meta"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "professional"
    mock.capabilities = ["team_coordination", "cognitive_processing", "task_management"]
    mock.metadata = {"agent_actions": [], "initialization_sequence": [], "initialization_errors": {}}
    mock.memory_system = None
    mock.world = None
    mock.attributes = None
    mock.factory = None
    mock.initialization_sequence = []
    mock.agent_dependencies = {}
    mock.initialization_errors = {}
    await mock.initialize()
    return mock

@pytest_asyncio.fixture
async def mock_memory_system(mock_vector_store: AsyncMock) -> AsyncMock:
    """Mock memory system fixture."""
    mock = AsyncMock(spec=TwoLayerMemorySystem)
    mock.initialize = AsyncMock(return_value=None)
    mock.store = AsyncMock(return_value=None)
    mock.search = AsyncMock(return_value=[])
    mock.vector_store = mock_vector_store
    mock.id = "memory-system-id"
    mock.name = "memory-system"
    mock.type = "memory"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "memory"
    mock.capabilities = ["memory"]
    mock.metadata = {}
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    return mock

@pytest_asyncio.fixture(name="test_app")
async def test_app_fixture(
    mock_tiny_factory: AsyncMock,
    mock_world: AsyncMock,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> FastAPI:
    """Create and configure FastAPI test application."""
    logger.info("Setting up test app")
    from nia.nova.core import dependencies

    tf = await mock_tiny_factory
    w = await mock_world
    ma = await mock_meta_agent_with_deps
    ms = await mock_memory_system

    app = FastAPI()
    app.dependency_overrides = {
        dependencies.get_tiny_factory: lambda: tf,
        dependencies.get_world: lambda: w,
        dependencies.get_meta_agent: lambda: ma,
        dependencies.get_memory_system: lambda: ms
    }
    app.include_router(nova_router)
    return app

@pytest_asyncio.fixture(name="async_client")
async def async_client_fixture(test_app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async test client."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_initial_processing(
    async_client: httpx.AsyncClient,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> None:
    """Test initial processing phase."""
    logger.info("Testing initial processing phase")
    response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "test query",
            "workspace": "personal"
        }
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response content: {response.json()}")

    logger.info("Verifying initial processing assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()

    assert "threadId" in response_data, "Response should have threadId"
    assert "message" in response_data, "Response should have message"
    assert "agent_actions" in response_data, "Response should have agent_actions"

    message = response_data["message"]
    assert "id" in message, "Message should have id"
    assert "content" in message, "Message should have content"
    assert "sender_type" in message, "Message should have sender_type"
    assert message["sender_id"] == "nova", "Sender ID should be nova"
    assert "timestamp" in message, "Message should have timestamp"
    assert "metadata" in message, "Message should have metadata"

    assert message["sender_type"] == "agent", "Sender type should be agent"

    metadata = message["metadata"]
    assert "agent_actions" in metadata, "Metadata should have agent_actions"

    await mock_meta_agent_with_deps.process_interaction.assert_called_once()
    await mock_memory_system.store.assert_called_once()

@pytest.mark.asyncio
async def test_task_detection(
    async_client: httpx.AsyncClient,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> None:
    """Test task detection phase."""
    logger.info("Testing task detection phase")

    response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "create a test",
            "workspace": "personal"
        }
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response content: {response.json()}")

    logger.info("Verifying task detection assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()

    assert "threadId" in response_data, "Response should have threadId"
    assert "message" in response_data, "Response should have message"
    assert "agent_actions" in response_data, "Response should have agent_actions"

    message = response_data["message"]
    assert "id" in message, "Message should have id"
    assert "content" in message, "Message should have content"
    assert "sender_type" in message, "Message should have sender_type"
    assert message["sender_id"] == "nova", "Sender ID should be nova"
    assert "timestamp" in message, "Message should have timestamp"
    assert "metadata" in message, "Message should have metadata"

    assert message["sender_type"] == "agent", "Sender type should be agent"

    metadata = message["metadata"]
    assert "agent_actions" in metadata, "Metadata should have agent_actions"

    await mock_meta_agent_with_deps.process_interaction.assert_called_once()
    await mock_memory_system.store.assert_called_once()

@pytest.mark.asyncio
async def test_schema_validation_failure(async_client: httpx.AsyncClient) -> None:
    """Test handling of schema validation failure."""
    logger.info("Testing schema validation failure")

    response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "test query",
            "workspace": "invalid"  # Invalid workspace value
        }
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response content: {response.json()}")

    logger.info("Verifying schema validation failure assertions")
    assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"
    response_data = response.json()
    assert "detail" in response_data, "Response should have validation error details"

@pytest.mark.asyncio
async def test_meta_agent_no_dependencies(
    async_client: httpx.AsyncClient,
    mock_meta_agent_no_deps: AsyncMock
) -> None:
    """Test MetaAgent functioning without dependencies."""
    logger.info("Testing MetaAgent without dependencies")

    ma = await mock_meta_agent_no_deps
    assert ma.memory_system is None, "MetaAgent should have no memory system"
    assert ma.world is None, "MetaAgent should have no world"
    assert ma.attributes is None, "MetaAgent should have no attributes"

    response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "simple query",
            "workspace": "personal"
        }
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response content: {response.json()}")

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()

    assert "threadId" in response_data, "Response should have threadId"
    assert "message" in response_data, "Response should have message"
    assert "agent_actions" in response_data, "Response should have agent_actions"

    message = response_data["message"]
    assert "id" in message, "Message should have id"
    assert "content" in message, "Message should have content"
    assert "sender_type" in message, "Message should have sender_type"
    assert message["sender_id"] == "nova", "Sender ID should be nova"
    assert "timestamp" in message, "Message should have timestamp"
    assert "metadata" in message, "Message should have metadata"

    assert message["sender_type"] == "agent", "Sender type should be agent"

    metadata = message["metadata"]
    assert "agent_actions" in metadata, "Metadata should have agent_actions"

    await ma.process_interaction.assert_called_once()

@pytest.mark.asyncio
async def test_initialization_error_handling(
    async_client: httpx.AsyncClient,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock,
    mock_world: AsyncMock
) -> None:
    """Test error handling during initialization."""
    logger.info("Testing initialization error handling")

    ma = await mock_meta_agent_with_deps
    ms = await mock_memory_system
    w = await mock_world

    ms.initialize.side_effect = Exception("Simulated memory system error")

    response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "test initialization errors",
            "workspace": "personal",
            "debug_flags": {
                "trace_initialization": True,
                "trace_dependencies": True,
                "simulate_errors": {
                    "memory_system": True
                }
            }
        }
    )

    assert response.status_code == 422, "Should return 422 when agent initialization fails"
    error_data = response.json()

    assert "detail" in error_data, "Should include error details"
    assert isinstance(error_data["detail"], list), "Error details should be a list"
    assert len(error_data["detail"]) > 0, "Should include error messages"

    ms.initialize.side_effect = None

    recovery_response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "test recovery",
            "workspace": "personal",
            "debug_flags": {
                "trace_initialization": True,
                "trace_dependencies": True
            }
        }
    )

    assert recovery_response.status_code == 200, "Should recover after initialization errors"
    recovery_data = recovery_response.json()

    assert "threadId" in recovery_data, "Response should have threadId"
    assert "message" in recovery_data, "Response should have message"
    assert "agent_actions" in recovery_data, "Response should have agent_actions"

    message = recovery_data["message"]
    assert "id" in message, "Message should have id"
    assert "content" in message, "Message should have content"
    assert "sender_type" in message, "Message should have sender_type"
    assert "sender_id" in message, "Message should have sender_id"
    assert "timestamp" in message, "Message should have timestamp"
    assert "metadata" in message, "Message should have metadata"

    assert message["sender_type"] == "agent", "Sender type should be agent"
    assert message["sender_id"] == "nova", "Sender ID should be nova"

    metadata = recovery_data["metadata"]
    assert "agent_actions" in metadata, "Metadata should have agent_actions"
    assert "debug_info" in metadata, "Metadata should have debug_info"

    debug_info = metadata["debug_info"]
    assert "initialization_sequence" in debug_info, "Debug info should have initialization sequence"
    assert "agent_dependencies" in debug_info, "Debug info should have agent dependencies"

    await ms.initialize.assert_called()
    await w.initialize.assert_called()
    await ma.initialize.assert_called()

@pytest.mark.asyncio
async def test_debug_flags(
    async_client: httpx.AsyncClient,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> None:
    """Test debug flags functionality."""
    logger.info("Testing debug flags")
    response = await async_client.post("/api/nova/ask",
        headers={"X-API-Key": "test-key"},
        json={
            "content": "test debug flags",
            "workspace": "personal",
            "debug_flags": {
                "trace_initialization": True,
                "trace_dependencies": True
            }
        }
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response content: {response.json()}")

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    response_data = response.json()

    assert "threadId" in response_data, "Response should have threadId"
    assert "message" in response_data, "Response should have message"
    assert "agent_actions" in response_data, "Response should have agent_actions"

    message = response_data["message"]
    assert "metadata" in message, "Message should have metadata"

    metadata = message["metadata"]
    assert "debug_info" in metadata, "Metadata should have debug_info"

    debug_info = metadata["debug_info"]
    assert "initialization_sequence" in debug_info, "Debug info should have initialization sequence"
    assert "agent_dependencies" in debug_info, "Debug info should have agent dependencies"

    await mock_meta_agent_with_deps.process_interaction.assert_called_once()
