"""Tests for the specialized CoordinationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.coordination_agent import CoordinationAgent
from src.nia.nova.core.coordination import CoordinationResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "groups": {
            "group1": {
                "name": "Test Group 1",
                "type": "task",
                "status": "active",
                "description": "Test group",
                "priority": 0.8,
                "dependencies": ["group2"]
            }
        },
        "assignments": {
            "agent1": ["group1"],
            "agent2": ["group1", "group2"]
        },
        "resources": {
            "resource1": {
                "type": "compute",
                "amount": 100,
                "assigned_to": ["agent1"]
            }
        },
        "issues": []
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Previous coordination"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    world = MagicMock()
    world.notify_agent = AsyncMock()
    return world

@pytest.fixture
def coordination_agent(mock_memory_system, mock_world, request):
    """Create a CoordinationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestCoordination_{request.node.name}"
    return CoordinationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(coordination_agent):
    """Test agent initialization with TinyTroupe integration."""
    assert "TestCoordination" in coordination_agent.name
    assert coordination_agent.domain == "professional"
    assert coordination_agent.agent_type == "coordination"
    
    # Verify TinyTroupe attributes
    attributes = coordination_agent.get_attributes()
    assert attributes["occupation"] == "Coordination Manager"
    assert "Manage agent groups effectively" in attributes["desires"]
    assert "baseline" in attributes["emotions"]
    assert "group_management" in attributes["capabilities"]
    
    # Verify coordination state initialization
    assert isinstance(coordination_agent.active_groups, dict)
    assert isinstance(coordination_agent.agent_assignments, dict)
    assert isinstance(coordination_agent.resource_allocations, dict)
    assert isinstance(coordination_agent.task_dependencies, dict)

@pytest.mark.asyncio
async def test_process_with_coordination_concepts(coordination_agent, mock_memory_system):
    """Test content processing with coordination concepts."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "coordination_result",
                "description": "successful"
            },
            {
                "type": "coordination_need",
                "name": "resource_reallocation"
            },
            {
                "type": "resource_state",
                "state": "constrained"
            },
            {
                "domain_relevance": 0.9
            }
        ]
    }
    
    content = {
        "type": "coordination_update",
        "content": "Test coordination"
    }
    
    response = await coordination_agent.process(content)
    
    # Verify emotional updates
    assert coordination_agent.emotions["coordination_state"] == "successful"
    assert coordination_agent.emotions["resource_state"] == "constrained"
    assert coordination_agent.emotions["domain_state"] == "highly_relevant"
    
    # Verify desire updates
    assert "Address resource_reallocation" in coordination_agent.desires

@pytest.mark.asyncio
async def test_coordinate_and_store(coordination_agent, mock_memory_system):
    """Test coordination processing and storage."""
    content = {
        "type": "coordination_request",
        "groups": {
            "group1": {
                "name": "Test Group",
                "status": "active"
            }
        }
    }
    
    result = await coordination_agent.coordinate_and_store(content)
    
    # Verify coordination result
    assert isinstance(result, CoordinationResult)
    assert result.is_valid is True
    assert "group1" in result.groups
    
    # Verify memory storage
    mock_memory_system.semantic.store.record_reflection.assert_called()
    
    # Verify state updates
    assert "group1" in coordination_agent.active_groups
    assert coordination_agent.active_groups["group1"]["status"] == "active"

@pytest.mark.asyncio
async def test_coordination_with_resource_conflicts(coordination_agent, mock_memory_system):
    """Test coordination handling with resource conflicts."""
    # Mock coordination result with conflicts
    mock_memory_system.llm.analyze.return_value = {
        "groups": {
            "group1": {"status": "active"}
        },
        "assignments": {
            "agent1": ["group1"]
        },
        "resources": {
            "resource1": {
                "amount": 100,
                "assigned_to": ["agent1", "agent2"]
            }
        },
        "issues": [
            {
                "type": "resource_conflict",
                "severity": "medium",
                "description": "Resource overallocation"
            }
        ]
    }
    
    result = await coordination_agent.coordinate_and_store({"type": "test"})
    
    # Verify conflict reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "Resource conflicts detected" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_domain_validation(coordination_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await coordination_agent.coordinate_and_store(
        {"type": "test"},
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await coordination_agent.coordinate_and_store(
            {"type": "test"},
            target_domain="restricted"
        )

@pytest.mark.asyncio
async def test_coordination_state_updates(coordination_agent):
    """Test internal coordination state updates."""
    result = CoordinationResult(
        is_valid=True,
        groups={
            "group1": {
                "status": "active",
                "dependencies": ["group2"]
            },
            "group2": {
                "status": "inactive"
            }
        },
        assignments={
            "agent1": ["group1"],
            "agent2": ["group1", "group2"]
        },
        resources={
            "resource1": {
                "amount": 100,
                "assigned_to": ["agent1"]
            }
        },
        metadata={},
        issues=[]
    )
    
    coordination_agent._update_coordination_state(result)
    
    # Verify active groups
    assert "group1" in coordination_agent.active_groups
    assert "group2" not in coordination_agent.active_groups
    
    # Verify assignments
    assert coordination_agent.agent_assignments["agent1"] == {"group1"}
    assert coordination_agent.agent_assignments["agent2"] == {"group1", "group2"}
    
    # Verify resource allocations
    assert "resource1" in coordination_agent.resource_allocations
    assert coordination_agent.resource_allocations["resource1"]["amount"] == 100
    
    # Verify dependencies
    assert coordination_agent.task_dependencies["group1"] == {"group2"}

@pytest.mark.asyncio
async def test_error_handling(coordination_agent, mock_memory_system):
    """Test error handling during coordination."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await coordination_agent.coordinate_and_store({"type": "test"})
    
    # Verify error handling
    assert isinstance(result, CoordinationResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Coordination failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_coordination_with_empty_groups(coordination_agent, mock_memory_system):
    """Test coordination handling with empty groups."""
    # Mock coordination result with no groups
    mock_memory_system.llm.analyze.return_value = {
        "groups": {},
        "assignments": {},
        "resources": {},
        "issues": []
    }
    
    result = await coordination_agent.coordinate_and_store({"type": "test"})
    
    # Verify result
    assert isinstance(result, CoordinationResult)
    assert result.is_valid is False
    assert not result.groups
    assert not result.assignments
    assert not result.resources

if __name__ == "__main__":
    pytest.main([__file__])
