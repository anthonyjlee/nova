"""Tests for Nova endpoints."""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
from pathlib import Path

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

# Import for breakpoint()
import pdb

from nia.nova.core.nova_endpoints import nova_router, NovaRequest, NovaResponse
from nia.core.feature_flags import FeatureFlags
from nia.core.types.memory_types import (
    Memory, MemoryType, DomainContext, TaskState,
    ValidationSchema, DomainTransfer
)
from nia.nova.core.dependencies import (
    get_memory_system,
    get_agent_store,
    get_llm_interface,
    get_schema_agent,
    get_parsing_agent,
    get_context_agent,
    get_memory_agent,
    get_analysis_agent,
    get_planning_agent,
    get_research_agent,
    get_belief_agent,
    get_desire_agent,
    get_emotion_agent,
    get_reflection_agent,
    get_meta_agent,
    get_integration_agent,
    get_validation_agent,
    get_orchestration_agent,
    get_dialogue_agent,
    get_synthesis_agent
)

# Create test app
app = FastAPI()
app.include_router(nova_router)

@pytest.fixture
def mock_memory_system():
    """Mock memory system."""
    memory = AsyncMock()
    memory.episodic = AsyncMock()
    memory.semantic = AsyncMock()
    memory.store_ephemeral = AsyncMock()
    memory.store_permanent = AsyncMock()
    memory.query_episodic = AsyncMock(return_value=[])
    return memory

@pytest.fixture
def mock_agent_store():
    """Mock agent store."""
    store = AsyncMock()
    store.store_agent = AsyncMock(return_value="test-agent-id")
    store.get_agent = AsyncMock(return_value={
        "id": "test-agent-id",
        "name": "test-agent",
        "type": "test",
        "status": "active",
        "metadata": {"capabilities": []}
    })
    return store

@pytest.fixture
def mock_llm():
    """Mock LLM interface."""
    return AsyncMock()

@pytest.fixture
def mock_agents():
    """Mock all agent dependencies."""
    return {
        "schema_agent": AsyncMock(
            validate_schema=AsyncMock(return_value=MagicMock(
                is_valid=True,
                dict=lambda: {"validation": "ok"}
            ))
        ),
        "parsing_agent": AsyncMock(
            parse_text=AsyncMock(return_value=MagicMock(
                response="parsed text",
                dict=lambda: {"parsed": "text"}
            ))
        ),
        "context_agent": AsyncMock(
            get_context=AsyncMock(return_value={"context": "test"})
        ),
        "memory_agent": AsyncMock(
            retrieve_relevant_memories=AsyncMock(return_value={"memories": []})
        ),
        "analysis_agent": AsyncMock(
            detect_task=AsyncMock(return_value=MagicMock(
                is_task=False,
                dict=lambda: {"task_detected": False}
            )),
            analyze=AsyncMock(return_value=MagicMock(
                key_points=["test point"],
                confidence=0.8,
                dict=lambda: {"analysis": "complete"}
            ))
        ),
        "planning_agent": AsyncMock(
            create_plan=AsyncMock(return_value=MagicMock(
                dict=lambda: {"plan": "created"}
            ))
        ),
        "research_agent": AsyncMock(
            gather_information=AsyncMock(return_value=MagicMock(
                confidence=0.8,
                dict=lambda: {"research": "complete"}
            ))
        ),
        "belief_agent": AsyncMock(
            analyze_beliefs=AsyncMock(return_value=MagicMock(
                beliefs=["test belief"],
                confidence=0.8,
                dict=lambda: {"beliefs": ["test belief"]}
            ))
        ),
        "desire_agent": AsyncMock(
            analyze_desires=AsyncMock(return_value=MagicMock(
                desires=["test desire"],
                confidence=0.8,
                dict=lambda: {"desires": ["test desire"]}
            ))
        ),
        "emotion_agent": AsyncMock(
            analyze_emotion=AsyncMock(return_value=MagicMock(
                emotions={"valence": 0.5},
                confidence=0.8,
                dict=lambda: {"emotions": {"valence": 0.5}}
            ))
        ),
        "reflection_agent": AsyncMock(
            analyze_reflection=AsyncMock(return_value=MagicMock(
                insights=["test insight"],
                confidence=0.8,
                dict=lambda: {"reflection": "complete"}
            ))
        ),
        "meta_agent": AsyncMock(
            process_interaction=AsyncMock(return_value=MagicMock(
                key_points=["test point"],
                confidence=0.8,
                dict=lambda: {"meta": "processed"}
            )),
            record_synthesis=AsyncMock()
        ),
        "integration_agent": AsyncMock(
            integrate=AsyncMock(return_value=MagicMock(
                dict=lambda: {"integrated": "response"}
            ))
        ),
        "validation_agent": AsyncMock(
            validate=AsyncMock(return_value=MagicMock(
                dict=lambda: {"validated": "response"}
            ))
        ),
        "orchestration_agent": AsyncMock(
            process_request=AsyncMock(return_value=MagicMock(
                dict=lambda: {"orchestrated": "response"}
            ))
        ),
        "dialogue_agent": AsyncMock(
            generate_response=AsyncMock(return_value=MagicMock(
                dict=lambda: {"dialogue": "response"}
            ))
        ),
        "synthesis_agent": AsyncMock(
            synthesize=AsyncMock(return_value=MagicMock(
                response="Final response",
                key_points=["key point"],
                implications=["implication"],
                uncertainties=["uncertainty"],
                reasoning=["reason"],
                confidence=0.9,
                concepts=[],
                dict=lambda: {"synthesized": "response"}
            ))
        )
    }

