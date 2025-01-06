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
    assert isinstance(result, DialogueResult), "Result should be a DialogueResult instance"
    
    # Verify utterances
    assert isinstance(result.utterances, list), "Utterances should be a list"
    assert len(result.utterances) >= 1, "Should have at least one utterance"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata and context
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata and result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"
    assert result.context is not None and isinstance(result.context, dict), \
        "Context should be a non-null dictionary"

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
    assert isinstance(result, DialogueResult), "Result should be a DialogueResult instance"
    
    # Verify utterances
    assert isinstance(result.utterances, list), "Utterances should be a list"
    assert len(result.utterances) >= 1, "Should have at least one utterance"
    assert any(u["type"] == "inferred_utterance" for u in result.utterances), \
        "Should have at least one inferred utterance"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify context without vector store
    assert isinstance(result.context, dict), "Context should be a dictionary"
    assert "conversation_history" not in result.context, \
        "Should not have conversation history without vector store"

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
    
    # Verify we got history back
    assert isinstance(history, list), "Should return a list of history items"
    assert len(history) >= 1, "Should have at least one history item"
    
    # Verify history item structure
    history_item = history[0]
    assert isinstance(history_item, dict), "Each history item should be a dictionary"
    assert "content" in history_item, "Each history item should have content"
    assert "speaker" in history_item, "Each history item should have a speaker"
    assert history_item["speaker"] == "user", "Speaker should match expected value"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "utterances" in result, "Result should contain utterances"
    assert "context" in result, "Result should contain context"
    
    # Verify utterances
    assert isinstance(result["utterances"], list), "Utterances should be a list"
    assert len(result["utterances"]) >= 2, "Should identify both 'says' and 'asks' utterances"
    assert all(u["type"] == "inferred_utterance" for u in result["utterances"]), \
        "Each utterance should be of type inferred_utterance"
    
    # Verify context
    assert isinstance(result["context"], dict), "Context should be a dictionary"
    assert "conversation_history" in result["context"], \
        "Context should contain conversation history"
    assert isinstance(result["context"]["conversation_history"], list), \
        "Conversation history should be a list"

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
    
    # Verify we got valid utterances (filtering out invalid ones)
    assert len(utterances) >= 1, "Should have at least one valid utterance"
    
    # Verify each utterance has required fields
    for utterance in utterances:
        assert isinstance(utterance, dict), "Each utterance should be a dictionary"
        assert "type" in utterance, "Each utterance should have a type"
        assert isinstance(utterance.get("confidence", 0.0), (int, float)), \
            "Confidence should be numeric"
        assert 0 <= utterance.get("confidence", 0.0) <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify utterance types
    assert any(u["type"] == "utterance" for u in utterances), \
        "Should have at least one default 'utterance' type"
    
    # Verify at least one utterance has extended fields
    assert any("domain_relevance" in u or "sentiment" in u for u in utterances), \
        "At least one utterance should have domain_relevance or sentiment"

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
    
    # Verify basic structure
    assert isinstance(context, dict), "Context should be a dictionary"
    
    # Verify required fields are present
    required_fields = ["conversation_history", "participants", "topics", "domain_factors", "flow_factors"]
    for field in required_fields:
        assert field in context, f"Context should contain {field}"
    
    # Verify field contents
    assert isinstance(context["conversation_history"], list), "Conversation history should be a list"
    assert isinstance(context["participants"], list), "Participants should be a list"
    assert len(context["participants"]) >= 2, "Should have at least two participants"
    
    assert isinstance(context["topics"], list), "Topics should be a list"
    assert len(context["topics"]) >= 1, "Should have at least one topic"
    
    assert isinstance(context["domain_factors"], dict), "Domain factors should be a dictionary"
    assert len(context["domain_factors"]) >= 1, "Should have at least one domain factor"
    
    assert isinstance(context["flow_factors"], list), "Flow factors should be a list"
    assert len(context["flow_factors"]) >= 1, "Should have at least one flow factor"
    
    # Verify invalid fields are filtered out
    assert "invalid" not in context, "Invalid fields should be filtered out"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence utterances (0.8, 0.6) and a structured context,
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"
    
    # Test with empty inputs
    empty_confidence = dialogue_agent._calculate_confidence([], {})
    assert isinstance(empty_confidence, (int, float)), "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"
    
    # Test with partial inputs
    partial_confidence = dialogue_agent._calculate_confidence(utterances, {})
    assert isinstance(partial_confidence, (int, float)), "Partial confidence should be numeric"
    assert 0 <= partial_confidence <= 1, "Partial confidence should be between 0 and 1"
    assert partial_confidence < confidence, \
        "Partial input should result in lower confidence than full input"

@pytest.mark.asyncio
async def test_error_handling(dialogue_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    dialogue_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await dialogue_agent.analyze_dialogue({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, DialogueResult), "Result should be a DialogueResult instance"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.utterances) == 0, "Should have no utterances when error occurs"
    
    # Verify error state
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    
    assert isinstance(result.context, dict), "Context should be a dictionary"
    assert "error" in result.context, "Context should contain error information"
    assert isinstance(result.context["error"], str), "Context error should be a string"

@pytest.mark.asyncio
async def test_domain_awareness(dialogue_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    
    # Test initial domain
    result = await dialogue_agent.analyze_dialogue(content)
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test domain change
    dialogue_agent.domain = "personal"
    result = await dialogue_agent.analyze_dialogue(content)
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"
    
    # Verify domain affects analysis
    assert isinstance(result.context, dict), "Result should have context dictionary"
    assert result.context is not None, "Context should not be null after domain change"

if __name__ == "__main__":
    pytest.main([__file__])
