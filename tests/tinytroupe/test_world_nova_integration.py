"""Tests for TinyTroupe integration with World and Nova systems."""

import pytest
from nia.agents.tinytroupe_agent import TinyTroupeAgent
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
