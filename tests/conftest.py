"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
import pytest_asyncio
from typing import Dict, List
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld
from nia.core.types.memory_types import KnowledgeVertical

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )

@pytest_asyncio.fixture
async def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def mock_memory_system():
    """Provide a mock memory system."""
    memory_system = MagicMock(spec=TwoLayerMemorySystem)
    
    # Set up LLM with detailed response
    memory_system.llm = AsyncMock()
    memory_system.llm.analyze = AsyncMock()
    memory_system.llm.analyze.return_value = {
        "initialization_state": {
            "status": "completed",
            "confidence": 0.95,
            "metrics": {
                "setup_quality": 0.93,
                "attribute_completeness": 0.94,
                "capability_readiness": 0.92
            }
        },
        "attribute_validation": {
            "occupation": {
                "value": "Advanced Action Executor",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Complete tasks",
                "secondary": ["Maintain quality", "Optimize processes"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_tasks": "focused",
                "towards_quality": "committed",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "task_execution",
                "supporting": ["quality_assurance", "process_optimization"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "task_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    }
    
    # Set up semantic store with async methods
    store = MagicMock()
    store.store_memory = AsyncMock()
    store.store_memory.return_value = None
    store.store_concept = AsyncMock()
    store.store_concept.return_value = None
    store.record_reflection = AsyncMock()
    store.record_reflection.return_value = None
    store.get_domain_access = AsyncMock()
    store.get_domain_access.return_value = True
    store.store = AsyncMock()
    store.store.return_value = None
    
    memory_system.semantic = MagicMock()
    memory_system.semantic.store = store
    
    # Configure store property
    store_property = property(lambda self: memory_system.semantic.store)
    type(memory_system).store = store_property
    
    # Set up episodic store with async methods
    memory_system.episodic = MagicMock()
    memory_system.episodic.store = MagicMock()
    memory_system.episodic.store.store = AsyncMock()
    memory_system.episodic.store.search = AsyncMock(return_value=[])
    memory_system.episodic.store.store_memory = AsyncMock()
    
    # Configure vector store
    memory_system.vector_store = MagicMock()
    memory_system.vector_store.store = AsyncMock()
    memory_system.vector_store.search = AsyncMock()
    
    # Set up async methods
    memory_system.store_experience = AsyncMock()
    memory_system.query_episodic = AsyncMock()
    memory_system.query_semantic = AsyncMock()
    memory_system.consolidate_memories = AsyncMock()
    memory_system.store_knowledge = AsyncMock()
    
    return memory_system

@pytest_asyncio.fixture
async def mock_world():
    """Provide a mock world environment."""
    world = MagicMock(spec=NIAWorld)
    world.get_domain_access = MagicMock(return_value=True)
    world.validate_domain = MagicMock(return_value=True)
    return world

@pytest.fixture
def base_agent_config():
    """Provide base agent configuration."""
    return {
        "name": "test_agent",
        "domain": "professional",
        "knowledge_vertical": KnowledgeVertical.GENERAL,
        "attributes": {
            "type": "execution",
            "role": "Advanced Action Executor",
            "occupation": "Advanced Action Executor",
            "capabilities": [
                "action_execution",
                "sequence_optimization",
                "resource_management"
            ],
            "metrics": {
                "performance": 0.8,
                "accuracy": 0.9,
                "reliability": 0.85
            }
        }
    }

@pytest_asyncio.fixture
async def mock_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Provide a base mock agent."""
    agent = MagicMock()
    
    # Configure basic properties
    agent.name = f"TestAgent_{request.node.name}"
    agent.domain = "professional"
    agent.agent_type = "execution"
    agent.attributes = base_agent_config["attributes"].copy()
    
    # Configure async methods
    agent.process = AsyncMock()
    agent.analyze = AsyncMock()
    agent.validate = AsyncMock()
    agent.store_memory = AsyncMock()
    agent.learn_concept = AsyncMock()
    agent.record_reflection = AsyncMock()
    agent.get_domain_access = AsyncMock(return_value=True)
    agent.validate_domain_access = AsyncMock(return_value=True)
    
    # Configure sequences and resources with proper structure
    sequences = {
        "seq1": {
            "status": "active",
            "current_phase": "validation",
            "metrics": {
                "performance": 0.6,
                "accuracy": 0.8
            }
        }
    }
    agent.active_sequences = MagicMock()
    agent.active_sequences.__getitem__ = MagicMock(side_effect=sequences.__getitem__)
    agent.active_sequences.get = MagicMock(side_effect=sequences.get)
    agent.active_sequences.items = MagicMock(return_value=sequences.items())
    
    resources = {
        "gpu": {
            "type": "gpu",
            "metrics": {
                "temperature": 85.0,
                "utilization": 0.75
            }
        }
    }
    agent.resource_usage = MagicMock()
    agent.resource_usage.__getitem__ = MagicMock(side_effect=resources.__getitem__)
    agent.resource_usage.get = MagicMock(side_effect=resources.get)
    agent.resource_usage.items = MagicMock(return_value=resources.items())
    
    # Configure vector store with proper async methods
    vector_store = AsyncMock()
    vector_store.store = AsyncMock()
    vector_store.store.return_value = None
    vector_store.search = AsyncMock()
    vector_store.search.return_value = []
    vector_store.store_memory = AsyncMock()
    vector_store.store_memory.return_value = None
    vector_store.store_concept = AsyncMock()
    vector_store.store_concept.return_value = None
    agent.vector_store = vector_store
    
    # Configure store with proper async methods
    store = AsyncMock()
    store.store_concept = AsyncMock()
    store.store_concept.return_value = None
    store.store_memory = AsyncMock()
    store.store_memory.return_value = None
    store.store = AsyncMock()
    store.store.return_value = None
    store.get_domain_access = AsyncMock()
    store.get_domain_access.return_value = True
    store.record_reflection = AsyncMock()
    store.record_reflection.return_value = None
    agent.store = store
    
    # Configure memory system
    memory_system = mock_memory_system
    memory_system.vector_store = vector_store
    memory_system.store = store
    memory_system.semantic.store = store
    memory_system.semantic.store.get_domain_access = AsyncMock(return_value=True)
    memory_system.semantic.store.record_reflection = AsyncMock()
    memory_system.semantic.store.record_reflection.return_value = None
    
    # Configure memory system property
    memory_property = property(lambda self: memory_system)
    type(agent).memory_system = memory_property
    agent._memory_system = memory_system
    
    # Configure world property
    world_property = property(lambda self: mock_world)
    type(agent).world = world_property
    agent._world = mock_world
    
    # Configure attributes
    agent.attributes = base_agent_config["attributes"].copy()
    agent.get_attributes = MagicMock(return_value=base_agent_config["attributes"].copy())
    agent.type = "execution"
    agent.role = "Advanced Action Executor"
    agent.occupation = "Advanced Action Executor"
    agent.agent_type = "execution"
    
    return agent

@pytest.fixture
def base_memory_data():
    """Provide base memory data for testing."""
    return {
        "content": "Test memory content",
        "source": "test",
        "timestamp": datetime.now(),
        "importance": 0.5,
        "metadata": {
            "test": True
        }
    }

@pytest.fixture
def memory_batch_data():
    """Provide test data for memory batches."""
    return [
        {
            "content": f"Memory {i}",
            "importance": 0.5 + (i * 0.1),
            "metadata": {"batch": "test"}
        }
        for i in range(3)
    ]

@pytest.fixture
def concept_data():
    """Provide test concept data."""
    return {
        "name": "Test Concept",
        "category": "Test Category",
        "attributes": {
            "key": "value"
        }
    }

@pytest.fixture
def relationship_data():
    """Provide test relationship data."""
    return {
        "from_concept": "Concept A",
        "to_concept": "Concept B",
        "type": "TEST_RELATION",
        "properties": {
            "strength": 0.8
        }
    }

@pytest.fixture
def consolidation_config():
    """Provide test consolidation configuration."""
    return {
        "time_based": {
            "enabled": True,
            "interval": 3600  # 1 hour
        },
        "volume_based": {
            "enabled": True,
            "threshold": 100
        },
        "importance_based": {
            "enabled": True,
            "threshold": 0.8
        }
    }

@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    class MockLogger:
        def __init__(self):
            self.logs = []
            
        def info(self, msg):
            self.logs.append(("INFO", msg))
            
        def error(self, msg):
            self.logs.append(("ERROR", msg))
            
        def warning(self, msg):
            self.logs.append(("WARNING", msg))
            
        def debug(self, msg):
            self.logs.append(("DEBUG", msg))
            
    return MockLogger()
