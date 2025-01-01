"""Tests for the specialized ContextAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.context_agent import ContextAgent
from src.nia.nova.core.context import ContextResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "name": "TestContext",
                "type": "environment",
                "description": "stable",
                "confidence": 0.8,
                "domain_relevance": 0.9
            },
            {
                "name": "TestNeed",
                "type": "context_need",
                "description": "investigation needed",
                "confidence": 0.7
            }
        ],
        "key_points": ["Test point"],
        "environment": {
            "type": "test",
            "mode": "development"
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
def context_agent(mock_memory_system, mock_world):
    """Create a ContextAgent instance with mock dependencies."""
    return ContextAgent(
        name="TestContext",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(context_agent):
    """Test agent initialization."""
    assert context_agent.name == "TestContext"
    assert context_agent.domain == "professional"
    assert context_agent.agent_type == "context"
    
    # Verify attributes were initialized
    attributes = context_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify domain-specific attributes
    assert "Maintain domain awareness" in attributes["desires"]
    assert "towards_domain" in attributes["emotions"]
    assert "domain_awareness" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(context_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await context_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "environmental_state" in context_agent.emotions
    assert "domain_state" in context_agent.emotions
    assert any("Investigate" in desire for desire in context_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(context_agent, mock_memory_system):
    """Test context analysis with domain awareness."""
    context = {
        "type": "test",
        "environment": {"mode": "test"}
    }
    
    result = await context_agent.analyze_and_store(
        context,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ContextResult)
    assert len(result.concepts) > 0
    assert len(result.key_points) > 0
    assert result.environment is not None
    
    # Verify memory storage
    assert hasattr(context_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(context_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await context_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await context_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(context_agent):
    """Test analysis with different domain configurations."""
    context = {"type": "test"}
    
    # Test professional domain
    prof_result = await context_agent.analyze_and_store(
        context,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await context_agent.analyze_and_store(
        context,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(context_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await context_agent.analyze_and_store({"test": "value"})
    
    # Verify error handling
    assert isinstance(result, ContextResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(context_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    context = {"type": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await context_agent.analyze_and_store(context)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await context_agent.analyze_and_store(context)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(context_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await context_agent.process(content)
    
    # Verify emotion updates
    assert context_agent.emotions["environmental_state"] == "stable"
    assert context_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(context_agent):
    """Test desire updates based on context needs."""
    content = {"text": "Test content"}
    
    await context_agent.process(content)
    
    # Verify desire updates
    assert any("Investigate TestNeed" in desire for desire in context_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
