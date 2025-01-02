"""Tests for Nova's dialogue analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.dialogue import DialogueAgent, DialogueResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "utterances": [
            {
                "statement": "Key dialogue point",
                "type": "core_utterance",
                "description": "Important statement",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "sentiment": 0.7,
                "intent": "inform",
                "speaker": "user"
            }
        ],
        "context": {
            "conversation_history": [
                {
                    "content": "Previous statement",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "speaker": "assistant"
                }
            ],
            "participants": ["user", "assistant"],
            "topics": ["main_topic"],
            "domain_factors": {
                "relevance": "high",
                "formality": "medium"
            },
            "flow_factors": [
                {
                    "factor": "coherence",
                    "weight": 0.8
                }
            ]
        }
    })
    return llm

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Previous dialogue"},
            "timestamp": "2024-01-01T00:00:00Z",
            "speaker": "user"
        }
    ])
    return store

@pytest.fixture
def dialogue_agent(mock_llm, mock_vector_store):
    """Create a DialogueAgent instance with mock dependencies."""
    return DialogueAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_dialogue_with_llm(dialogue_agent, mock_llm):
    """Test dialogue analysis using LLM."""
    content = {
        "content": "Dialogue content to analyze",
        "type": "dialogue",
        "conversation_id": "test-123"
    }
    
    result = await dialogue_agent.analyze_dialogue(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, DialogueResult)
    assert len(result.utterances) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.context is not None

@pytest.mark.asyncio
async def test_analyze_dialogue_without_llm():
    """Test dialogue analysis without LLM (fallback mode)."""
    agent = DialogueAgent()  # No LLM provided
    content = {
        "content": "User says this and asks that",
        "context": {"setting": "conversation"}
    }
    
    result = await agent.analyze_dialogue(content)
    
    # Verify basic analysis worked
    assert isinstance(result, DialogueResult)
    assert len(result.utterances) > 0
    assert any(u["type"] == "inferred_utterance" for u in result.utterances)
    assert result.confidence >= 0
    assert "conversation_history" not in result.context  # No vector store

@pytest.mark.asyncio
async def test_get_conversation_history(dialogue_agent, mock_vector_store):
    """Test conversation history retrieval."""
    content = {
        "content": "test content",
        "conversation_id": "test-123"
    }
    
    history = await dialogue_agent._get_conversation_history(content)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test-123",
        limit=10,
        metadata_filter={
            "domain": "professional",
            "type": "dialogue"
        }
    )
    assert len(history) == 1
    assert "content" in history[0]
    assert history[0]["speaker"] == "user"

def test_basic_analysis(dialogue_agent):
    """Test basic dialogue analysis without LLM."""
    content = {
        "content": "User says X and asks Y",
        "context": {
            "setting": "conversation"
        }
    }
    
    conversation_history = [
        {
            "content": {"content": "Previous statement"},
            "timestamp": "2024-01-01T00:00:00Z",
            "speaker": "assistant"
        }
    ]
    
    result = dialogue_agent._basic_analysis(content, conversation_history)
    
    assert "utterances" in result
    assert "context" in result
    assert len(result["utterances"]) == 2  # "says" and "asks"
    assert all(u["type"] == "inferred_utterance" for u in result["utterances"])
    assert "conversation_history" in result["context"]

def test_extract_utterances(dialogue_agent):
    """Test utterance extraction and validation."""
    analysis = {
        "utterances": [
            {
                "statement": "Valid",
                "type": "core_utterance",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "sentiment": 0.7,
                "intent": "inform",
                "speaker": "user"
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    utterances = dialogue_agent._extract_utterances(analysis)
    
    assert len(utterances) == 2  # Invalid one should be filtered out
    assert all("type" in u for u in utterances)
    assert any(u["type"] == "utterance" for u in utterances)  # Default type
    assert any("domain_relevance" in u for u in utterances)
    assert any("sentiment" in u for u in utterances)

def test_extract_context(dialogue_agent):
    """Test context extraction and validation."""
    analysis = {
        "context": {
            "conversation_history": [
                {
                    "content": "statement1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "speaker": "user"
                }
            ],
            "participants": ["user", "assistant"],
            "topics": ["topic1", "topic2"],
            "domain_factors": {
                "relevance": "high",
                "formality": "medium"
            },
            "flow_factors": [
                {
                    "factor": "coherence",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    context = dialogue_agent._extract_context(analysis)
    
    assert "conversation_history" in context
    assert "participants" in context
    assert "topics" in context
    assert "domain_factors" in context
    assert "flow_factors" in context
    assert len(context["participants"]) == 2
    assert len(context["flow_factors"]) == 1
    assert "invalid" not in context

def test_calculate_confidence(dialogue_agent):
    """Test confidence calculation."""
    utterances = [
        {
            "confidence": 0.8,
            "sentiment": 0.7
        },
        {
            "confidence": 0.6,
            "sentiment": 0.8
        }
    ]
    
    context = {
        "conversation_history": [
            {
                "content": "statement1",
                "timestamp": "2024-01-01T00:00:00Z",
                "speaker": "user"
            }
        ],
        "participants": ["user", "assistant"],
        "topics": ["topic1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "flow_factors": [
            {
                "factor": "coherence",
                "weight": 0.8
            }
        ]
    }
    
    confidence = dialogue_agent._calculate_confidence(utterances, context)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Utterance confidence (0.7 average)
    # - History (0.2 from 1 entry)
    # - Participants (0.3 from 2 participants)
    # - Topics (0.1 from 1 topic)
    # - Domain factors (0.2 from 2 factors)
    # - Flow factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

@pytest.mark.asyncio
async def test_error_handling(dialogue_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    dialogue_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await dialogue_agent.analyze_dialogue({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, DialogueResult)
    assert result.confidence == 0.0
    assert len(result.utterances) == 0
    assert "error" in result.metadata
    assert "error" in result.context

@pytest.mark.asyncio
async def test_domain_awareness(dialogue_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await dialogue_agent.analyze_dialogue(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    dialogue_agent.domain = "personal"
    result = await dialogue_agent.analyze_dialogue(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
