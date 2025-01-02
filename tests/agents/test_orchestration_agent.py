"""Tests for the specialized OrchestrationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.orchestration_agent import OrchestrationAgent
from src.nia.nova.core.orchestration import OrchestrationResult

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
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main agent"
                }
            }
        },
        "decisions": [
            {
                "type": "flow",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "orchestration_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_flow",
                "severity": "medium",
                "description": "Missing flow",
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
            "content": {"content": "Similar orchestration"},
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
    """Test agent initialization."""
    assert orchestration_agent.name == "TestOrchestration"
    assert orchestration_agent.domain == "professional"
    assert orchestration_agent.agent_type == "orchestration"
    
    # Verify attributes were initialized
    attributes = orchestration_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify orchestration-specific attributes
    assert "Coordinate agents effectively" in attributes["desires"]
    assert "towards_agents" in attributes["emotions"]
    assert "agent_orchestration" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(orchestration_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await orchestration_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "orchestration_state" in orchestration_agent.emotions
    assert "domain_state" in orchestration_agent.emotions
    assert any("Coordinate" in desire for desire in orchestration_agent.desires)

@pytest.mark.asyncio
async def test_orchestrate_and_store(orchestration_agent, mock_memory_system):
    """Test agent orchestration with domain awareness."""
    content = {
        "text": "Content to orchestrate",
        "type": "sequential"
    }
    
    result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, OrchestrationResult)
    assert result.orchestration["type"] == "sequential"
    assert len(result.orchestration["agents"]) == 1
    assert len(result.decisions) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(orchestration_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(orchestration_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await orchestration_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await orchestration_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_orchestrate_with_different_domains(orchestration_agent):
    """Test orchestration with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(orchestration_agent, mock_memory_system):
    """Test error handling during orchestration."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await orchestration_agent.orchestrate_and_store(
        {"content": "test"},
        orchestration_type="sequential"
    )
    
    # Verify error handling
    assert isinstance(result, OrchestrationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.decisions) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(orchestration_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["decisions"] = [
        {
            "type": "test_decision",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["decisions"] = [
        {
            "type": "test_decision",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Orchestration failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(orchestration_agent, mock_memory_system):
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
    
    result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical orchestration issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_decision_reflection(orchestration_agent, mock_memory_system):
    """Test reflection recording for important decisions."""
    content = {"text": "test"}
    
    # Add important decision
    mock_memory_system.llm.analyze.return_value["decisions"] = [
        {
            "type": "important_decision",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical decision"
        }
    ]
    
    result = await orchestration_agent.orchestrate_and_store(
        content,
        orchestration_type="sequential"
    )
    
    # Verify important decision reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important agent coordination decisions" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(orchestration_agent):
    """Test emotion updates based on orchestration results."""
    content = {"text": "Test content"}
    
    await orchestration_agent.process(content)
    
    # Verify emotion updates
    assert "orchestration_state" in orchestration_agent.emotions
    assert "domain_state" in orchestration_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(orchestration_agent):
    """Test desire updates based on orchestration needs."""
    content = {"text": "Test content"}
    
    await orchestration_agent.process(content)
    
    # Verify desire updates
    assert any("Coordinate" in desire for desire in orchestration_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
