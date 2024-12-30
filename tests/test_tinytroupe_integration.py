"""Tests for TinyTroupe integration with existing system."""

import pytest
from datetime import datetime
from typing import Dict, List

from nia.agents.tinytroupe_agent import TinyTroupeAgent
from nia.agents.base import BaseAgent
from nia.nova.orchestrator import Nova
from nia.world.environment import NIAWorld
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.memory.memory_types import Memory, EpisodicMemory, Concept, AgentResponse

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

@pytest.mark.asyncio
async def test_tinytroupe_agent_initialization():
    """Test TinyTroupe agent initialization."""
    agent = TinyTroupeAgent(
        name="test_agent",
        attributes={
            "occupation": "Tester",
            "desires": ["Run tests"],
            "emotions": {"baseline": "focused"}
        }
    )
    
    # Verify TinyTroupe attributes
    assert agent.name == "test_agent"
    assert agent.occupation == "Tester"
    assert "Run tests" in agent.desires
    assert agent.emotions["baseline"] == "focused"
    
    # Verify memory system attributes
    assert agent.agent_type == "base"
    assert hasattr(agent, "store_memory")
    assert hasattr(agent, "recall_memories")

@pytest.mark.asyncio
async def test_memory_tinytroupe_integration(memory_system):
    """Test memory system integration with TinyTroupe."""
    agent = TinyTroupeAgent(
        name="memory_test",
        memory_system=memory_system
    )
    
    # Store memory
    memory_id = await agent.store_memory(
        content="Test memory",
        importance=0.8,
        context={"type": "test"}
    )
    
    # Verify memory storage
    assert memory_id is not None
    
    # Verify TinyTroupe state update
    assert "memory" in agent.memory_references
    
    # Recall memory
    memories = await agent.recall_memories(
        query={"filter": {"content": "Test memory"}}
    )
    
    assert len(memories) == 1
    assert memories[0].content == "Test memory"
    assert memories[0].importance == 0.8

@pytest.mark.asyncio
async def test_emotion_concept_integration(memory_system):
    """Test emotion concept integration."""
    agent = TinyTroupeAgent(
        name="emotion_test",
        memory_system=memory_system
    )
    
    # Process emotion concept
    await agent.process({
        "content": "Test content",
        "concepts": [{
            "name": "Joy",
            "type": "emotion",
            "description": "Feeling happy",
            "related": []
        }]
    })
    
    # Verify emotion update
    assert "Joy" in agent.emotions
    assert agent.emotions["Joy"] == "Feeling happy"

@pytest.mark.asyncio
async def test_reflection_integration(memory_system):
    """Test reflection across both systems."""
    agent = TinyTroupeAgent(
        name="reflection_test",
        memory_system=memory_system
    )
    
    # Create test memories
    for i in range(3):
        await agent.store_memory(
            content=f"Memory {i}",
            importance=0.8,
            context={"type": "test_memory"}
        )
    
    # Trigger reflection
    await agent.reflect()
    
    # Verify memory reflection
    memories = await agent.recall_memories(
        query={"filter": {"content.type": "reflection"}}
    )
    assert len(memories) == 1
    
    # Verify TinyTroupe state updates
    assert "interest" in agent.emotions
    assert agent.emotions["interest"] == "high"
    assert any("Learn more about" in desire for desire in agent.desires)

@pytest.mark.asyncio
async def test_world_integration(world, memory_system):
    """Test world environment integration."""
    agent = TinyTroupeAgent(
        name="world_test",
        memory_system=memory_system,
        world=world
    )
    
    # Register with world
    world.add_agent(agent)
    
    # Define test resource
    world.define_resource(
        "test_resource",
        {"data": "test"}
    )
    
    # Access resource
    result = await world.execute_action(
        agent,
        "use_resource",
        resource="test_resource"
    )
    
    assert result["data"] == "test"
    assert agent.name in world.resources["test_resource"]["accessed_by"]

@pytest.mark.asyncio
async def test_nova_integration(nova, memory_system):
    """Test Nova orchestrator integration."""
    # Spawn test agent
    agent = await nova.spawn_agent(
        agent_type="TestAgent",
        name="test_agent",
        attributes={
            "occupation": "Tester",
            "desires": ["Run tests"]
        }
    )
    
    # Verify agent creation
    assert agent.name == "test_agent"
    assert isinstance(agent, TinyTroupeAgent)
    
    # Test conversation
    response = await nova.handle_conversation(
        message="Hello agent",
        target="test_agent"
    )
    
    assert response["type"] == "conversation"
    assert response["target"] == "test_agent"
    assert "response" in response

@pytest.mark.asyncio
async def test_task_domain_integration(nova):
    """Test task domain integration."""
    # Register domain
    domain = "test_domain"
    nova.world.register_domain(domain)
    
    # Start task
    task_id = await nova.start_task(
        task={
            "type": "test_task",
            "description": "Test domain task"
        },
        domain=domain
    )
    
    # Verify agent creation and assignment
    domain_agents = nova.world.get_domain_agents(domain)
    assert len(domain_agents) == 1
    
    # Verify task status
    status = await nova.get_task_status(task_id)
    assert status["status"] == "in_progress"

if __name__ == "__main__":
    pytest.main([__file__])
