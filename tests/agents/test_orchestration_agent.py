"""Tests for the enhanced OrchestrationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.orchestration_agent import OrchestrationAgent
from src.nia.nova.core.orchestration import OrchestrationResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "orchestration": {
            "type": "sequential",
            "agents": {
                "agent1": {
                    "type": "task",
                    "priority": 0.8,
                    "flows": ["flow1"]
                }
            },
            "flows": {
                "flow1": {
                    "type": "sequential",
                    "steps": ["step1", "step2"]
                }
            }
        },
        "decisions": [
            {
                "type": "flow_selection",
                "description": "Selected sequential flow",
                "confidence": 0.8,
                "importance": 0.9
            }
        ],
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
            "content": {"content": "Previous orchestration"},
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
def orchestration_agent(mock_memory_system, mock_world):
    """Create an OrchestrationAgent instance with mock dependencies."""
    return OrchestrationAgent(
        name="TestOrchestration",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(orchestration_agent):
    """Test agent initialization with enhanced attributes."""
    assert orchestration_agent.name == "TestOrchestration"
    assert orchestration_agent.domain == "professional"
    assert orchestration_agent.agent_type == "orchestration"
    
    # Verify enhanced attributes
    attributes = orchestration_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Agent Orchestrator"
    assert "Optimize task flows" in attributes["desires"]
    assert "towards_flows" in attributes["emotions"]
    assert "flow_optimization" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(orchestration_agent.active_flows, dict)
    assert isinstance(orchestration_agent.flow_patterns, dict)
    assert isinstance(orchestration_agent.execution_monitors, dict)
    assert isinstance(orchestration_agent.resource_allocations, dict)
    assert isinstance(orchestration_agent.dependency_graph, dict)

@pytest.mark.asyncio
async def test_process_with_flow_tracking(orchestration_agent, mock_memory_system):
    """Test content processing with flow state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "orchestration_result",
                "description": "successful"
            },
            {
                "type": "flow_state",
                "state": "progressing"
            },
            {
                "type": "resource_state",
                "state": "optimal"
            },
            {
                "type": "execution_state",
                "state": "running"
            }
        ]
    }
    
    content = {
        "flow_id": "flow1",
        "flow_status": "active",
        "flow_phase": "execution",
        "flow_metrics": {"progress": 0.5},
        "step_completed": True
    }
    
    response = await orchestration_agent.process(content)
    
    # Verify flow state tracking
    assert "flow1" in orchestration_agent.active_flows
    flow_state = orchestration_agent.active_flows["flow1"]
    assert flow_state["status"] == "active"
    assert flow_state["current_phase"] == "execution"
    assert flow_state["steps_completed"] == 1
    assert flow_state["metrics"]["progress"] == 0.5
    
    # Verify emotional updates
    assert orchestration_agent.emotions["flow_state"] == "progressing"
    assert orchestration_agent.emotions["resource_state"] == "optimal"
    assert orchestration_agent.emotions["execution_state"] == "running"

@pytest.mark.asyncio
async def test_flow_pattern_matching(orchestration_agent):
    """Test flow pattern matching and application."""
    # Set up test pattern
    pattern = {
        "conditions": {
            "flow_phase": "execution",
            "metrics": {"progress": 0.5}
        },
        "actions": [
            {
                "type": "update_phase",
                "phase": "validation"
            },
            {
                "type": "add_metric",
                "name": "validation_started",
                "value": True
            }
        ],
        "priority": 0.8
    }
    
    orchestration_agent._update_flow_patterns({"pattern1": pattern})
    
    # Test matching content
    content = {
        "flow_id": "flow1",
        "flow_phase": "execution",
        "metrics": {"progress": 0.5}
    }
    
    await orchestration_agent._update_flow_state("flow1", content)
    
    # Verify pattern application
    flow_state = orchestration_agent.active_flows["flow1"]
    assert flow_state["current_phase"] == "validation"
    assert flow_state["metrics"]["validation_started"] is True

