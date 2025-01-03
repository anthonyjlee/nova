"""Tests for the specialized ReflectionAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.reflection_agent import ReflectionAgent
from src.nia.nova.core.reflection import ReflectionResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "insights": [
            {
                "statement": "Key insight",
                "type": "insight",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "impact": 0.7
            },
            {
                "statement": "Need to learn more",
                "type": "learning_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "patterns": {
            "similar_reflections": [
                {
                    "content": "Related insight",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "recurring_themes": ["theme1"]
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
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar reflection"},
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
def reflection_agent(mock_memory_system, mock_world, request):
    """Create a ReflectionAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestReflection_{request.node.name}"
    return ReflectionAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(reflection_agent):
    """Test agent initialization."""
    assert "TestReflection" in reflection_agent.name
    assert reflection_agent.domain == "professional"
    assert reflection_agent.agent_type == "reflection"
    
    # Verify attributes were initialized
    attributes = reflection_agent.get_attributes()
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
async def test_process_content(reflection_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await reflection_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in reflection_agent.emotions
    assert "domain_state" in reflection_agent.emotions
    assert any("Explore" in desire for desire in reflection_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(reflection_agent, mock_memory_system):
    """Test reflection analysis with domain awareness."""
    content = {
        "content": "Reflection content to analyze",
        "type": "reflection"
    }
    
    result = await reflection_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ReflectionResult)
    assert len(result.insights) > 0
    assert result.confidence > 0
    assert result.patterns is not None
    
    # Verify memory storage
    assert hasattr(reflection_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(reflection_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await reflection_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await reflection_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(reflection_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await reflection_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await reflection_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(reflection_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await reflection_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, ReflectionResult)
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(reflection_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await reflection_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await reflection_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(reflection_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await reflection_agent.process(content)
    
    # Verify emotion updates
    assert reflection_agent.emotions["analysis_state"] == "positive"
    assert reflection_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(reflection_agent):
    """Test desire updates based on learning needs."""
    content = {"text": "Test content"}
    
    await reflection_agent.process(content)
    
    # Verify desire updates
    assert any("Explore" in desire for desire in reflection_agent.desires)

@pytest.mark.asyncio
async def test_recurring_themes_reflection(reflection_agent, mock_memory_system):
    """Test reflection recording for recurring themes."""
    content = {"content": "test"}
    
    # Ensure recurring themes exist
    mock_memory_system.llm.analyze.return_value["patterns"]["recurring_themes"] = ["theme1"]
    
    result = await reflection_agent.analyze_and_store(content)
    
    # Verify recurring themes reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Recurring themes" in str(call) for call in reflection_calls)

if __name__ == "__main__":
    pytest.main([__file__])
