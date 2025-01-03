"""Tests for the enhanced ExecutionAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.execution_agent import ExecutionAgent
from src.nia.nova.core.execution import ExecutionResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "execution": {
            "type": "sequential",
            "steps": {
                "step1": {
                    "type": "task",
                    "priority": 0.8,
                    "actions": ["action1"]
                }
            },
            "actions": {
                "action1": {
                    "type": "process",
                    "parameters": {"value": 10}
                }
            }
        },
        "actions": [
            {
                "type": "step_execution",
                "description": "Execute step1",
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
            "content": {"content": "Previous execution"},
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
def execution_agent(mock_memory_system, mock_world, request):
    """Create an ExecutionAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestExecution_{request.node.name}"
    return ExecutionAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(execution_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestExecution" in execution_agent.name
    assert execution_agent.domain == "professional"
    assert execution_agent.agent_type == "execution"
    
    # Verify enhanced attributes
    attributes = execution_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Action Executor"
    assert "Optimize resource usage" in attributes["desires"]
    assert "towards_sequences" in attributes["emotions"]
    assert "error_recovery" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(execution_agent.active_sequences, dict)
    assert isinstance(execution_agent.execution_patterns, dict)
    assert isinstance(execution_agent.resource_usage, dict)
    assert isinstance(execution_agent.error_recovery, dict)
    assert isinstance(execution_agent.retry_states, dict)
    assert isinstance(execution_agent.schedule_queue, dict)

@pytest.mark.asyncio
async def test_process_with_sequence_tracking(execution_agent, mock_memory_system):
    """Test content processing with sequence state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "execution_result",
                "description": "successful"
            },
            {
                "type": "sequence_state",
                "state": "progressing"
            },
            {
                "type": "resource_state",
                "state": "optimal"
            },
            {
                "type": "error_state",
                "state": "recovered"
            }
        ]
    }
    
    content = {
        "sequence_id": "seq1",
        "sequence_status": "active",
        "sequence_phase": "execution",
        "sequence_metrics": {"progress": 0.5},
        "step_completed": True,
        "resource_usage": {"cpu": 0.7}
    }
    
    response = await execution_agent.process(content)
    
    # Verify sequence state tracking
    assert "seq1" in execution_agent.active_sequences
    sequence_state = execution_agent.active_sequences["seq1"]
    assert sequence_state["status"] == "active"
    assert sequence_state["current_phase"] == "execution"
    assert sequence_state["steps_completed"] == 1
    assert sequence_state["metrics"]["progress"] == 0.5
    assert sequence_state["resource_usage"]["cpu"] == 0.7
    
    # Verify emotional updates
    assert execution_agent.emotions["sequence_state"] == "progressing"
    assert execution_agent.emotions["resource_state"] == "optimal"
    assert execution_agent.emotions["error_state"] == "recovered"

@pytest.mark.asyncio
async def test_execution_pattern_matching(execution_agent):
    """Test execution pattern matching and application."""
    # Set up test pattern
    pattern = {
        "conditions": {
            "sequence_phase": "execution",
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
            },
            {
                "type": "set_optimization",
                "value": True
            }
        ],
        "priority": 0.8
    }
    
    execution_agent._update_execution_patterns({"pattern1": pattern})
    
    # Test matching content
    content = {
        "sequence_id": "seq1",
        "sequence_phase": "execution",
        "metrics": {"progress": 0.5}
    }
    
    await execution_agent._update_sequence_state("seq1", content)
    
    # Verify pattern application
    sequence_state = execution_agent.active_sequences["seq1"]
    assert sequence_state["current_phase"] == "validation"
    assert sequence_state["metrics"]["validation_started"] is True
    assert sequence_state["needs_optimization"] is True

@pytest.mark.asyncio
async def test_resource_usage_tracking(execution_agent):
    """Test resource usage tracking."""
    resources = {
        "cpu": {
            "type": "compute",
            "allocated": 100.0,
            "utilized": 75.0,
            "peak": 80.0,
            "constraints": {"min_free": 10.0}
        }
    }
    
    await execution_agent._update_resource_usage(resources)
    
    # Verify resource tracking
    assert "cpu" in execution_agent.resource_usage
    resource = execution_agent.resource_usage["cpu"]
    assert resource["type"] == "compute"
    assert resource["allocated"] == 100.0
    assert resource["utilized"] == 75.0
    assert resource["peak"] == 80.0
    assert resource["constraints"] == {"min_free": 10.0}

@pytest.mark.asyncio
async def test_schedule_queue_management(execution_agent):
    """Test schedule queue management."""
    schedule = {
        "high": [
            {"id": "task1", "type": "critical"},
            {"id": "task2", "type": "important"}
        ],
        "medium": [
            {"id": "task3", "type": "normal"}
        ]
    }
    
    execution_agent._update_schedule_queue(schedule)
    
    # Verify queue management
    assert "high" in execution_agent.schedule_queue
    assert "medium" in execution_agent.schedule_queue
    assert len(execution_agent.schedule_queue["high"]["actions"]) == 2
    assert len(execution_agent.schedule_queue["medium"]["actions"]) == 1

@pytest.mark.asyncio
async def test_execute_and_store_with_enhancements(execution_agent, mock_memory_system):
    """Test enhanced execution and storage."""
    content = {
        "sequence_id": "seq1",
        "execution_patterns": {
            "pattern1": {
                "conditions": {"phase": "execution"},
                "actions": [{"type": "update_phase", "phase": "complete"}]
            }
        },
        "resources": {
            "memory": {
                "type": "ram",
                "allocated": 16.0,
                "utilized": 12.0
            }
        },
        "schedule": {
            "high": [{"id": "task1", "type": "critical"}]
        }
    }
    
    result = await execution_agent.execute_and_store(content, "sequential")
    
    # Verify execution result
    assert isinstance(result, ExecutionResult)
    assert result.is_valid is True
    
    # Verify pattern storage
    assert "pattern1" in execution_agent.execution_patterns
    
    # Verify resource tracking
    assert "memory" in execution_agent.resource_usage
    assert execution_agent.resource_usage["memory"]["utilized"] == 12.0
    
    # Verify schedule tracking
    assert "high" in execution_agent.schedule_queue
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence execution completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_sequence_optimization_handling(execution_agent, mock_memory_system):
    """Test sequence optimization handling."""
    content = {
        "sequence_id": "seq1",
        "needs_optimization": True,
        "resource_usage": {"cpu": 0.9}
    }
    
    await execution_agent._update_sequence_state("seq1", content)
    
    # Verify optimization flag
    assert execution_agent.active_sequences["seq1"]["needs_optimization"] is True
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Sequence seq1 needs optimization in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_resource_utilization_monitoring(execution_agent, mock_memory_system):
    """Test resource utilization monitoring."""
    resources = {
        "gpu": {
            "type": "compute",
            "allocated": 100.0,
            "utilized": 95.0,
            "peak": 98.0
        }
    }
    
    await execution_agent._update_resource_usage(resources)
    
    # Verify reflection was recorded for high utilization
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Resource gpu nearing capacity in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_recovery_monitoring(execution_agent, mock_memory_system):
    """Test error recovery monitoring."""
    # Set up failed recovery
    execution_agent.error_recovery["error1"] = {
        "status": "failed",
        "attempts": 3,
        "reason": "Unrecoverable state"
    }
    
    # Trigger monitoring through execution
    await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify reflection was recorded for failed recovery
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Error recovery failed for error1 in professional domain - escalation needed",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_retry_state_monitoring(execution_agent, mock_memory_system):
    """Test retry state monitoring."""
    # Set up exceeded retries
    execution_agent.retry_states["action1"] = {
        "attempts": 3,
        "max_attempts": 3,
        "last_error": "Connection failed"
    }
    
    # Trigger monitoring through execution
    await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify reflection was recorded for exceeded retries
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Action action1 exceeded retry limit in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_schedule_queue_monitoring(execution_agent, mock_memory_system):
    """Test schedule queue monitoring."""
    # Set up queue exceeding threshold
    execution_agent.schedule_queue["high"] = {
        "actions": [{"id": f"task{i}"} for i in range(15)],
        "threshold": 10,
        "metrics": {}
    }
    
    # Trigger monitoring through execution
    await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify reflection was recorded for exceeded threshold
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Priority high queue exceeding threshold in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(execution_agent, mock_memory_system):
    """Test error handling during execution."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify error handling
    assert isinstance(result, ExecutionResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Execution failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(execution_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await execution_agent.execute_and_store(
        {"type": "test"},
        "sequential",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await execution_agent.execute_and_store(
            {"type": "test"},
            "sequential",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
