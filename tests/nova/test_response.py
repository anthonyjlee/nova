"""Tests for Nova's response processing functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.response import ResponseAgent, ResponseResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "components": [
            {
                "statement": "Key component",
                "type": "core_component",
                "description": "Important part",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "intent": "inform",
                "context": "explanation",
                "role": "clarification"
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
            "sequence": ["step1", "step2"],
            "dependencies": ["dep1"],
            "domain_factors": {
                "relevance": "high",
                "formality": "medium"
            },
            "quality_factors": [
                {
                    "factor": "clarity",
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
            "content": {"content": "Similar response"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def response_agent(mock_llm, mock_vector_store):
    """Create a ResponseAgent instance with mock dependencies."""
    return ResponseAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_response_with_llm(response_agent, mock_llm):
    """Test response analysis using LLM."""
    content = {
        "content": "Response content to analyze",
        "type": "response"
    }
    
    result = await response_agent.analyze_response(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ResponseResult)
    assert len(result.components) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.structure is not None

@pytest.mark.asyncio
async def test_analyze_response_without_llm():
    """Test response analysis without LLM (fallback mode)."""
    agent = ResponseAgent()  # No LLM provided
    content = {
        "content": "This statement explains and that question asks",
        "context": {"setting": "response"}
    }
    
    result = await agent.analyze_response(content)
    
    # Verify basic analysis worked
    assert isinstance(result, ResponseResult)
    assert len(result.components) > 0
    assert any(c["type"] == "inferred_statement" for c in result.components)
    assert result.confidence >= 0
    assert "similar_responses" not in result.structure  # No vector store

@pytest.mark.asyncio
async def test_get_similar_responses(response_agent, mock_vector_store):
    """Test similar response retrieval."""
    content = {"content": "test content"}
    
    responses = await response_agent._get_similar_responses(content)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "response"
        }
    )
    assert len(responses) == 1
    assert "content" in responses[0]
    assert responses[0]["similarity"] == 0.9

def test_basic_analysis(response_agent):
    """Test basic response analysis without LLM."""
    content = {
        "content": "This statement explains X and that question asks Y",
        "context": {
            "setting": "response"
        }
    }
    
    similar_responses = [
        {
            "content": {"content": "Similar component"},
            "similarity": 0.8,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    result = response_agent._basic_analysis(content, similar_responses)
    
    assert "components" in result
    assert "structure" in result
    assert len(result["components"]) == 2  # "statement" and "question"
    assert all(c["type"].startswith("inferred_") for c in result["components"])
    assert "similar_responses" in result["structure"]

def test_extract_components(response_agent):
    """Test component extraction and validation."""
    analysis = {
        "components": [
            {
                "statement": "Valid",
                "type": "core_component",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "intent": "inform",
                "context": "explanation",
                "role": "clarification"
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    components = response_agent._extract_components(analysis)
    
    assert len(components) == 2  # Invalid one should be filtered out
    assert all("type" in c for c in components)
    assert any(c["type"] == "component" for c in components)  # Default type
    assert any("domain_relevance" in c for c in components)
    assert any("intent" in c for c in components)

def test_extract_structure(response_agent):
    """Test structure extraction and validation."""
    analysis = {
        "structure": {
            "similar_responses": [
                {
                    "content": "response1",
                    "similarity": 0.8,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "sequence": ["step1", "step2"],
            "dependencies": ["dep1"],
            "domain_factors": {
                "relevance": "high",
                "formality": "medium"
            },
            "quality_factors": [
                {
                    "factor": "clarity",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    structure = response_agent._extract_structure(analysis)
    
    assert "similar_responses" in structure
    assert "sequence" in structure
    assert "dependencies" in structure
    assert "domain_factors" in structure
    assert "quality_factors" in structure
    assert len(structure["sequence"]) == 2
    assert len(structure["quality_factors"]) == 1
    assert "invalid" not in structure

def test_calculate_confidence(response_agent):
    """Test confidence calculation."""
    components = [
        {
            "confidence": 0.8,
            "intent": "inform"
        },
        {
            "confidence": 0.6,
            "intent": "clarify"
        }
    ]
    
    structure = {
        "similar_responses": [
            {
                "content": "response1",
                "similarity": 0.8,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ],
        "sequence": ["step1", "step2"],
        "dependencies": ["dep1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "quality_factors": [
            {
                "factor": "clarity",
                "weight": 0.8
            }
        ]
    }
    
    confidence = response_agent._calculate_confidence(components, structure)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Component confidence (0.7 average)
    # - Similar responses (0.2 from 1 response)
    # - Sequence (0.3 from 2 steps)
    # - Dependencies (0.1 from 1 dependency)
    # - Domain factors (0.2 from 2 factors)
    # - Quality factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

@pytest.mark.asyncio
async def test_error_handling(response_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    response_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await response_agent.analyze_response({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ResponseResult)
    assert result.confidence == 0.0
    assert len(result.components) == 0
    assert "error" in result.metadata
    assert "error" in result.structure

@pytest.mark.asyncio
async def test_domain_awareness(response_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await response_agent.analyze_response(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    response_agent.domain = "personal"
    result = await response_agent.analyze_response(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
