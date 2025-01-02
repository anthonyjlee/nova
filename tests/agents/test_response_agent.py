"""Tests for the specialized ResponseAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.response_agent import ResponseAgent
from src.nia.nova.core.response import ResponseResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "components": [
            {
                "statement": "Key point",
                "type": "component",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "intent": "inform"
            },
            {
                "statement": "Need improvement",
                "type": "response_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "structure": {
            "similar_responses": [
                {
                    "content": "Related response",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "quality_factors": [
                {
                    "factor": "clarity",
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
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar response"},
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
def response_agent(mock_memory_system, mock_world):
    """Create a ResponseAgent instance with mock dependencies."""
    return ResponseAgent(
        name="TestResponse",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(response_agent):
    """Test agent initialization."""
    assert response_agent.name == "TestResponse"
    assert response_agent.domain == "professional"
    assert response_agent.agent_type == "response"
    
    # Verify attributes were initialized
    attributes = response_agent.get_attributes()
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
async def test_process_content(response_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await response_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in response_agent.emotions
    assert "domain_state" in response_agent.emotions
    assert any("Improve" in desire for desire in response_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(response_agent, mock_memory_system):
    """Test response analysis with domain awareness."""
    content = {
        "content": "Response content to analyze",
        "type": "response"
    }
    
    result = await response_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ResponseResult)
    assert len(result.components) > 0
    assert result.confidence > 0
    assert result.structure is not None
    
    # Verify memory storage
    assert hasattr(response_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(response_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await response_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await response_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(response_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await response_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await response_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(response_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await response_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, ResponseResult)
    assert result.confidence == 0.0
    assert len(result.components) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(response_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await response_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await response_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(response_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await response_agent.process(content)
    
    # Verify emotion updates
    assert response_agent.emotions["analysis_state"] == "positive"
    assert response_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(response_agent):
    """Test desire updates based on response needs."""
    content = {"text": "Test content"}
    
    await response_agent.process(content)
    
    # Verify desire updates
    assert any("Improve" in desire for desire in response_agent.desires)

@pytest.mark.asyncio
async def test_quality_factor_reflection(response_agent, mock_memory_system):
    """Test reflection recording for quality factors."""
    content = {"content": "test"}
    
    # Ensure quality factors exist
    mock_memory_system.llm.analyze.return_value["structure"]["quality_factors"] = [
        {
            "factor": "clarity",
            "weight": 0.8
        }
    ]
    
    result = await response_agent.analyze_and_store(content)
    
    # Verify quality factor reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Quality factors" in str(call) for call in reflection_calls)

if __name__ == "__main__":
    pytest.main([__file__])
