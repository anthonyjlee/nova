"""Tests for Nova endpoints."""

import pytest
import logging
import asyncio
from fastapi import FastAPI
import httpx
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

import pytest_asyncio

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
from nia.nova.core import dependencies

# Configure logging
LOGS_DIR = Path("logs/tests")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"test_nova_endpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("test-nova-endpoints")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent propagation to root logger


@pytest_asyncio.fixture
async def mock_vector_store() -> AsyncMock:
    """Mock vector store fixture."""
    mock = AsyncMock(spec=VectorStore)
    mock.initialize = AsyncMock(return_value=None, name="mock_vs_initialize")
    mock.store_vector = AsyncMock(return_value=None, name="mock_vs_store_vector")
    mock.search_vectors = AsyncMock(return_value=[], name="mock_vs_search_vectors")
    mock.inspect_collection = AsyncMock(return_value=None, name="mock_vs_inspect_collection")
    mock.id = "vector-store-id"
    mock.name = "vector-store"
    mock.type = "vector-store"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "memory"
    mock.capabilities = ["vector-store"]
    mock.metadata = {}
    mock.get_state = AsyncMock(return_value={}, name="mock_vs_get_state")
    mock.update_state = AsyncMock(return_value=None, name="mock_vs_update_state")
    return mock


@pytest_asyncio.fixture
async def mock_world() -> AsyncMock:
    """Mock world fixture."""
    mock = AsyncMock(spec=World)
    mock.initialize = AsyncMock(return_value=None, name="mock_world_initialize")
    mock.get_state = AsyncMock(return_value={}, name="mock_world_get_state")
    mock.update_state = AsyncMock(return_value=None, name="mock_world_update_state")
    mock.execute_action = AsyncMock(return_value={"status": "success"}, name="mock_world_execute_action")
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
    mock.initialize = AsyncMock(return_value=None, name="mock_tf_initialize")
    mock.create_agent = AsyncMock(
        return_value=MagicMock(
            id="test-agent-id",
            name="test-agent",
            type="test",
            status="active",
            episodic=True,
            domain="test-domain",
            capabilities=["test"],
            metadata={},
            initialize=AsyncMock(return_value=None, name="mock_agent_initialize"),
            process=AsyncMock(return_value={"content": "test", "metadata": {}}, name="mock_agent_process"),
            get_state=AsyncMock(return_value={}, name="mock_agent_get_state"),
            update_state=AsyncMock(return_value=None, name="mock_agent_update_state")
        ),
        name="mock_tf_create_agent"
    )
    mock.id = "tiny-factory-id"
    mock.name = "tiny-factory"
    mock.type = "factory"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "factory"
    mock.capabilities = ["factory"]
    mock.metadata = {}
    mock.get_state = AsyncMock(return_value={}, name="mock_tf_get_state")
    mock.update_state = AsyncMock(return_value=None, name="mock_tf_update_state")
    return mock


@pytest_asyncio.fixture
async def mock_meta_agent_with_deps(mock_world: AsyncMock, mock_tiny_factory: AsyncMock) -> AsyncMock:
    """Create meta agent fixture with dependencies."""
    mock = AsyncMock(spec=MetaAgent)
    mock.initialize = AsyncMock(return_value=None, name="mock_ma_initialize")
    mock.process_interaction = AsyncMock(
        return_value={
            "content": "test response",
            "metadata": {
                "agent_actions": [],
                "initialization_sequence": [],
                "initialization_errors": {}
            }
        },
        name="mock_ma_process_interaction"
    )
    mock.get_state = AsyncMock(return_value={}, name="mock_ma_get_state")
    mock.update_state = AsyncMock(return_value=None, name="mock_ma_update_state")
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

    # Actually run the mocked initialize
    await mock.initialize()
    return mock


@pytest_asyncio.fixture
async def mock_meta_agent_no_deps() -> AsyncMock:
    """Create meta agent fixture without dependencies."""
    mock = AsyncMock(spec=MetaAgent)
    mock.initialize = AsyncMock(return_value=None, name="mock_ma_no_deps_initialize")
    mock.process_interaction = AsyncMock(
        return_value={
            "content": "test response",
            "metadata": {
                "agent_actions": [],
                "initialization_sequence": [],
                "initialization_errors": {}
            }
        },
        name="mock_ma_no_deps_process_interaction"
    )
    mock.get_state = AsyncMock(return_value={}, name="mock_ma_no_deps_get_state")
    mock.update_state = AsyncMock(return_value=None, name="mock_ma_no_deps_update_state")
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

    # Actually run the mocked initialize
    await mock.initialize()
    return mock


@pytest_asyncio.fixture
async def mock_memory_system(mock_vector_store: AsyncMock) -> AsyncMock:
    """Mock memory system fixture."""
    mock = AsyncMock(spec=TwoLayerMemorySystem)
    mock.initialize = AsyncMock(return_value=None, name="mock_ms_initialize")
    mock.store = AsyncMock(return_value=None, name="mock_ms_store")
    mock.search = AsyncMock(return_value=[], name="mock_ms_search")
    mock.vector_store = mock_vector_store
    mock.id = "memory-system-id"
    mock.name = "memory-system"
    mock.type = "memory"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "memory"
    mock.capabilities = ["memory"]
    mock.metadata = {}
    mock.get_state = AsyncMock(return_value={}, name="mock_ms_get_state")
    mock.update_state = AsyncMock(return_value=None, name="mock_ms_update_state")
    return mock


