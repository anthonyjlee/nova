"""Tests for the specialized TaskAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.task_agent import TaskAgent
from src.nia.nova.core.task import TaskResult

@pytest.fixture
def base_agent_config():
    """Create base agent configuration."""
    return {
        "name": "test_agent",
        "agent_type": "task",
        "domain": "professional",
        "attributes": {
            "occupation": "Task Analyst",
            "desires": [
                "Understand task requirements",
                "Track task dependencies"
            ],
            "emotions": {
                "baseline": "focused",
                "towards_analysis": "systematic"
            },
            "capabilities": [
                "task_analysis",
                "dependency_tracking"
            ]
        }
    }

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value=TaskResult(
        tasks=[
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
        confidence=0.8,
        dependencies={
            "sequential": ["task1"],
            "blockers": ["blocker1"],
            "priority_factors": [{"factor": "urgency", "weight": 0.8}]
        },
        metadata={"domain": "professional"}
    ))
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    memory.semantic.store.store_concept = AsyncMock()
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    memory.episodic.store.store = AsyncMock()
    
    # Mock store_memory
    memory.store_memory = AsyncMock()
    memory.store = AsyncMock()
    
    # Mock analyze_tasks
    memory.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[{
            "statement": "Test task",
            "type": "task",
            "confidence": 0.9,
            "domain_relevance": 0.9
        }],
        confidence=0.9,
        dependencies={"blockers": []},
        metadata={"domain": "professional"}
    ))
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    world = MagicMock()
    world.notify_agent = AsyncMock()
    return world

@pytest.fixture
def task_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a TaskAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestTask_{request.node.name}"
    
    # Create agent with task-specific attributes
    attributes = {
        "occupation": "Task Analyst",
        "desires": [
            "Understand task requirements",
            "Track task dependencies",
            "Ensure task completion",
            "Maintain domain boundaries"
        ],
        "emotions": {
            "baseline": "focused",
            "towards_analysis": "systematic",
            "towards_domain": "mindful",
            "analysis_state": "neutral",
            "domain_state": "neutral"
        },
        "capabilities": [
            "task_analysis",
            "dependency_tracking",
            "domain_validation",
            "priority_assessment"
        ]
    }

    agent = TaskAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        attributes=attributes,
        domain="professional"
    )
    
    return agent

@pytest.mark.asyncio
async def test_initialization(task_agent):
    """Test agent initialization."""
    assert "TestTask" in task_agent.name
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
    
    # Verify memory storage was called
    mock_memory_system.store.assert_called()
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_any_call(
            content="High confidence task analysis achieved in professional domain",
            domain="professional"
        )

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
async def test_analyze_with_different_domains(task_agent, mock_memory_system):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Configure mock for professional domain
    mock_memory_system.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[{
            "statement": "Professional task",
            "type": "task",
            "confidence": 0.9,
            "domain_relevance": 0.9
        }],
        confidence=0.9,
        dependencies={"blockers": []},
        metadata={"domain": "professional"}
    ))
    
    # Test professional domain
    prof_result = await task_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    assert prof_result.confidence == 0.9
    
    # Configure mock for personal domain
    mock_memory_system.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[{
            "statement": "Personal task",
            "type": "task",
            "confidence": 0.9,
            "domain_relevance": 0.9
        }],
        confidence=0.9,
        dependencies={"blockers": []},
        metadata={"domain": "personal"}
    ))
    
    # Test personal domain
    pers_result = await task_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    assert pers_result.confidence == 0.9

@pytest.mark.asyncio
async def test_error_handling(task_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    # Configure mock analyze_tasks for error case
    mock_memory_system.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[],
        confidence=0.0,
        dependencies={},
        metadata={"error": "Test error", "error_type": "execution_failure"}
    ))
    
    result = await task_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, TaskResult)
    assert result.confidence == 0.0
    assert len(result.tasks) == 0
    assert "error" in result.metadata
    assert result.metadata["error_type"] == "execution_failure"

@pytest.mark.asyncio
async def test_reflection_recording(task_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Configure mock for high confidence case
    mock_memory_system.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[{
            "statement": "Important task",
            "type": "task",
            "confidence": 0.9,
            "domain_relevance": 0.9
        }],
        confidence=0.9,
        dependencies={"sequential": ["task1"], "blockers": []},
        metadata={"domain": "professional"}
    ))
    
    result = await task_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        content="High confidence task analysis achieved in professional domain",
        domain="professional"
    )
    
    # Configure mock for low confidence case
    mock_memory_system.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[{
            "statement": "Unclear task",
            "type": "task",
            "confidence": 0.2,
            "domain_relevance": 0.5
        }],
        confidence=0.2,
        dependencies={"sequential": [], "blockers": []},
        metadata={"domain": "professional"}
    ))
    
    result = await task_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        content="Low confidence task analysis - may need additional dependencies in professional domain",
        domain="professional"
    )

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
    
    # Configure mock for blocked task case
    mock_memory_system.analyze_tasks = AsyncMock(return_value=TaskResult(
        tasks=[{
            "statement": "Blocked task",
            "type": "task",
            "confidence": 0.9,
            "domain_relevance": 0.9
        }],
        confidence=0.9,
        dependencies={
            "sequential": ["task1"],
            "blockers": ["critical_blocker", "major_blocker"],
            "priority_factors": [{"factor": "urgency", "weight": 0.9}]
        },
        metadata={"domain": "professional"}
    ))
    
    result = await task_agent.analyze_and_store(content)
    
    # Verify blocker reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        content="Task blockers identified in professional domain - resolution required",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