@pytest.mark.asyncio
async def test_resource_allocation(orchestration_agent):
    """Test resource allocation tracking."""
    resources = {
        "cpu": {
            "type": "compute",
            "capacity": 100.0,
            "utilization": 75.0,
            "assigned_to": ["agent1", "agent2"],
            "constraints": {"min_free": 10.0}
        }
    }
    
    await orchestration_agent._update_resource_allocations(resources)
    
    # Verify resource tracking
    assert "cpu" in orchestration_agent.resource_allocations
    resource = orchestration_agent.resource_allocations["cpu"]
    assert resource["type"] == "compute"
    assert resource["capacity"] == 100.0
    assert resource["utilization"] == 75.0
    assert resource["assigned_to"] == ["agent1", "agent2"]
    assert resource["constraints"] == {"min_free": 10.0}

@pytest.mark.asyncio
async def test_dependency_tracking(orchestration_agent):
    """Test dependency graph tracking."""
    dependencies = {
        "task1": ["task2", "task3"],
        "task2": ["task4"],
        "task3": []
    }
    
    orchestration_agent._update_dependency_graph(dependencies)
    
    # Verify dependency tracking
    assert orchestration_agent.dependency_graph["task1"] == {"task2", "task3"}
    assert orchestration_agent.dependency_graph["task2"] == {"task4"}
    assert orchestration_agent.dependency_graph["task3"] == set()

@pytest.mark.asyncio
async def test_orchestrate_and_store_with_enhancements(orchestration_agent, mock_memory_system):
    """Test enhanced orchestration and storage."""
    content = {
        "flow_id": "flow1",
        "flow_patterns": {
            "pattern1": {
                "conditions": {"phase": "execution"},
                "actions": [{"type": "update_phase", "phase": "complete"}]
            }
        },
        "resources": {
            "memory": {
                "type": "ram",
                "capacity": 16.0,
                "utilization": 12.0
            }
        },
        "dependencies": {
            "task1": ["task2"]
        }
    }
    
    result = await orchestration_agent.orchestrate_and_store(content, "sequential")
    
    # Verify orchestration result
    assert isinstance(result, OrchestrationResult)
    assert result.is_valid is True
    
    # Verify pattern storage
    assert "pattern1" in orchestration_agent.flow_patterns
    
    # Verify resource tracking
    assert "memory" in orchestration_agent.resource_allocations
    assert orchestration_agent.resource_allocations["memory"]["utilization"] == 12.0
    
    # Verify dependency tracking
    assert orchestration_agent.dependency_graph["task1"] == {"task2"}
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence orchestration completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_flow_attention_handling(orchestration_agent, mock_memory_system):
    """Test flow attention handling."""
    content = {
        "flow_id": "flow1",
        "needs_attention": True,
        "has_blockers": True
    }
    
    await orchestration_agent._update_flow_state("flow1", content)
    
    # Verify attention flag
    assert orchestration_agent.active_flows["flow1"]["needs_attention"] is True
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Flow flow1 requires attention in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_resource_utilization_monitoring(orchestration_agent, mock_memory_system):
    """Test resource utilization monitoring."""
    resources = {
        "gpu": {
            "type": "compute",
            "capacity": 100.0,
            "utilization": 95.0
        }
    }
    
    await orchestration_agent._update_resource_allocations(resources)
    
    # Verify reflection was recorded for high utilization
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Resource gpu nearing capacity in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_execution_monitoring(orchestration_agent, mock_memory_system):
    """Test execution state monitoring."""
    # Set up blocked task
    orchestration_agent.execution_monitors["task1"] = {
        "status": "blocked",
        "reason": "Dependency not met"
    }
    
    # Trigger monitoring through orchestration
    await orchestration_agent.orchestrate_and_store({"type": "test"}, "sequential")
    
    # Verify reflection was recorded for blocked task
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Task task1 blocked in professional domain - intervention needed",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(orchestration_agent, mock_memory_system):
    """Test error handling during orchestration."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await orchestration_agent.orchestrate_and_store({"type": "test"}, "sequential")
    
    # Verify error handling
    assert isinstance(result, OrchestrationResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Orchestration failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(orchestration_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await orchestration_agent.orchestrate_and_store(
        {"type": "test"},
        "sequential",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await orchestration_agent.orchestrate_and_store(
            {"type": "test"},
            "sequential",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