@pytest_asyncio.fixture(name="test_app")
async def test_app_fixture(
    mock_tiny_factory: AsyncMock,
    mock_world: AsyncMock,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> FastAPI:
    """Create and configure FastAPI test application."""
    app = FastAPI()
    app.dependency_overrides = {
        dependencies.get_tiny_factory: lambda: mock_tiny_factory,
        dependencies.get_world: lambda: mock_world,
        dependencies.get_meta_agent: lambda: mock_meta_agent_with_deps,
        dependencies.get_memory_system: lambda: mock_memory_system
    }
    app.include_router(nova_router)
    return app


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_initial_processing(
    async_client,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> None:
    """Test initial processing phase."""
    logger.info("Testing initial processing phase")
    response = await async_client.post(
        "/api/nova/ask",
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

    # Check that process_interaction was called
    mock_meta_agent_with_deps.process_interaction.assert_awaited_once()

    # Check that memory system store was called
    mock_memory_system.store.assert_awaited_once_with(
        content='test query',
        metadata={'source': 'user', 'workspace': 'personal'}
    )


@pytest.mark.asyncio
async def test_task_detection(
    async_client,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> None:
    """Test task detection phase."""
    logger.info("Testing task detection phase")
    response = await async_client.post(
        "/api/nova/ask",
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

    mock_meta_agent_with_deps.process_interaction.assert_awaited_once()
    mock_memory_system.store.assert_awaited_once_with(
        content='create a test',
        metadata={'source': 'user', 'workspace': 'personal'}
    )


@pytest.mark.asyncio
async def test_schema_validation_failure(async_client) -> None:
    """Test handling of schema validation failure."""
    logger.info("Testing schema validation failure")
    response = await async_client.post(
        "/api/nova/ask",
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
    assert isinstance(response_data["detail"], list), "Error details should be a list"
    assert len(response_data["detail"]) > 0, "Error details should not be empty"
    # Example check: "value is not a valid enumeration member" in response_data["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_meta_agent_no_dependencies(
    mock_meta_agent_no_deps: AsyncMock,
    async_client,
    test_app: FastAPI
) -> None:
    # Override the meta agent dependency
    test_app.dependency_overrides[dependencies.get_meta_agent] = lambda: mock_meta_agent_no_deps
    """Test MetaAgent functioning without dependencies."""
    logger.info("Testing MetaAgent without dependencies")
    assert mock_meta_agent_no_deps.memory_system is None, "MetaAgent should have no memory system"
    assert mock_meta_agent_no_deps.world is None, "MetaAgent should have no world"
    assert mock_meta_agent_no_deps.attributes is None, "MetaAgent should have no attributes"

    response = await async_client.post(
        "/api/nova/ask",
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

    # Ensure the meta agent was called
    mock_meta_agent_no_deps.process_interaction.assert_awaited_once()
    # If you want to ensure memory not used:
    # mock_memory_system.store.assert_not_called()


@pytest.mark.asyncio
async def test_initialization_error_handling(
    async_client,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock,
    mock_world: AsyncMock
) -> None:
    """Test error handling during initialization."""
    logger.info("Testing initialization error handling")
    mock_memory_system.initialize.side_effect = Exception("Simulated memory system error")

    response = await async_client.post(
        "/api/nova/ask",
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

    # Expecting your endpoint logic to handle the error as 422
    assert response.status_code == 422, "Should return 422 when agent initialization fails"
    error_data = response.json()
    assert "detail" in error_data, "Should include error details"
    assert isinstance(error_data["detail"], list), "Error details should be a list"
    assert len(error_data["detail"]) > 0, "Should include error messages"
    assert "Failed to initialize MetaAgent" in error_data["detail"][0]["msg"]  # Depends on your error message

    # Reset side effect for subsequent calls
    mock_memory_system.initialize.side_effect = None

    # Now test "recovery"
    recovery_response = await async_client.post(
        "/api/nova/ask",
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

    metadata = message["metadata"]
    assert "agent_actions" in metadata, "Metadata should have agent_actions"
    assert "debug_info" in metadata, "Metadata should have debug_info"

    debug_info = metadata["debug_info"]
    assert "initialization_sequence" in debug_info, "Debug info should have initialization sequence"
    assert "agent_dependencies" in debug_info, "Debug info should have agent dependencies"
    assert "MetaAgent" in debug_info["initialization_sequence"], "MetaAgent should appear in initialization sequence"

    # Properly await the object methods without the extra parentheses
    await mock_memory_system.initialize()
    await mock_world.initialize()
    await mock_meta_agent_with_deps.initialize()


@pytest.mark.asyncio
async def test_debug_flags(
    async_client,
    mock_meta_agent_with_deps: AsyncMock,
    mock_memory_system: AsyncMock
) -> None:
    """Test debug flags functionality."""
    logger.info("Testing debug flags")
    response = await async_client.post(
        "/api/nova/ask",
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
    assert isinstance(debug_info["initialization_sequence"], list), "Initialization sequence should be a list"
    assert isinstance(debug_info["agent_dependencies"], dict), "Agent dependencies should be a dict"
    assert "MetaAgent" in debug_info["initialization_sequence"], "Should see MetaAgent in the sequence"

    mock_meta_agent_with_deps.process_interaction.assert_awaited_once()
