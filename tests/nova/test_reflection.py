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
    assert len(result.insights) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.patterns is not None

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
    assert isinstance(result, ReflectionResult)
    assert len(result.insights) > 0
    assert any(i["type"] == "inferred_insight" for i in result.insights)
    assert result.confidence >= 0
    assert "similar_reflections" not in result.patterns  # No vector store

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
    assert len(reflections) == 1
    assert "content" in reflections[0]
    assert reflections[0]["similarity"] == 0.9

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
    
    assert "insights" in result
    assert "patterns" in result
    assert len(result["insights"]) == 2  # "realized" and "learned"
    assert all(i["type"] == "inferred_insight" for i in result["insights"])
    assert "similar_reflections" in result["patterns"]

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
    
    assert len(insights) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in insights)
    assert any(i["type"] == "insight" for i in insights)  # Default type
    assert any("domain_relevance" in i for i in insights)
    assert any("impact" in i for i in insights)

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
    
    assert "similar_reflections" in patterns
    assert "recurring_themes" in patterns
    assert "connections" in patterns
    assert "domain_factors" in patterns
    assert "learning_factors" in patterns
    assert len(patterns["recurring_themes"]) == 2
    assert len(patterns["learning_factors"]) == 1
    assert "invalid" not in patterns

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
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Insight confidence (0.7 average)
    # - Similar reflections (0.2 from 1 reflection)
    # - Recurring themes (0.3 from 2 themes)
    # - Connections (0.1 from 1 connection)
    # - Domain factors (0.2 from 2 factors)
    # - Learning factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

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
