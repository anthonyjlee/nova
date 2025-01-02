"""Tests for the specialized ExecutionAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.execution_agent import ExecutionAgent
from src.nia.nova.core.execution import ExecutionResult

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
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main step"
                }
            }
        },
        "actions": [
            {
                "type": "step",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "execution_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_step",
                "severity": "medium",
                "description": "Missing step",
                "domain_impact": 0.3
            }
        ]
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
            "content": {"content": "Similar execution"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def execution_agent(mock_memory_system, mock_world):
    """Create an ExecutionAgent instance with mock dependencies."""
    return ExecutionAgent(
        name="TestExecution",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(execution_agent):
    """Test agent initialization."""
    assert execution_agent.name == "TestExecution"
    assert execution_agent.domain == "professional"
    assert execution_agent.agent_type == "execution"
    
    # Verify attributes were initialized
    attributes = execution_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify execution-specific attributes
    assert "Execute actions effectively" in attributes["desires"]
    assert "towards_actions" in attributes["emotions"]
    assert "action_execution" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(execution_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await execution_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "execution_state" in execution_agent.emotions
    assert "domain_state" in execution_agent.emotions
    assert any("Execute" in desire for desire in execution_agent.desires)

@pytest.mark.asyncio
async def test_execute_and_store(execution_agent, mock_memory_system):
    """Test action execution with domain awareness."""
    content = {
        "text": "Content to execute",
        "type": "sequential"
    }
    
    result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ExecutionResult)
    assert result.execution["type"] == "sequential"
    assert len(result.execution["steps"]) == 1
    assert len(result.actions) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(execution_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(execution_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await execution_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await execution_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_execute_with_different_domains(execution_agent):
    """Test execution with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(execution_agent, mock_memory_system):
    """Test error handling during execution."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await execution_agent.execute_and_store(
        {"content": "test"},
        execution_type="sequential"
    )
    
    # Verify error handling
    assert isinstance(result, ExecutionResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.actions) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(execution_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["actions"] = [
        {
            "type": "test_action",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["actions"] = [
        {
            "type": "test_action",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Execution failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(execution_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {"text": "test"}
    
    # Add critical issue
    mock_memory_system.llm.analyze.return_value["issues"] = [
        {
            "type": "critical_issue",
            "severity": "high",
            "description": "Critical problem"
        }
    ]
    
    result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical execution issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_action_reflection(execution_agent, mock_memory_system):
    """Test reflection recording for important actions."""
    content = {"text": "test"}
    
    # Add important action
    mock_memory_system.llm.analyze.return_value["actions"] = [
        {
            "type": "important_action",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical action"
        }
    ]
    
    result = await execution_agent.execute_and_store(
        content,
        execution_type="sequential"
    )
    
    # Verify important action reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important action steps completed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(execution_agent):
    """Test emotion updates based on execution results."""
    content = {"text": "Test content"}
    
    await execution_agent.process(content)
    
    # Verify emotion updates
    assert "execution_state" in execution_agent.emotions
    assert "domain_state" in execution_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(execution_agent):
    """Test desire updates based on execution needs."""
    content = {"text": "Test content"}
    
    await execution_agent.process(content)
    
    # Verify desire updates
    assert any("Execute" in desire for desire in execution_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
