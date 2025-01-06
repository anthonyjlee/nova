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
    assert isinstance(result, ResponseResult), "Result should be a ResponseResult instance"
    
    # Verify components
    assert isinstance(result.components, list), "Components should be a list"
    assert len(result.components) >= 1, "Should have at least one component"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata and result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"
    
    # Verify structure
    assert result.structure is not None, "Structure should not be None"
    assert isinstance(result.structure, dict), "Structure should be a dictionary"
    assert "similar_responses" in result.structure, "Structure should contain similar responses"
    assert "sequence" in result.structure, "Structure should contain sequence"
    assert "domain_factors" in result.structure, "Structure should contain domain factors"

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
    assert isinstance(result, ResponseResult), "Result should be a ResponseResult instance"
    
    # Verify components
    assert isinstance(result.components, list), "Components should be a list"
    assert len(result.components) > 0, "Should have at least one component"
    assert any(c["type"] == "inferred_statement" for c in result.components), \
        "Should have at least one inferred statement component"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify structure
    assert isinstance(result.structure, dict), "Structure should be a dictionary"
    assert "similar_responses" not in result.structure, \
        "Structure should not contain similar responses without vector store"
    
    # Verify basic structure elements are present
    assert "sequence" in result.structure, "Structure should contain sequence"
    assert isinstance(result.structure["sequence"], list), "Sequence should be a list"
    assert len(result.structure["sequence"]) > 0, "Should have at least one sequence step"

