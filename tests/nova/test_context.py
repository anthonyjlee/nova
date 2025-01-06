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
    assert isinstance(result, ContextResult), "Result should be a ContextResult instance"
    
    # Verify concepts
    assert isinstance(result.concepts, list), "Concepts should be a list"
    assert len(result.concepts) >= 1, "Should have at least one concept"
    
    # Verify key points
    assert isinstance(result.key_points, list), "Key points should be a list"
    assert len(result.key_points) >= 1, "Should have at least one key point"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata and environment
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata and result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"
    assert result.environment is not None and isinstance(result.environment, dict), \
        "Environment should be a non-null dictionary"

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
    assert isinstance(result, ContextResult), "Result should be a ContextResult instance"
    
    # Verify concepts
    assert isinstance(result.concepts, list), "Concepts should be a list"
    assert len(result.concepts) >= 1, "Should have at least one concept"
    
    # Verify concept types
    concept_types = [c["type"] for c in result.concepts]
    assert any(t == "context_factor" for t in concept_types), \
        "Should identify basic context factors"
    assert any(t == "nested_context" for t in concept_types), \
        "Should identify nested context structures"
    assert any(t == "multi_value" for t in concept_types), \
        "Should identify multi-value elements"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "concepts" in result, "Result should contain concepts"
    assert "key_points" in result, "Result should contain key points"
    assert "environment" in result, "Result should contain environment"
    
    # Verify concepts and key points
    assert isinstance(result["concepts"], list), "Concepts should be a list"
    assert isinstance(result["key_points"], list), "Key points should be a list"
    assert len(result["key_points"]) >= 1, "Should have at least one key point"
    
    # Verify key point content
    assert any("nested context" in kp.lower() for kp in result["key_points"]), \
        "Should identify nested context in key points"
    
    # Verify environment
    assert isinstance(result["environment"], dict), "Environment should be a dictionary"

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
    
    # Verify we got valid concepts (filtering out invalid ones)
    assert len(concepts) >= 1, "Should have at least one valid concept"
    
    # Verify each concept has required fields
    for concept in concepts:
        assert isinstance(concept, dict), "Each concept should be a dictionary"
        assert "type" in concept, "Each concept should have a type"
        assert isinstance(concept.get("confidence", 0.0), (int, float)), \
            "Confidence should be numeric"
        assert 0 <= concept.get("confidence", 0.0) <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify concept types
    assert any(c["type"] == "context" for c in concepts), \
        "Should have at least one default 'context' type"
    
    # Verify at least one concept has extended fields
    assert any("domain_relevance" in c for c in concepts), \
        "At least one concept should have domain_relevance"

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
    
    # Verify basic structure
    assert isinstance(environment, dict), "Environment should be a dictionary"
    
    # Verify required fields are present
    required_fields = ["string", "number", "boolean", "nested"]
    for field in required_fields:
        assert field in environment, f"Environment should contain {field}"
    
    # Verify field types
    assert isinstance(environment["string"], str), "String field should be a string"
    assert isinstance(environment["number"], (int, float)), "Number field should be numeric"
    assert isinstance(environment["boolean"], bool), "Boolean field should be a boolean"
    assert isinstance(environment["nested"], dict), "Nested field should be a dictionary"
    
    # Verify nested structure
    assert "key" in environment["nested"], "Nested dict should contain 'key'"
    assert "list" in environment["nested"], "Nested dict should contain 'list'"
    assert isinstance(environment["nested"]["list"], list), "Nested list should be a list"
    
    # Verify invalid fields are filtered out
    assert "invalid" not in environment, "Invalid fields should be filtered out"

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
    
    # Verify basic structure
    assert isinstance(cleaned, dict), "Cleaned result should be a dictionary"
    
    # Verify field types
    assert isinstance(cleaned["str"], str), "String field should be a string"
    assert isinstance(cleaned["num"], (int, float)), "Number field should be numeric"
    assert isinstance(cleaned["bool"], bool), "Boolean field should be a boolean"
    assert isinstance(cleaned["list"], list), "List field should be a list"
    assert isinstance(cleaned["nested"], dict), "Nested field should be a dictionary"
    
    # Verify list cleaning
    assert None not in cleaned["list"], "List should not contain None values"
    assert all(isinstance(item, str) for item in cleaned["list"]), \
        "All list items should be strings"
    
    # Verify nested cleaning
    assert "key" in cleaned["nested"], "Nested dict should contain 'key'"
    assert isinstance(cleaned["nested"]["key"], str), "Nested key value should be a string"
    assert "invalid" not in cleaned["nested"], "Invalid fields should be filtered out"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence concepts (0.8, 0.6) and a structured environment,
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"
    
    # Test with empty inputs
    empty_confidence = context_agent._calculate_confidence([], {})
    assert isinstance(empty_confidence, (int, float)), "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"

@pytest.mark.asyncio
async def test_error_handling(context_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    context_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await context_agent.analyze_context({"test": "value"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ContextResult), "Result should be a ContextResult instance"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    
    # Verify error state
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    
    assert isinstance(result.environment, dict), "Environment should be a dictionary"
    assert "error" in result.environment, "Environment should contain error information"
    assert isinstance(result.environment["error"], str), "Environment error should be a string"

@pytest.mark.asyncio
async def test_domain_awareness(context_agent):
    """Test domain awareness in analysis."""
    context = {"test": "value"}
    result = await context_agent.analyze_context(context)
    
    # Verify domain is included and correct
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test with different domain
    context_agent.domain = "personal"
    result = await context_agent.analyze_context(context)
    
    # Verify domain was updated
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"

if __name__ == "__main__":
    pytest.main([__file__])