@pytest.fixture
def mock_dependencies(
    mock_memory_system,
    mock_agent_store,
    mock_llm,
    mock_agents
):
    """Override FastAPI dependencies."""
    app.dependency_overrides[get_memory_system] = lambda: mock_memory_system
    app.dependency_overrides[get_agent_store] = lambda: mock_agent_store
    app.dependency_overrides[get_llm_interface] = lambda: mock_llm
    app.dependency_overrides[get_schema_agent] = lambda: mock_agents["schema_agent"]
    app.dependency_overrides[get_parsing_agent] = lambda: mock_agents["parsing_agent"]
    app.dependency_overrides[get_context_agent] = lambda: mock_agents["context_agent"]
    app.dependency_overrides[get_memory_agent] = lambda: mock_agents["memory_agent"]
    app.dependency_overrides[get_analysis_agent] = lambda: mock_agents["analysis_agent"]
    app.dependency_overrides[get_planning_agent] = lambda: mock_agents["planning_agent"]
    app.dependency_overrides[get_research_agent] = lambda: mock_agents["research_agent"]
    app.dependency_overrides[get_belief_agent] = lambda: mock_agents["belief_agent"]
    app.dependency_overrides[get_desire_agent] = lambda: mock_agents["desire_agent"]
    app.dependency_overrides[get_emotion_agent] = lambda: mock_agents["emotion_agent"]
    app.dependency_overrides[get_reflection_agent] = lambda: mock_agents["reflection_agent"]
    app.dependency_overrides[get_meta_agent] = lambda: mock_agents["meta_agent"]
    app.dependency_overrides[get_integration_agent] = lambda: mock_agents["integration_agent"]
    app.dependency_overrides[get_validation_agent] = lambda: mock_agents["validation_agent"]
    app.dependency_overrides[get_orchestration_agent] = lambda: mock_agents["orchestration_agent"]
    app.dependency_overrides[get_dialogue_agent] = lambda: mock_agents["dialogue_agent"]
    app.dependency_overrides[get_synthesis_agent] = lambda: mock_agents["synthesis_agent"]

@pytest.fixture
async def feature_flags():
    """Setup feature flags for testing."""
    flags = FeatureFlags()
    # Enable debug flags for testing
    await flags.enable_debug('log_validation')
    await flags.enable_debug('log_websocket')
    await flags.enable_debug('log_storage')
    return flags

@pytest.fixture
def client(mock_dependencies, feature_flags):
    """Test client with mocked dependencies."""
    logger.info("Setting up test client with mocked dependencies")
    return TestClient(app)

