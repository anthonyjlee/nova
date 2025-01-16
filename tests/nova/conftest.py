"""Shared fixtures for Nova integration tests."""

import pytest
import pytest_asyncio
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, List, Any, Optional

from tests.nova.test_utils import (
    track_resource,
    untrack_resource,
    generate_test_memory,
    generate_test_agent
)
from nia.nova.core.analytics import AnalyticsResult
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld
from nia.memory.types.memory_types import (
    Memory, MemoryType, EpisodicMemory,
    TaskOutput, OutputType, TaskStatus
)

# Test data generators
def generate_test_profile(
    name: str,
    domain: str,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate test user profile data."""
    profile_id = f"test_profile_{uuid.uuid4()}"
    track_resource(profile_id)
    
    return {
        "id": profile_id,
        "name": name,
        "domain": domain,
        "preferences": preferences or {
            "communication_style": "technical",
            "visualization_preference": "high",
            "task_granularity": "detailed"
        },
        "metadata": {
            "test": True,
            "created": datetime.now(timezone.utc).isoformat()
        }
    }

def generate_test_task(
    title: str,
    domain: str,
    agent_id: Optional[str] = None,
    status: str = "pending",
    subtasks: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate test task data."""
    task_id = f"test_task_{uuid.uuid4()}"
    track_resource(task_id)
    
    return {
        "id": task_id,
        "title": title,
        "domain": domain,
        "agent_id": agent_id,
        "status": status,
        "subtasks": subtasks or [],
        "metadata": {
            "test": True,
            "created": datetime.now(timezone.utc).isoformat()
        }
    }

def generate_test_output(
    task_id: str,
    output_type: str,
    content: str,
    agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate test task output data."""
    output_id = f"test_output_{uuid.uuid4()}"
    track_resource(output_id)
    
    return {
        "id": output_id,
        "task_id": task_id,
        "type": output_type,
        "content": content,
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "test": True
        }
    }

# Test domains
TEST_DOMAINS = {
    "development": {
        "name": "Development",
        "description": "Software development domain",
        "capabilities": ["coding", "testing", "debugging"]
    },
    "security": {
        "name": "Security",
        "description": "Security analysis domain",
        "capabilities": ["audit", "review", "hardening"]
    },
    "documentation": {
        "name": "Documentation",
        "description": "Documentation and writing domain",
        "capabilities": ["writing", "editing", "formatting"]
    }
}

@pytest.fixture
def test_domain():
    """Get test domain data."""
    domain_id = f"test_domain_{uuid.uuid4()}"
    track_resource(domain_id)
    return {
        "id": domain_id,
        **TEST_DOMAINS["development"]
    }

@pytest_asyncio.fixture
async def mock_vector_store():
    """Create mock vector store."""
    store = AsyncMock()
    store.search = AsyncMock(return_value=[{
        "domain": "test",
        "content": "test content",
        "analytics": {"test": "data"}
    }])
    store.delete_nodes = AsyncMock(return_value=True)
    store.delete_vectors = AsyncMock(return_value=True)
    store.search_vectors = AsyncMock(return_value=[{
        "domain": "test",
        "content": "test content",
        "analytics": {"test": "data"}
    }])
    store.store_vector = AsyncMock(return_value="test_id")
    store.update_metadata = AsyncMock(return_value=True)
    return store

@pytest_asyncio.fixture
async def mock_neo4j_store():
    """Create mock Neo4j store."""
    store = AsyncMock()
    store.query = AsyncMock(return_value=[{
        "domain": "test_science",
        "content": "test content",
        "analytics": {"test": "data"}
    }])
    store.run_query = AsyncMock(return_value=[{
        "domain": "test_science",
        "content": "test content",
        "analytics": {"test": "data"}
    }])
    store.search = AsyncMock(return_value=[{
        "domain": "test_science",
        "content": "test content",
        "analytics": {"test": "data"}
    }])
    store.store_concept = AsyncMock(return_value=True)
    store.connect = AsyncMock()
    store.close = AsyncMock()
    return store

@pytest_asyncio.fixture
async def memory_system(mock_vector_store, mock_neo4j_store):
    """Create memory system with mock stores."""
    vector_store = await mock_vector_store
    neo4j_store = await mock_neo4j_store
    
    system = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store=vector_store
    )
    # Override semantic store with mock
    system.semantic = neo4j_store
    # Initialize system
    await system.initialize()
    return system

@pytest_asyncio.fixture
async def mock_meta_agent_with_deps(mock_world: AsyncMock, mock_tiny_factory: AsyncMock) -> AsyncMock:
    """Create meta agent fixture with dependencies."""
    mock = AsyncMock()
    mock.initialize = AsyncMock(return_value=None)
    
    # Return a dictionary that matches what the endpoint expects
    mock.process_interaction = AsyncMock(return_value={
        "content": "test response",
        "agent_actions": [],
        "cognitive_state": {},
        "task_context": {},
        "debug_info": {
            "initialization_sequence": ["MetaAgent"],
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
        "initialization_sequence": ["MetaAgent"],
        "initialization_errors": {}
    }
    mock.memory_system = None
    mock.world = mock_world
    mock.attributes = None
    mock.factory = mock_tiny_factory
    mock.initialization_sequence = ["MetaAgent"]
    mock.agent_dependencies = {}
    mock.initialization_errors = {}
    await mock.initialize()
    return mock

@pytest_asyncio.fixture
async def mock_meta_agent_no_deps() -> AsyncMock:
    """Create meta agent fixture without dependencies."""
    mock = AsyncMock()
    mock.initialize = AsyncMock(return_value=None)
    
    # Return a dictionary that matches what the endpoint expects
    mock.process_interaction = AsyncMock(return_value={
        "content": "test response",
        "agent_actions": [],
        "cognitive_state": {},
        "task_context": {},
        "debug_info": {
            "initialization_sequence": ["MetaAgent"],
            "initialization_errors": {}
        }
    })
    mock.get_state = AsyncMock(return_value={})
    mock.update_state = AsyncMock(return_value=None)
    mock.id = "meta-agent-no-deps-id"
    mock.name = "meta-agent-no-deps"
    mock.type = "meta"
    mock.status = "active"
    mock.episodic = True
    mock.domain = "professional"
    mock.capabilities = ["team_coordination", "cognitive_processing", "task_management"]
    mock.metadata = {
        "agent_actions": [],
        "initialization_sequence": ["MetaAgent"],
        "initialization_errors": {}
    }
    mock.memory_system = None
    mock.world = None
    mock.attributes = None
    mock.factory = None
    mock.initialization_sequence = ["MetaAgent"]
    mock.agent_dependencies = {}
    mock.initialization_errors = {}
    await mock.initialize()
    return mock

@pytest_asyncio.fixture
async def mock_analytics_agent():
    """Create mock analytics agent."""
    agent = AsyncMock()
    
    async def process_analytics(**kwargs):
        """Mock analytics processing with dynamic response based on input."""
        if "questionnaire" in kwargs:
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "profile_creation": {"success": True},
                    "personality_insights": {
                        "openness": kwargs["questionnaire"]["big_five"]["openness"],
                        "conscientiousness": kwargs["questionnaire"]["big_five"]["conscientiousness"]
                    },
                    "learning_preferences": kwargs["questionnaire"]["learning_style"],
                    "communication_style": kwargs["questionnaire"]["communication"]
                },
                insights=[{"type": "profile", "description": "Profile created successfully"}],
                confidence=0.95
            )
        elif "cross_domain" in kwargs:
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "cross_domain_request": {
                        "requires_approval": True,
                        "auto_approved": False,
                        "operation": kwargs["cross_domain"]["operation"]
                    }
                },
                insights=[{"type": "security", "description": "Cross-domain request requires approval"}],
                confidence=0.9
            )
        elif "task" in kwargs and "profile_id" in kwargs:
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "task_adaptation": {
                        "profile_applied": True,
                        "adaptations": {
                            "granularity": "detailed",
                            "communication_style": "technical",
                            "visualization_preference": "high"
                        }
                    }
                },
                insights=[{"type": "adaptation", "description": "Task adapted to user profile"}],
                confidence=0.85
            )
        elif "settings" in kwargs:
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "settings_update": {
                        "success": True,
                        "current_settings": kwargs["settings"]
                    }
                },
                insights=[{"type": "settings", "description": "Auto-approval settings updated"}],
                confidence=0.95
            )
        elif "target" in kwargs and kwargs["target"].get("domain") != kwargs.get("domain"):
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "access_violation": {
                        "blocked": True,
                        "reason": "domain_boundary",
                        "source_domain": kwargs.get("domain"),
                        "target_domain": kwargs["target"]["domain"],
                        "operation": "direct_access"
                    }
                },
                insights=[{"type": "security", "description": "Domain boundary violation prevented"}],
                confidence=0.95
            )
        elif "task" in kwargs and not "profile_id" in kwargs:
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "task_creation": {
                        "success": True,
                        "subtasks": [
                            {
                                "id": subtask["id"],
                                "type": subtask["type"],
                                "domain": kwargs["domain"],
                                "inherited_domain": True
                            }
                            for subtask in kwargs["task"]["subtasks"]
                        ]
                    }
                },
                insights=[{"type": "task", "description": "Task created with domain inheritance"}],
                confidence=0.9
            )
        elif "swarm_config" in kwargs:
            if kwargs["swarm_config"]["type"] == "majority_voting":
                return AnalyticsResult(
                    is_valid=True,
                    analytics={
                        "voting_results": {
                            "threshold_met": True,
                            "votes": {"approve": 3, "reject": 1},
                            "confidence": 0.85
                        }
                    },
                    insights=[{"type": "voting", "description": "Majority consensus reached"}],
                    confidence=0.9
                )
            elif kwargs["swarm_config"]["type"] == "round_robin":
                return AnalyticsResult(
                    is_valid=True,
                    analytics={
                        "rotation_metrics": {
                            "fair_distribution": True,
                            "completed_rotations": 1,
                            "agent_stats": {"total": 3, "active": 3}
                        }
                    },
                    insights=[{"type": "rotation", "description": "Fair task distribution achieved"}],
                    confidence=0.9
                )
            elif kwargs["swarm_config"]["type"] == "graph_workflow":
                return AnalyticsResult(
                    is_valid=True,
                    analytics={
                        "graph_metrics": {
                            "execution_complete": True,
                            "node_results": [
                                {"id": "parse", "status": "completed"},
                                {"id": "analyze", "status": "completed"},
                                {"id": "validate", "status": "completed"}
                            ],
                            "execution_time": 1.5
                        }
                    },
                    insights=[{"type": "workflow", "description": "Graph execution completed successfully"}],
                    confidence=0.9
                )
        else:
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "key_metrics": [{"name": "Test", "value": 0.8, "confidence": 0.9}],
                    "trends": [{"name": "Test", "description": "Test", "confidence": 0.85}]
                },
                insights=[{"type": "test", "description": "Test"}],
                confidence=0.9
            )
    
    agent.process_analytics = AsyncMock(side_effect=process_analytics)
    return agent

@pytest_asyncio.fixture
async def llm_interface():
    """Create mock LLM interface."""
    interface = AsyncMock()
    interface.generate = AsyncMock(return_value="Test response")
    interface.get_embedding = AsyncMock(return_value=[0.1] * 384)
    return interface

@pytest_asyncio.fixture
async def world(memory_system):
    """Create world environment."""
    mem_sys = await memory_system
    world = NIAWorld(memory_system=mem_sys)
    yield world
    # Cleanup
    await world.cleanup()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Reset any global state
    from nia.nova.core.app import app
    app.dependency_overrides.clear()
