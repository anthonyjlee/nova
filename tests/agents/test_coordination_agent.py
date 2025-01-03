"""Tests for the specialized CoordinationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.coordination_agent import CoordinationAgent
from src.nia.nova.core.coordination import CoordinationResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def coordination_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a CoordinationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestCoordination_{request.node.name}"
    
    # Update mock memory system for coordination agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
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
        "issues": [],
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting",
            "role": "coordinator",
            "status": "active"
        }
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return CoordinationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
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
    
    # Verify swarm capabilities
    assert "swarm" in attributes["capabilities"]
    assert "architectures" in attributes["capabilities"]["swarm"]
    assert "hierarchical" in attributes["capabilities"]["swarm"]["architectures"]
    assert "types" in attributes["capabilities"]["swarm"]
    assert "MajorityVoting" in attributes["capabilities"]["swarm"]["types"]
    assert "roles" in attributes["capabilities"]["swarm"]
    assert "coordinator" in attributes["capabilities"]["swarm"]["roles"]

@pytest.mark.asyncio
async def test_swarm_architecture_validation(coordination_agent):
    """Test swarm architecture validation."""
    # Test valid architecture
    await coordination_agent.validate_swarm_architecture("hierarchical")
    
    # Test invalid architecture
    with pytest.raises(ValueError):
        await coordination_agent.validate_swarm_architecture("invalid_arch")
        
    # Test architecture transition
    await coordination_agent.validate_swarm_architecture("parallel")
    assert coordination_agent._configuration["swarm_architecture"] == "parallel"

@pytest.mark.asyncio
async def test_swarm_communication_patterns(coordination_agent):
    """Test swarm communication pattern handling."""
    # Test broadcast pattern
    broadcast_result = await coordination_agent.handle_swarm_communication("broadcast")
    assert broadcast_result["pattern"] == "broadcast"
    assert broadcast_result["success"] is True
    
    # Test direct pattern
    direct_result = await coordination_agent.handle_swarm_communication("direct")
    assert direct_result["pattern"] == "direct"
    assert direct_result["success"] is True
    
    # Test group pattern
    group_result = await coordination_agent.handle_swarm_communication("group")
    assert group_result["pattern"] == "group"
    assert group_result["success"] is True
    
    # Test invalid pattern
    with pytest.raises(KeyError):
        await coordination_agent.handle_swarm_communication("invalid_pattern")

@pytest.mark.asyncio
async def test_swarm_resource_management(coordination_agent):
    """Test swarm resource management for different swarm types."""
    # Test MajorityVoting resources
    voting_result = await coordination_agent.manage_swarm_resources("MajorityVoting")
    assert voting_result["type"] == "MajorityVoting"
    assert "voting_resources" in voting_result
    
    # Test RoundRobin resources
    roundrobin_result = await coordination_agent.manage_swarm_resources("RoundRobin")
    assert roundrobin_result["type"] == "RoundRobin"
    assert "rotation_schedule" in roundrobin_result
    
    # Test GraphWorkflow resources
    workflow_result = await coordination_agent.manage_swarm_resources("GraphWorkflow")
    assert workflow_result["type"] == "GraphWorkflow"
    assert "workflow_resources" in workflow_result
    
    # Test invalid swarm type
    with pytest.raises(KeyError):
        await coordination_agent.manage_swarm_resources("invalid_type")

@pytest.mark.asyncio
async def test_swarm_metrics_tracking(coordination_agent):
    """Test swarm metrics tracking and analysis."""
    metrics = await coordination_agent.track_swarm_metrics()
    
    # Verify metric categories
    assert "communication_overhead" in metrics
    assert "resource_utilization" in metrics
    assert "task_completion_rate" in metrics
    assert "swarm_health" in metrics
    
    # Verify metric values
    assert isinstance(metrics["communication_overhead"], (int, float))
    assert isinstance(metrics["resource_utilization"], (int, float))
    assert isinstance(metrics["task_completion_rate"], (int, float))
    assert isinstance(metrics["swarm_health"], (int, float))

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
            },
            {
                "type": "swarm_operation",
                "architecture": "hierarchical",
                "role": "coordinator",
                "status": "active"
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
    
    # Verify swarm operation tracking
    assert "swarm_operations" in response.metadata
    assert response.metadata["swarm_operations"]["architecture"] == "hierarchical"
    assert response.metadata["swarm_operations"]["role"] == "coordinator"

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
        },
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting"
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
    
    # Verify swarm metadata
    assert "swarm_operations" in result.metadata
    assert result.metadata["swarm_operations"]["architecture"] == "hierarchical"
    assert result.metadata["swarm_operations"]["type"] == "MajorityVoting"

@pytest.mark.asyncio
async def test_coordination_with_resource_conflicts(coordination_agent, mock_memory_system):
    """Test coordination handling with resource conflicts."""
    # Configure mock LLM response with resource conflicts
    mock_memory_system.llm.analyze = AsyncMock(return_value={
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
        ],
        "swarm": {
            "type": "MajorityVoting",
            "voting_required": True,
            "status": "conflict_resolution"
        }
    })
    
    result = await coordination_agent.coordinate_and_store({"type": "test"})
    
    # Verify conflict reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource conflicts detected in professional domain",
        domain="professional"
    )
    
    # Verify swarm voting trigger
    assert result.metadata["swarm_operations"]["voting_required"] is True
    assert result.metadata["swarm_operations"]["status"] == "conflict_resolution"

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
        metadata={
            "swarm_operations": {
                "architecture": "hierarchical",
                "type": "MajorityVoting",
                "role": "coordinator"
            }
        },
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
    
    # Verify swarm state
    assert coordination_agent._configuration["swarm_architecture"] == "hierarchical"
    assert coordination_agent._configuration["swarm_role"] == "coordinator"

@pytest.mark.asyncio
async def test_error_handling(coordination_agent, mock_memory_system):
    """Test error handling during coordination."""
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await coordination_agent.coordinate_and_store({"type": "test"})
    
    # Verify error handling
    assert isinstance(result, CoordinationResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Coordination failed - issues detected in professional domain",
        domain="professional"
    )
    
    # Verify swarm error handling
    assert "swarm_operations" in result.metadata
    assert result.metadata["swarm_operations"]["status"] == "error"

@pytest.mark.asyncio
async def test_coordination_with_empty_groups(coordination_agent, mock_memory_system):
    """Test coordination handling with empty groups."""
    # Mock coordination result with no groups
    mock_memory_system.llm.analyze.return_value = {
        "groups": {},
        "assignments": {},
        "resources": {},
        "issues": [],
        "swarm": {
            "architecture": "hierarchical",
            "type": "MajorityVoting",
            "status": "inactive"
        }
    }
    
    result = await coordination_agent.coordinate_and_store({"type": "test"})
    
    # Verify result
    assert isinstance(result, CoordinationResult)
    assert result.is_valid is False
    assert not result.groups
    assert not result.assignments
    assert not result.resources
    
    # Verify swarm status
    assert result.metadata["swarm_operations"]["status"] == "inactive"

if __name__ == "__main__":
    pytest.main([__file__])
