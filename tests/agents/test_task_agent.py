"""Tests for the specialized TaskAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.task_agent import TaskAgent
from src.nia.nova.core.task import TaskResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "tasks": [
            {
                "statement": "Complete this task",
                "type": "task",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9
            },
            {
                "statement": "Need more resources",
                "type": "task_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "dependencies": {
            "sequential": ["task1"],
            "blockers": ["blocker1"],
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ]
        }
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def task_agent(mock_memory_system, mock_world):
    """Create a TaskAgent instance with mock dependencies."""
    return TaskAgent(
        name="TestTask",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(task_agent):
    """Test agent initialization."""
    assert task_agent.name == "TestTask"
    assert task_agent.domain == "professional"
    assert task_agent.agent_type == "task"
    
    # Verify attributes were initialized
    attributes = task_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify domain-specific attributes
    assert "Maintain domain boundaries" in attributes["desires"]
    assert "towards_domain" in attributes["emotions"]
    assert "domain_validation" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(task_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await task_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in task_agent.emotions
    assert "domain_state" in task_agent.emotions
    assert any("Address" in desire for desire in task_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(task_agent, mock_memory_system):
    """Test task analysis with domain awareness."""
    content = {
        "content": "We need to complete this task",
        "type": "statement"
    }
    
    result = await task_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, TaskResult)
    assert len(result.tasks) > 0
    assert result.confidence > 0
    assert result.dependencies is not None
    
    # Verify memory storage
    assert hasattr(task_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(task_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await task_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await task_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(task_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await task_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await task_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(task_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await task_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, TaskResult)
    assert result.confidence == 0.0
    assert len(result.tasks) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(task_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await task_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await task_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(task_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await task_agent.process(content)
    
    # Verify emotion updates
    assert task_agent.emotions["analysis_state"] == "positive"
    assert task_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(task_agent):
    """Test desire updates based on task needs."""
    content = {"text": "Test content"}
    
    await task_agent.process(content)
    
    # Verify desire updates
    assert any("Address" in desire for desire in task_agent.desires)

@pytest.mark.asyncio
async def test_blocker_reflection(task_agent, mock_memory_system):
    """Test reflection recording for task blockers."""
    content = {"content": "test"}
    
    # Ensure blockers exist in dependencies
    mock_memory_system.llm.analyze.return_value["dependencies"]["blockers"] = ["blocker1"]
    
    result = await task_agent.analyze_and_store(content)
    
    # Verify blocker reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Task blockers" in str(call) for call in reflection_calls)

if __name__ == "__main__":
    pytest.main([__file__])
