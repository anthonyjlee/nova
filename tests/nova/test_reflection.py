"""Tests for Nova's reflection analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.reflection import ReflectionAgent, ReflectionResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "insights": [
            {
                "statement": "Key insight",
                "type": "core_insight",
                "description": "Important realization",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "impact": 0.8,
                "novelty": 0.7,
                "status": "verified"
            }
        ],
        "patterns": {
            "similar_reflections": [
                {
                    "content": "Related reflection",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "recurring_themes": ["theme1", "theme2"],
            "connections": ["connection1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "learning_factors": [
                {
                    "factor": "understanding",
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
            "content": {"content": "Similar reflection"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def reflection_agent(mock_llm, mock_vector_store):
    """Create a ReflectionAgent instance with mock dependencies."""
    return ReflectionAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_reflection_with_llm(reflection_agent, mock_llm):
    """Test reflection analysis using LLM."""
    content = {
        "content": "Reflection content to analyze",
        "type": "reflection"
    }
    
    result = await reflection_agent.analyze_reflection(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ReflectionResult)
    assert len(result.insights) >= 1, "Should have at least one insight"
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    # Verify domain and patterns are present
    assert "domain" in result.metadata and result.metadata["domain"] == "professional"
    assert result.patterns is not None and isinstance(result.patterns, dict)

@pytest.mark.asyncio
async def test_analyze_reflection_without_llm():
    """Test reflection analysis without LLM (fallback mode)."""
    agent = ReflectionAgent()  # No LLM provided
    content = {
        "content": "I realized this and learned that",
        "context": {"setting": "reflection"}
    }
    
    result = await agent.analyze_reflection(content)
    
    # Verify basic analysis worked
    assert isinstance(result, ReflectionResult), "Result should be a ReflectionResult instance"
    assert len(result.insights) >= 1, "Should have at least one insight"
    assert any(i["type"] == "inferred_insight" for i in result.insights), \
        "Should have at least one inferred insight"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify patterns without vector store
    assert isinstance(result.patterns, dict), "Patterns should be a dictionary"
    assert "similar_reflections" not in result.patterns, \
        "Should not have similar_reflections without vector store"

@pytest.mark.asyncio
async def test_get_similar_reflections(reflection_agent, mock_vector_store):
    """Test similar reflection retrieval."""
    content = {"content": "test content"}
    
    reflections = await reflection_agent._get_similar_reflections(content)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "reflection"
        }
    )
    # Verify we got reflections back
    assert isinstance(reflections, list), "Should return a list of reflections"
    assert len(reflections) >= 1, "Should have at least one reflection"
    
    # Verify reflection structure
    reflection = reflections[0]
    assert isinstance(reflection, dict), "Each reflection should be a dictionary"
    assert "content" in reflection, "Each reflection should have content"
    assert isinstance(reflection.get("similarity", 0.0), (int, float)), \
        "Similarity should be numeric"
    assert 0 <= reflection.get("similarity", 0.0) <= 1, \
        "Similarity should be between 0 and 1"

def test_basic_analysis(reflection_agent):
    """Test basic reflection analysis without LLM."""
    content = {
        "content": "I realized X and learned Y",
        "context": {
            "setting": "reflection"
        }
    }
    
    similar_reflections = [
        {
            "content": {"content": "Similar insight"},
            "similarity": 0.8,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    result = reflection_agent._basic_analysis(content, similar_reflections)
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "insights" in result, "Result should contain insights"
    assert "patterns" in result, "Result should contain patterns"
    
    # Verify insights
    assert len(result["insights"]) >= 1, "Should have at least one insight"
    assert all(i["type"] == "inferred_insight" for i in result["insights"]), \
        "All insights should be of type inferred_insight"
    
    # Verify patterns
    assert isinstance(result["patterns"], dict), "Patterns should be a dictionary"
    assert "similar_reflections" in result["patterns"], \
        "Patterns should contain similar_reflections from input"

def test_extract_insights(reflection_agent):
    """Test insight extraction and validation."""
    analysis = {
        "insights": [
            {
                "statement": "Valid",
                "type": "core_insight",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "impact": 0.7,
                "novelty": 0.8,
                "status": "verified"
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    insights = reflection_agent._extract_insights(analysis)
    
    # Verify we got valid insights (filtering out invalid ones)
    assert len(insights) >= 1, "Should have at least one valid insight"
    
    # Verify each insight has required fields
    for insight in insights:
        assert isinstance(insight, dict), "Each insight should be a dictionary"
        assert "type" in insight, "Each insight should have a type"
        assert isinstance(insight.get("confidence", 0.0), (int, float)), "Confidence should be numeric"
        assert 0 <= insight.get("confidence", 0.0) <= 1, "Confidence should be between 0 and 1"
    
    # Verify at least one insight has extended fields
    assert any("domain_relevance" in i or "impact" in i for i in insights), \
        "At least one insight should have domain_relevance or impact"

def test_extract_patterns(reflection_agent):
    """Test pattern extraction and validation."""
    analysis = {
        "patterns": {
            "similar_reflections": [
                {
                    "content": "reflection1",
                    "similarity": 0.8,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "recurring_themes": ["theme1", "theme2"],
            "connections": ["connection1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "learning_factors": [
                {
                    "factor": "understanding",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    patterns = reflection_agent._extract_patterns(analysis)
    
    # Verify required pattern fields are present
    assert isinstance(patterns, dict), "Patterns should be a dictionary"
    assert all(field in patterns for field in ["similar_reflections", "recurring_themes", "connections", "domain_factors", "learning_factors"]), \
        "All required pattern fields should be present"
    
    # Verify field types and non-empty content
    assert isinstance(patterns["similar_reflections"], list), "Similar reflections should be a list"
    assert isinstance(patterns["recurring_themes"], list), "Recurring themes should be a list"
    assert isinstance(patterns["connections"], list), "Connections should be a list"
    assert isinstance(patterns["domain_factors"], dict), "Domain factors should be a dictionary"
    assert isinstance(patterns["learning_factors"], list), "Learning factors should be a list"
    
    # Verify at least some content is present
    assert any([
        len(patterns["similar_reflections"]) > 0,
        len(patterns["recurring_themes"]) > 0,
        len(patterns["connections"]) > 0,
        len(patterns["domain_factors"]) > 0,
        len(patterns["learning_factors"]) > 0
    ]), "At least one pattern field should have content"
    
    # Verify invalid fields are filtered out
    assert "invalid" not in patterns, "Invalid fields should be filtered out"

def test_calculate_confidence(reflection_agent):
    """Test confidence calculation."""
    insights = [
        {
            "confidence": 0.8,
            "impact": 0.7
        },
        {
            "confidence": 0.6,
            "impact": 0.8
        }
    ]
    
    patterns = {
        "similar_reflections": [
            {
                "content": "reflection1",
                "similarity": 0.8,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ],
        "recurring_themes": ["theme1", "theme2"],
        "connections": ["connection1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "learning_factors": [
            {
                "factor": "understanding",
                "weight": 0.8
            }
        ]
    }
    
    confidence = reflection_agent._calculate_confidence(insights, patterns)
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    
    # Verify confidence calculation is reasonable
    # Given high confidence insights (0.8, 0.6) and rich patterns structure
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"

@pytest.mark.asyncio
async def test_error_handling(reflection_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    reflection_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await reflection_agent.analyze_reflection({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ReflectionResult)
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert "error" in result.metadata
    assert "error" in result.patterns

@pytest.mark.asyncio
async def test_domain_awareness(reflection_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await reflection_agent.analyze_reflection(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    reflection_agent.domain = "personal"
    result = await reflection_agent.analyze_reflection(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
