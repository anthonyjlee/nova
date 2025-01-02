"""Tests for the specialized ResearchAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.research_agent import ResearchAgent
from src.nia.nova.core.research import ResearchResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "findings": [
            {
                "statement": "Key finding",
                "type": "finding",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "novelty": 0.9
            },
            {
                "statement": "Need more data",
                "type": "research_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "sources": {
            "similar_memories": [
                {
                    "content": "Related finding",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "references": ["ref1"]
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
            "content": {"content": "Similar content"},
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
def research_agent(mock_memory_system, mock_world):
    """Create a ResearchAgent instance with mock dependencies."""
    return ResearchAgent(
        name="TestResearch",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(research_agent):
    """Test agent initialization."""
    assert research_agent.name == "TestResearch"
    assert research_agent.domain == "professional"
    assert research_agent.agent_type == "research"
    
    # Verify attributes were initialized
    attributes = research_agent.get_attributes()
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
async def test_process_content(research_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await research_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in research_agent.emotions
    assert "domain_state" in research_agent.emotions
    assert any("Investigate" in desire for desire in research_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(research_agent, mock_memory_system):
    """Test research analysis with domain awareness."""
    content = {
        "content": "Research content to analyze",
        "type": "research"
    }
    
    result = await research_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ResearchResult)
    assert len(result.findings) > 0
    assert result.confidence > 0
    assert result.sources is not None
    
    # Verify memory storage
    assert hasattr(research_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(research_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await research_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await research_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(research_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await research_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await research_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(research_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await research_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, ResearchResult)
    assert result.confidence == 0.0
    assert len(result.findings) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(research_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(research_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await research_agent.process(content)
    
    # Verify emotion updates
    assert research_agent.emotions["analysis_state"] == "positive"
    assert research_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(research_agent):
    """Test desire updates based on research needs."""
    content = {"text": "Test content"}
    
    await research_agent.process(content)
    
    # Verify desire updates
    assert any("Investigate" in desire for desire in research_agent.desires)

@pytest.mark.asyncio
async def test_novelty_reflection(research_agent, mock_memory_system):
    """Test reflection recording for novel findings."""
    content = {"content": "test"}
    
    # Ensure novel findings exist
    mock_memory_system.llm.analyze.return_value["findings"][0]["novelty"] = 0.9
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify novelty reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Novel research findings" in str(call) for call in reflection_calls)

if __name__ == "__main__":
    pytest.main([__file__])
