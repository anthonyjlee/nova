"""Shared fixtures for TinyTroupe integration tests."""

import pytest
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.nova.orchestrator import Nova
from nia.world.environment import NIAWorld

@pytest.fixture
def memory_system(mock_vector_store, mock_neo4j_store):
    """Create memory system for testing."""
    return TwoLayerMemorySystem(mock_neo4j_store, mock_vector_store)

@pytest.fixture
def world(memory_system):
    """Create world environment for testing."""
    return NIAWorld(memory_system=memory_system)

@pytest.fixture
def nova(memory_system, world):
    """Create Nova orchestrator for testing."""
    return Nova(memory_system=memory_system, world=world)
