"""Tests for Nova's context analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.context import ContextAgent, ContextResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "name": "TestContext",
                "type": "environment",
                "description": "A test environment",
                "confidence": 0.8,
                "domain_relevance": 0.9
            }
        ],
        "key_points": [
            "Environment detected",
            "Context analyzed"
        ],
        "environment": {
            "type": "test",
            "settings": {
                "mode": "development",
                "features": ["test1", "test2"]
            }
        }
    })
    return llm

@pytest.fixture
def context_agent(mock_llm):
    """Create a ContextAgent instance with mock dependencies."""
    return ContextAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock(),
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_context_with_llm(context_agent, mock_llm):
    """Test context analysis using LLM."""
    context = {
        "type": "test",
        "environment": {"mode": "test"}
    }
    
    result = await context_agent.analyze_context(context)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ContextResult)
    assert len(result.concepts) == 1
    assert len(result.key_points) == 2
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.environment is not None

@pytest.mark.asyncio
async def test_analyze_context_without_llm():
    """Test context analysis without LLM (fallback mode)."""
    agent = ContextAgent()  # No LLM provided
    context = {
        "string_value": "test",
        "number_value": 123,
        "nested": {"key": "value"},
        "list_value": ["item1", "item2"]
    }
    
    result = await agent.analyze_context(context)
    
    # Verify basic analysis worked
    assert isinstance(result, ContextResult)
    assert len(result.concepts) > 0
    assert any(c["type"] == "context_factor" for c in result.concepts)
    assert any(c["type"] == "nested_context" for c in result.concepts)
    assert any(c["type"] == "multi_value" for c in result.concepts)
    assert result.confidence >= 0

def test_basic_analysis(context_agent):
    """Test basic context analysis without LLM."""
    context = {
        "environment": {
            "mode": "test",
            "settings": {
                "feature1": True,
                "feature2": False
            }
        },
        "metadata": ["tag1", "tag2"]
    }
    
    result = context_agent._basic_analysis(context)
    
    assert "concepts" in result
    assert "key_points" in result
    assert "environment" in result
    assert any("nested context" in kp.lower() for kp in result["key_points"])

def test_extract_concepts(context_agent):
    """Test concept extraction and validation."""
    analysis = {
        "concepts": [
            {
                "name": "Valid",
                "type": "environment",
                "confidence": 0.8,
                "domain_relevance": 0.9
            },
            {
                "name": "NoType"  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    concepts = context_agent._extract_concepts(analysis)
    
    assert len(concepts) == 2  # Invalid one should be filtered out
    assert all("type" in c for c in concepts)
    assert any(c["type"] == "context" for c in concepts)  # Default type
    assert any("domain_relevance" in c for c in concepts)

def test_extract_environment(context_agent):
    """Test environment extraction and validation."""
    analysis = {
        "environment": {
            "string": "value",
            "number": 123,
            "boolean": True,
            "nested": {
                "key": "value",
                "list": ["item1", "item2"]
            },
            "invalid": object()  # Should be ignored
        }
    }
    
    environment = context_agent._extract_environment(analysis)
    
    assert "string" in environment
    assert "number" in environment
    assert "boolean" in environment
    assert "nested" in environment
    assert isinstance(environment["nested"], dict)
    assert "invalid" not in environment

def test_clean_env_dict(context_agent):
    """Test environment dictionary cleaning."""
    env_dict = {
        "str": "value",
        "num": 123,
        "bool": True,
        "list": ["item1", None, "item2"],
        "nested": {
            "key": "value",
            "invalid": object()
        }
    }
    
    cleaned = context_agent._clean_env_dict(env_dict)
    
    assert isinstance(cleaned["str"], str)
    assert isinstance(cleaned["num"], (int, float))
    assert isinstance(cleaned["bool"], bool)
    assert isinstance(cleaned["list"], list)
    assert None not in cleaned["list"]
    assert isinstance(cleaned["nested"], dict)
    assert "invalid" not in cleaned["nested"]

def test_calculate_confidence(context_agent):
    """Test confidence calculation."""
    concepts = [
        {"confidence": 0.8},
        {"confidence": 0.6}
    ]
    
    environment = {
        "key1": "value1",
        "key2": {
            "nested": "value2"
        }
    }
    
    confidence = context_agent._calculate_confidence(concepts, environment)
    
    assert 0 <= confidence <= 1
    # Should be weighted average with environment size factor
    # Concept confidence: 0.7
    # Environment confidence: based on size
    assert confidence > 0.5

@pytest.mark.asyncio
async def test_error_handling(context_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    context_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await context_agent.analyze_context({"test": "value"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ContextResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata
    assert "error" in result.environment

@pytest.mark.asyncio
async def test_domain_awareness(context_agent):
    """Test domain awareness in analysis."""
    context = {"test": "value"}
    result = await context_agent.analyze_context(context)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    context_agent.domain = "personal"
    result = await context_agent.analyze_context(context)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
