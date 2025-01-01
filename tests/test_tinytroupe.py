"""Tests for TinyTroupe integration."""

import pytest
from datetime import datetime
from typing import Dict, List

from nia.nova.orchestrator import Nova
from nia.world.environment import NIAWorld
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.memory.types.memory_types import Memory, EpisodicMemory
from nia.agents.base import BaseAgent

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
async def test_agent_spawning(nova):
    """Test agent spawning and registration."""
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
    assert agent.occupation == "Tester"
    assert "Run tests" in agent.desires
    
    # Verify world registration
    assert agent.name in nova.world.agents
    assert agent.world == nova.world
    assert agent.memory == nova.memory

@pytest.mark.asyncio
async def test_conversation_during_pause(nova):
    """Test conversation continues during task pause."""
    # Spawn agents
    agent1 = await nova.spawn_agent("TestAgent", "agent1")
    agent2 = await nova.spawn_agent("TestAgent", "agent2")
    
    # Start and pause tasks
    await nova.pause_tasks()
    
    # Verify conversation still works
    response = await nova.handle_conversation(
        message="Hello agent2",
        source="agent1",
        target="agent2"
    )
    
    assert response["type"] == "conversation"
    assert response["from"] == "agent1"
    assert response["to"] == "agent2"
    
    # Verify task execution is blocked
    task_response = await nova.world.execute_action(
        agent1,
        "process_task",
        task={"type": "test"}
    )
    assert task_response is None

@pytest.mark.asyncio
async def test_domain_task_execution(nova):
    """Test domain-specific task execution."""
    # Register domain
    domain = "test_domain"
    nova.world.register_domain(domain)
    
    # Start task in domain
    task_id = await nova.start_task(
        task={
            "type": "test_task",
            "description": "Test domain task"
        },
        domain=domain
    )
    
    # Verify agent was created for domain
    domain_agents = nova.world.get_domain_agents(domain)
    assert len(domain_agents) == 1
    
    # Verify task status
    status = await nova.get_task_status(task_id)
    assert status["status"] == "in_progress"

@pytest.mark.asyncio
async def test_emergent_task_detection(nova):
    """Test detection of emergent tasks from conversation."""
    # Simulate conversation with task indicator
    conversation = "We should create a test suite for this"
    
    # Detect emergent tasks
    tasks = await nova.detect_emergent_tasks(conversation)
    
    # Verify task detection
    assert len(tasks) > 0
    assert tasks[0]["type"] == "emergent"
    assert tasks[0]["source"] == "conversation"
    assert tasks[0]["importance"] == 0.7

@pytest.mark.asyncio
async def test_agent_memory_integration(nova):
    """Test agent memory storage and recall."""
    # Spawn agent
    agent = await nova.spawn_agent("TestAgent", "memory_test")
    
    # Store memory through agent
    memory_id = await agent.store_memory(
        content="Test memory",
        importance=0.8,
        context={"type": "test"}
    )
    
    # Recall memory
    memories = await agent.recall_memories(
        query={"filter": {"content": "Test memory"}}
    )
    
    assert len(memories) == 1
    assert memories[0].content == "Test memory"
    assert memories[0].importance == 0.8
    assert memories[0].context["type"] == "test"

@pytest.mark.asyncio
async def test_world_resource_management(nova):
    """Test world resource management."""
    # Define resource
    nova.world.define_resource(
        "test_resource",
        {"data": "test"}
    )
    
    # Spawn agent
    agent = await nova.spawn_agent("TestAgent", "resource_test")
    
    # Access resource
    result = await nova.world.execute_action(
        agent,
        "use_resource",
        resource="test_resource"
    )
    
    assert result["data"] == "test"
    assert agent.name in nova.world.resources["test_resource"]["accessed_by"]

@pytest.mark.asyncio
async def test_agent_reflection(nova):
    """Test agent reflection capabilities."""
    # Spawn agent
    agent = await nova.spawn_agent("TestAgent", "reflection_test")
    
    # Create some memories
    for i in range(3):
        await agent.store_memory(
            content=f"Memory {i}",
            context={"type": "test_memory"}
        )
    
    # Trigger reflection
    await agent.reflect()
    
    # Verify reflection memory was created
    memories = await agent.recall_memories(
        query={"filter": {"context.type": "reflection"}}
    )
    
    assert len(memories) == 1
    assert memories[0].content["type"] == "reflection"
    assert len(memories[0].content["patterns"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
