"""Shared fixtures for Nova integration tests."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from nia.nova.core.analytics import AnalyticsResult
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld

@pytest.fixture
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

@pytest.fixture
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

@pytest.fixture
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

@pytest.fixture
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

@pytest.fixture
async def llm_interface():
    """Create mock LLM interface."""
    interface = AsyncMock()
    interface.generate = AsyncMock(return_value="Test response")
    interface.get_embedding = AsyncMock(return_value=[0.1] * 384)
    return interface

@pytest.fixture
async def world(memory_system):
    """Create world environment."""
    mem_sys = await memory_system
    world = NIAWorld(memory_system=mem_sys)
    yield world
    # Cleanup
    await world.cleanup()

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Reset any global state
    from nia.nova.core.app import app
    app.dependency_overrides.clear()
