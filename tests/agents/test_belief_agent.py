"""Tests for the specialized BeliefAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.belief_agent import BeliefAgent
from src.nia.nova.core.belief import BeliefResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "beliefs": [
            {
                "statement": "This is important",
                "type": "belief",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9
            },
            {
                "statement": "Further investigation needed",
                "type": "belief_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "evidence": {
            "sources": ["document1"],
            "supporting_facts": ["fact1"],
            "contradictions": ["contra1"]
        }
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    memory.semantic.store.store_concept = AsyncMock()
    memory.semantic.store.store_memory = AsyncMock()
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    memory.episodic.store.store = AsyncMock()
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def belief_agent(mock_memory_system, mock_world, request):
    """Create a BeliefAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestBelief_{request.node.name}"
    return BeliefAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(belief_agent):
    """Test agent initialization."""
    assert "TestBelief" in belief_agent.name
    assert belief_agent.domain == "professional"
    assert belief_agent.agent_type == "belief"
    
    # Verify attributes were initialized
    attributes = belief_agent.get_attributes()
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
async def test_process_content(belief_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await belief_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in belief_agent.emotions
    assert "domain_state" in belief_agent.emotions
    assert any("Investigate" in desire for desire in belief_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(belief_agent, mock_memory_system):
    """Test belief analysis with domain awareness."""
    content = {
        "content": "I believe this is important",
        "type": "statement"
    }
    
    result = await belief_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, BeliefResult)
    assert len(result.beliefs) > 0
    assert result.confidence > 0
    assert result.evidence is not None
    
    # Verify memory storage
    assert hasattr(belief_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(belief_agent, mock_memory_system):
    """Test domain access validation."""
    # Mock domain access based on domain
    async def mock_domain_access(agent_name, domain):
        if domain == "professional":
            return False  # Deny professional domain for test
        return True  # Allow other domains
        
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(side_effect=mock_domain_access)
    
    # Test denied domain
    with pytest.raises(PermissionError):
        await belief_agent.validate_domain_access("professional")
        
    # Test allowed domain
    await belief_agent.validate_domain_access("personal")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(belief_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Mock domain access
    async def mock_domain_access(agent_name, domain):
        if domain == "professional":
            return False
        return True
        
    belief_agent.memory_system.semantic.store.get_domain_access = AsyncMock(side_effect=mock_domain_access)
    
    # Test professional domain (should fail)
    with pytest.raises(PermissionError):
        await belief_agent.analyze_and_store(
            content,
            target_domain="professional"
        )
    
    # Test personal domain (should succeed)
    pers_result = await belief_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(belief_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await belief_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, BeliefResult)
    assert result.confidence == 0.0
    assert len(result.beliefs) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(belief_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await belief_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await belief_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(belief_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await belief_agent.process(content)
    
    # Verify emotion updates
    assert belief_agent.emotions["analysis_state"] == "positive"
    assert belief_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(belief_agent):
    """Test desire updates based on belief needs."""
    content = {"text": "Test content"}
    
    await belief_agent.process(content)
    
    # Verify desire updates
    assert any("Investigate" in desire for desire in belief_agent.desires)

@pytest.mark.asyncio
async def test_contradiction_reflection(belief_agent, mock_memory_system):
    """Test reflection recording for contradictions."""
    content = {"content": "test"}
    
    # Ensure contradictions exist in evidence
    mock_memory_system.llm.analyze.return_value["evidence"]["contradictions"] = ["contra1"]
    
    result = await belief_agent.analyze_and_store(content)
    
    # Verify contradiction reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Contradictory evidence" in str(call) for call in reflection_calls)

if __name__ == "__main__":
    pytest.main([__file__])
