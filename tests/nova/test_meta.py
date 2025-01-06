"""Tests for Nova's meta-orchestration functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.meta import MetaAgent, MetaResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "response": "Synthesized response",
        "concepts": [
            {
                "name": "TestConcept",
                "type": "synthesis",
                "description": "A test concept",
                "confidence": 0.8
            }
        ],
        "key_points": [
            "This is a key point",
            "This is another key point"
        ]
    })
    return llm

@pytest.fixture
def mock_store():
    """Create a mock store."""
    store = MagicMock()
    store.store_memory = AsyncMock()
    return store

@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = MagicMock()
    agent.process = AsyncMock(return_value=MagicMock(
        concepts=[{"name": "AgentConcept", "type": "test"}],
        key_points=["Agent key point"],
        confidence=0.7
    ))
    agent.get_domain_access = AsyncMock(return_value=True)
    return agent

@pytest.fixture
def meta_agent(mock_llm, mock_store, mock_agent):
    """Create a MetaAgent instance with mock dependencies."""
    return MetaAgent(
        llm=mock_llm,
        store=mock_store,
        vector_store=MagicMock(),
        agents={"test_agent": mock_agent}
    )

@pytest.mark.asyncio
async def test_process_interaction(meta_agent, mock_llm):
    """Test processing an interaction with LLM."""
    result = await meta_agent.process_interaction("Test content")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, MetaResult)
    assert result.response == "Synthesized response"
    assert len(result.concepts) == 1
    assert len(result.key_points) == 2
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata
    assert "agent_count" in result.metadata

@pytest.mark.asyncio
async def test_process_interaction_without_llm(mock_agent):
    """Test processing without LLM (fallback mode)."""
    agent = MetaAgent(agents={"test_agent": mock_agent})
    result = await agent.process_interaction("Test content")
    
    # Verify basic synthesis worked
    assert isinstance(result, MetaResult)
    assert result.response == "Synthesized response from multiple agents"
    assert len(result.concepts) > 0
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1

@pytest.mark.asyncio
async def test_gather_agent_responses(meta_agent, mock_agent):
    """Test gathering responses from agents."""
    meta_agent.agents = {"test_agent": mock_agent}  # mock_agent is now properly injected as fixture
    responses = await meta_agent._gather_agent_responses("Test content", {"domain": "professional"})
    
    # Verify agent was called
    mock_agent.process.assert_called_once()
    assert "test_agent" in responses

@pytest.mark.asyncio
async def test_domain_access_check(meta_agent, mock_agent):
    """Test domain access checking during response gathering."""
    # Set up agent to deny access
    mock_agent.get_domain_access.return_value = False
    meta_agent.agents = {"test_agent": mock_agent}
    
    responses = await meta_agent._gather_agent_responses("Test content", {"domain": "restricted"})
    
    # Verify agent was not processed due to domain restriction
    assert not responses
    mock_agent.process.assert_not_called()

@pytest.mark.asyncio
async def test_error_handling(meta_agent):
    """Test error handling during processing."""
    # Make LLM raise an error
    meta_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await meta_agent.process_interaction("Test content")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, MetaResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata

def test_basic_synthesis(meta_agent):
    """Test basic synthesis without LLM."""
    agent_responses = {
        "agent1": MagicMock(
            concepts=[{"name": "Concept1", "type": "test"}],
            key_points=["Point1"]
        ),
        "agent2": MagicMock(
            concepts=[{"name": "Concept2", "type": "test"}],
            key_points=["Point2"]
        )
    }
    
    synthesis = meta_agent._basic_synthesis("Test content", agent_responses)
    
    assert "response" in synthesis
    assert len(synthesis["concepts"]) == 2
    assert len(synthesis["key_points"]) == 2

def test_extract_concepts(meta_agent):
    """Test concept extraction and validation."""
    synthesis = {
        "concepts": [
            {
                "name": "Valid",
                "type": "test",
                "confidence": 0.8
            },
            {
                "name": "NoType"  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    concepts = meta_agent._extract_concepts(synthesis)
    
    assert len(concepts) == 2  # Invalid one should be filtered out
    assert all("type" in c for c in concepts)
    assert any(c["type"] == "synthesis" for c in concepts)  # Default type
    assert all("confidence" in c for c in concepts)
    assert all(isinstance(c["confidence"], (int, float)) for c in concepts)
    assert all(0 <= c["confidence"] <= 1 for c in concepts)

@pytest.mark.asyncio
async def test_record_synthesis(meta_agent, mock_store):
    """Test recording synthesis results."""
    result = MetaResult(
        response="Test response",
        concepts=[{"name": "TestConcept", "type": "test"}],
        key_points=["Test point"],
        confidence=0.8,
        metadata={"domain": "professional"}
    )
    
    await meta_agent.record_synthesis(result)
    
    # Verify memory was stored
    mock_store.store_memory.assert_called_once()
    call_args = mock_store.store_memory.call_args[1]
    assert call_args["content"]["type"] == "synthesis"
    assert call_args["domain"] == meta_agent.domain

def test_calculate_confidence(meta_agent):
    """Test confidence calculation."""
    concepts = [
        {"confidence": 0.8},
        {"confidence": 0.6}
    ]
    
    agent_responses = {
        "agent1": MagicMock(confidence=0.7),
        "agent2": MagicMock(confidence=0.9)
    }
    
    confidence = meta_agent._calculate_confidence(concepts, agent_responses)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should be weighted average: (0.6 * 0.7 + 0.4 * 0.8) ≈ 0.74
    assert 0.73 <= confidence <= 0.75

if __name__ == "__main__":
    pytest.main([__file__])
