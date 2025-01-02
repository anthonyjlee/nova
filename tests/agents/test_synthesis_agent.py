"""Tests for the specialized SynthesisAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.synthesis_agent import SynthesisAgent
from src.nia.nova.core.synthesis import SynthesisResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "synthesis": {
            "type": "analysis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content"
                }
            }
        },
        "conclusions": [
            {
                "type": "theme",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "synthesis_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_theme",
                "severity": "medium",
                "description": "Missing theme",
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
            "content": {"content": "Similar synthesis"},
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
def synthesis_agent(mock_memory_system, mock_world):
    """Create a SynthesisAgent instance with mock dependencies."""
    return SynthesisAgent(
        name="TestSynthesis",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(synthesis_agent):
    """Test agent initialization."""
    assert synthesis_agent.name == "TestSynthesis"
    assert synthesis_agent.domain == "professional"
    assert synthesis_agent.agent_type == "synthesis"
    
    # Verify attributes were initialized
    attributes = synthesis_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify synthesis-specific attributes
    assert "Combine insights effectively" in attributes["desires"]
    assert "towards_content" in attributes["emotions"]
    assert "content_synthesis" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(synthesis_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await synthesis_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "synthesis_state" in synthesis_agent.emotions
    assert "domain_state" in synthesis_agent.emotions
    assert any("Explore" in desire for desire in synthesis_agent.desires)

@pytest.mark.asyncio
async def test_synthesize_and_store(synthesis_agent, mock_memory_system):
    """Test content synthesis with domain awareness."""
    content = {
        "text": "Content to synthesize",
        "type": "analysis"
    }
    
    result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, SynthesisResult)
    assert result.synthesis["type"] == "analysis"
    assert len(result.synthesis["components"]) == 1
    assert len(result.conclusions) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(synthesis_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(synthesis_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await synthesis_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await synthesis_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_synthesize_with_different_domains(synthesis_agent):
    """Test synthesis with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(synthesis_agent, mock_memory_system):
    """Test error handling during synthesis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await synthesis_agent.synthesize_and_store(
        {"content": "test"},
        synthesis_type="analysis"
    )
    
    # Verify error handling
    assert isinstance(result, SynthesisResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.conclusions) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(synthesis_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["conclusions"] = [
        {
            "type": "test_conclusion",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["conclusions"] = [
        {
            "type": "test_conclusion",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Synthesis failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(synthesis_agent, mock_memory_system):
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
    
    result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical synthesis issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_conclusion_reflection(synthesis_agent, mock_memory_system):
    """Test reflection recording for important conclusions."""
    content = {"text": "test"}
    
    # Add important conclusion
    mock_memory_system.llm.analyze.return_value["conclusions"] = [
        {
            "type": "important_conclusion",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical conclusion"
        }
    ]
    
    result = await synthesis_agent.synthesize_and_store(
        content,
        synthesis_type="analysis"
    )
    
    # Verify important conclusion reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important conclusions drawn" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(synthesis_agent):
    """Test emotion updates based on synthesis results."""
    content = {"text": "Test content"}
    
    await synthesis_agent.process(content)
    
    # Verify emotion updates
    assert "synthesis_state" in synthesis_agent.emotions
    assert "domain_state" in synthesis_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(synthesis_agent):
    """Test desire updates based on synthesis needs."""
    content = {"text": "Test content"}
    
    await synthesis_agent.process(content)
    
    # Verify desire updates
    assert any("Explore" in desire for desire in synthesis_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
