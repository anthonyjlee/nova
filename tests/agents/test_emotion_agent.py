"""Tests for the specialized EmotionAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.emotion_agent import EmotionAgent
from src.nia.nova.core.emotion import EmotionResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "emotions": [
            {
                "name": "joy",
                "type": "emotion",
                "description": "positive",
                "intensity": 0.8,
                "confidence": 0.9,
                "domain_appropriateness": 0.9
            },
            {
                "name": "interest",
                "type": "emotional_need",
                "description": "requires attention",
                "intensity": 0.7,
                "confidence": 0.8
            }
        ],
        "context": {
            "triggers": ["achievement"],
            "background": "project success"
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
def emotion_agent(mock_memory_system, mock_world):
    """Create an EmotionAgent instance with mock dependencies."""
    return EmotionAgent(
        name="TestEmotion",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(emotion_agent):
    """Test agent initialization."""
    assert emotion_agent.name == "TestEmotion"
    assert emotion_agent.domain == "professional"
    assert emotion_agent.agent_type == "emotion"
    
    # Verify attributes were initialized
    attributes = emotion_agent.get_attributes()
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
async def test_process_content(emotion_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await emotion_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in emotion_agent.emotions
    assert "domain_state" in emotion_agent.emotions
    assert any("Address" in desire for desire in emotion_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(emotion_agent, mock_memory_system):
    """Test emotion analysis with domain awareness."""
    content = {
        "content": "I'm very happy with the results!",
        "type": "feedback"
    }
    
    result = await emotion_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, EmotionResult)
    assert len(result.emotions) > 0
    assert result.intensity > 0
    assert result.confidence > 0
    assert result.context is not None
    
    # Verify memory storage
    assert hasattr(emotion_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(emotion_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await emotion_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await emotion_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(emotion_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await emotion_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await emotion_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(emotion_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await emotion_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, EmotionResult)
    assert result.confidence == 0.0
    assert result.intensity == 0.0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(emotion_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await emotion_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await emotion_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(emotion_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await emotion_agent.process(content)
    
    # Verify emotion updates
    assert emotion_agent.emotions["analysis_state"] == "positive"
    assert emotion_agent.emotions["domain_state"] == "highly_appropriate"

@pytest.mark.asyncio
async def test_desire_updates(emotion_agent):
    """Test desire updates based on emotional needs."""
    content = {"text": "Test content"}
    
    await emotion_agent.process(content)
    
    # Verify desire updates
    assert any("Address interest" in desire for desire in emotion_agent.desires)

@pytest.mark.asyncio
async def test_intensity_reflection(emotion_agent, mock_memory_system):
    """Test reflection recording for high intensity emotions."""
    content = {"content": "test"}
    
    # Force high intensity result
    mock_memory_system.llm.analyze.return_value["emotions"][0]["intensity"] = 0.9
    
    result = await emotion_agent.analyze_and_store(content)
    
    # Verify intensity reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High intensity" in str(call) for call in reflection_calls)

if __name__ == "__main__":
    pytest.main([__file__])