@pytest.mark.asyncio
async def test_initial_processing(client, mock_agents, feature_flags):
    """Test initial processing phase."""
    logger.info("Testing initial processing phase")
    # Breakpoint before schema validation
    breakpoint()
    try:
        response = await client.post("/api/nova/ask", json={
            "content": "test query",
            "workspace": "personal",
            "debug_flags": {
                "log_validation": True,
                "log_websocket": True,
                "log_storage": True
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in initial processing test: {str(e)}")
        raise

    logger.info("Verifying initial processing assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    mock_agents["schema_agent"].validate_schema.assert_called_once()
    mock_agents["parsing_agent"].parse_text.assert_called_once()
    mock_agents["context_agent"].get_context.assert_called_once()
    mock_agents["memory_agent"].retrieve_relevant_memories.assert_called_once()

@pytest.mark.asyncio
async def test_task_detection(client, mock_agents, feature_flags):
    """Test task detection phase."""
    logger.info("Testing task detection phase")
    logger.debug("Setting up mock task detection")
    mock_agents["analysis_agent"].detect_task.return_value = MagicMock(
        is_task=True,
        task_type="test_task",
        requires_agents=True,
        required_agents=[
            MagicMock(
                name="test_agent",
                capabilities=["test"],
                specialization="test",
                dict=lambda: {"agent": "config"}
            )
        ],
        task_id="test-task-id",
        dict=lambda: {"task": "detected"}
    )
    
    try:
        response = await client.post("/api/nova/ask", json={
            "content": "create a test",
            "workspace": "personal",
            "debug_flags": {
                "log_validation": True,
                "log_websocket": True,
                "log_storage": True
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in task detection test: {str(e)}")
        raise

    logger.info("Verifying task detection assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    mock_agents["analysis_agent"].detect_task.assert_called_once()
    mock_agents["planning_agent"].create_plan.assert_called_once()

@pytest.mark.asyncio
async def test_cognitive_processing(client, mock_agents, feature_flags):
    """Test cognitive processing phase."""
    logger.info("Testing cognitive processing phase")
    try:
        response = await client.post("/api/nova/ask", json={
            "content": "test query",
            "workspace": "personal",
            "debug_flags": {
                "log_validation": True,
                "log_websocket": True,
                "log_storage": True
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in cognitive processing test: {str(e)}")
        raise

    logger.info("Verifying cognitive processing assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    mock_agents["belief_agent"].analyze_beliefs.assert_called_once()
    mock_agents["desire_agent"].analyze_desires.assert_called_once()
    mock_agents["emotion_agent"].analyze_emotion.assert_called_once()
    mock_agents["reflection_agent"].analyze_reflection.assert_called_once()
    mock_agents["meta_agent"].process_interaction.assert_called_once()

@pytest.mark.asyncio
async def test_response_generation(client, mock_agents, feature_flags):
    """Test response generation phase."""
    logger.info("Testing response generation phase")
    try:
        response = await client.post("/api/nova/ask", json={
            "content": "test query",
            "workspace": "personal",
            "debug_flags": {
                "log_validation": True,
                "log_websocket": True,
                "log_storage": True
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in response generation test: {str(e)}")
        raise

    logger.info("Verifying response generation assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    mock_agents["integration_agent"].integrate.assert_called_once()
    mock_agents["validation_agent"].validate.assert_called_once()
    mock_agents["orchestration_agent"].process_request.assert_called_once()
    mock_agents["dialogue_agent"].generate_response.assert_called_once()
    mock_agents["synthesis_agent"].synthesize.assert_called_once()

@pytest.mark.asyncio
async def test_schema_validation_failure(client, mock_agents, feature_flags):
    """Test handling of schema validation failure."""
    logger.info("Testing schema validation failure")
    logger.debug("Setting up mock validation failure")
    # Breakpoint before validation failure test
    breakpoint()
    mock_agents["schema_agent"].validate_schema.return_value = MagicMock(
        is_valid=False,
        issues=["Invalid schema"],
        dict=lambda: {"validation": "failed", "issues": ["Invalid schema"]}
    )
    
    try:
        # Test with strict mode
        response = await client.post("/api/nova/ask", json={
            "content": "test query",
            "workspace": "personal",
            "debug_flags": {
                "strict_mode": True,
                "log_validation": True
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in schema validation failure test: {str(e)}")
        raise

    logger.info("Verifying schema validation failure assertions")
    assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
    assert "Schema validation failed" in response.json()["detail"], "Expected validation failure message not found"

@pytest.mark.asyncio
async def test_memory_storage(client, mock_memory_system, feature_flags):
    """Test memory storage operations."""
    logger.info("Testing memory storage operations")
    # Breakpoint before memory operations
    breakpoint()
    try:
        response = await client.post("/api/nova/ask", json={
            "content": "test query",
            "workspace": "personal",
            "debug_flags": {
                "log_validation": True,
                "log_websocket": True,
                "log_storage": True
            }
        })
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in memory storage test: {str(e)}")
        raise

    logger.info("Verifying memory storage assertions")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    mock_memory_system.store_ephemeral.assert_called()
    mock_memory_system.query_episodic.assert_called()
    mock_memory_system.episodic.store_memory.assert_called()