@pytest.mark.asyncio
async def test_get_similar_responses(response_agent, mock_vector_store):
    """Test similar response retrieval."""
    content = {"content": "test content"}
    
    responses = await response_agent._get_similar_responses(content)
    
    # Verify vector store search was called correctly
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "response"
        }
    )
    
    # Verify responses structure
    assert isinstance(responses, list), "Should return a list of responses"
    assert len(responses) >= 1, "Should have at least one similar response"
    
    # Verify response item structure
    response_item = responses[0]
    assert isinstance(response_item, dict), "Each response should be a dictionary"
    assert "content" in response_item, "Each response should have content"
    assert "similarity" in response_item, "Each response should have similarity score"
    assert isinstance(response_item["similarity"], (int, float)), \
        "Similarity should be numeric"
    assert 0 <= response_item["similarity"] <= 1, \
        "Similarity should be between 0 and 1"
    assert response_item["similarity"] >= 0.9, \
        "Similarity should be high for mock response"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "components" in result, "Result should contain components"
    assert "structure" in result, "Result should contain structure"
    
    # Verify components
    assert isinstance(result["components"], list), "Components should be a list"
    assert len(result["components"]) >= 2, "Should have at least two components"
    assert all(isinstance(c, dict) for c in result["components"]), \
        "Each component should be a dictionary"
    assert all(c["type"].startswith("inferred_") for c in result["components"]), \
        "Each component should have inferred type"
    
    # Verify component types
    component_types = [c["type"] for c in result["components"]]
    assert "inferred_statement" in component_types, \
        "Should have an inferred statement component"
    assert "inferred_question" in component_types, \
        "Should have an inferred question component"
    
    # Verify structure
    assert isinstance(result["structure"], dict), "Structure should be a dictionary"
    assert "similar_responses" in result["structure"], \
        "Structure should contain similar responses"
    assert isinstance(result["structure"]["similar_responses"], list), \
        "Similar responses should be a list"
    assert len(result["structure"]["similar_responses"]) > 0, \
        "Should have at least one similar response"

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
    
    # Verify components structure
    assert isinstance(components, list), "Should return a list of components"
    assert len(components) >= 2, "Should have at least two valid components"
    
    # Verify each component has required fields
    for component in components:
        assert isinstance(component, dict), "Each component should be a dictionary"
        assert "type" in component, "Each component should have a type"
        assert "confidence" in component, "Each component should have a confidence score"
        assert isinstance(component["confidence"], (int, float)), \
            "Confidence should be numeric"
        assert 0 <= component["confidence"] <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify at least one component has core fields
    assert any(c["type"] == "core_component" for c in components), \
        "Should have at least one core component"
    assert any("domain_relevance" in c for c in components), \
        "At least one component should have domain relevance"
    assert any("intent" in c for c in components), \
        "At least one component should have intent"
    assert any("context" in c for c in components), \
        "At least one component should have context"
    assert any("role" in c for c in components), \
        "At least one component should have role"
    
    # Verify default type assignment
    assert any(c["type"] == "component" for c in components), \
        "Should assign default type to basic component"

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
    
    # Verify basic structure
    assert isinstance(structure, dict), "Structure should be a dictionary"
    assert "invalid" not in structure, "Invalid fields should be filtered out"
    
    # Verify similar responses
    assert "similar_responses" in structure, "Structure should contain similar responses"
    assert isinstance(structure["similar_responses"], list), \
        "Similar responses should be a list"
    assert len(structure["similar_responses"]) >= 1, \
        "Should have at least one similar response"
    
    # Verify sequence
    assert "sequence" in structure, "Structure should contain sequence"
    assert isinstance(structure["sequence"], list), "Sequence should be a list"
    assert len(structure["sequence"]) >= 2, "Should have at least two sequence steps"
    
    # Verify dependencies
    assert "dependencies" in structure, "Structure should contain dependencies"
    assert isinstance(structure["dependencies"], list), "Dependencies should be a list"
    assert len(structure["dependencies"]) >= 1, "Should have at least one dependency"
    
    # Verify domain factors
    assert "domain_factors" in structure, "Structure should contain domain factors"
    assert isinstance(structure["domain_factors"], dict), \
        "Domain factors should be a dictionary"
    assert len(structure["domain_factors"]) >= 2, \
        "Should have at least two domain factors"
    
    # Verify quality factors
    assert "quality_factors" in structure, "Structure should contain quality factors"
    assert isinstance(structure["quality_factors"], list), \
        "Quality factors should be a list"
    assert len(structure["quality_factors"]) >= 1, \
        "Should have at least one quality factor"
    
    # Verify quality factor structure
    quality_factor = structure["quality_factors"][0]
    assert isinstance(quality_factor, dict), "Quality factor should be a dictionary"
    assert "factor" in quality_factor, "Quality factor should have a factor name"
    assert "weight" in quality_factor, "Quality factor should have a weight"
    assert isinstance(quality_factor["weight"], (int, float)), \
        "Quality factor weight should be numeric"
    assert 0 <= quality_factor["weight"] <= 1, \
        "Quality factor weight should be between 0 and 1"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence components and well-structured input,
    # confidence should be above threshold
    assert confidence >= 0.5, \
        f"Confidence {confidence} should be >= 0.5 given strong input values"
    
    # Test with empty inputs
    empty_confidence = response_agent._calculate_confidence([], {})
    assert isinstance(empty_confidence, (int, float)), \
        "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, \
        "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"
    
    # Test with partial inputs
    partial_confidence = response_agent._calculate_confidence(components, {})
    assert isinstance(partial_confidence, (int, float)), \
        "Partial confidence should be numeric"
    assert 0 <= partial_confidence <= 1, \
        "Partial confidence should be between 0 and 1"
    assert partial_confidence < confidence, \
        "Partial input should result in lower confidence than full input"
    
    # Test with low confidence components
    low_components = [
        {"confidence": 0.3, "intent": "inform"},
        {"confidence": 0.2, "intent": "clarify"}
    ]
    low_confidence = response_agent._calculate_confidence(low_components, structure)
    assert isinstance(low_confidence, (int, float)), \
        "Low confidence should be numeric"
    assert 0 <= low_confidence <= 1, \
        "Low confidence should be between 0 and 1"
    assert low_confidence < confidence, \
        "Low confidence components should result in lower overall confidence"

@pytest.mark.asyncio
async def test_error_handling(response_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    response_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await response_agent.analyze_response({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ResponseResult), "Result should be a ResponseResult instance"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.components) == 0, "Should have no components when error occurs"
    
    # Verify error metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    assert "Test error" in result.metadata["error"], \
        "Error message should contain original error text"
    
    # Verify error structure
    assert isinstance(result.structure, dict), "Structure should be a dictionary"
    assert "error" in result.structure, "Structure should contain error information"
    assert isinstance(result.structure["error"], str), "Error should be a string message"
    assert "Test error" in result.structure["error"], \
        "Error message should contain original error text"

@pytest.mark.asyncio
async def test_domain_awareness(response_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    
    # Test initial domain
    result = await response_agent.analyze_response(content)
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test domain change
    response_agent.domain = "personal"
    result = await response_agent.analyze_response(content)
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"
    
    # Verify domain affects analysis
    assert isinstance(result.components, list), "Result should have components list"
    assert isinstance(result.structure, dict), "Result should have structure dictionary"
    assert result.structure is not None, "Structure should not be null after domain change"

if __name__ == "__main__":
    pytest.main([__file__])
