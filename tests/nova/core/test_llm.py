"""Tests for LM Studio integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from nia.nova.core.llm import LMStudioLLM
from nia.nova.core.models import (
    LLMConcept,
    LLMAnalysisResult,
    LLMAnalyticsResult,
    LLMErrorResponse
)

@pytest.fixture
def llm():
    """Create LLM instance for testing."""
    return LMStudioLLM(
        chat_model="test_model",
        embedding_model="test_embeddings",
        api_base="http://localhost:1234/v1"
    )

@pytest.mark.asyncio
async def test_structured_completion():
    """Test getting structured completion."""
    with patch("openai.OpenAI") as mock_openai, \
         patch("outlines.generate.json") as mock_generator:
        
        # Setup mock response
        mock_response = LLMAnalyticsResult(
            response="Test analysis",
            confidence=0.8
        )
        mock_generator.return_value = MagicMock(return_value=mock_response)
        
        # Create LLM instance
        llm = LMStudioLLM("test_model", "test_embeddings")
        
        # Test completion
        result = await llm.get_structured_completion(
            prompt="Test prompt",
            response_model=Dict[str, Any],
            agent_type="test",
            metadata={"test": "metadata"}
        )
        
        # Verify response
        assert result["response"] == "Test analysis"
        assert result["confidence"] == 0.8
        assert result["metadata"] == {"test": "metadata"}
        
        # Verify OpenAI client creation
        mock_openai.assert_called_once_with(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio"
        )

@pytest.mark.asyncio
async def test_analytics_processing():
    """Test analytics processing template."""
    with patch("openai.OpenAI") as mock_openai, \
         patch("outlines.generate.json") as mock_generator:
        
        # Setup mock response
        mock_response = LLMAnalyticsResult(
            response="Analytics insights",
            confidence=0.9
        )
        mock_generator.return_value = MagicMock(return_value=mock_response)
        
        # Create LLM instance
        llm = LMStudioLLM("test_model", "test_embeddings")
        
        # Test analytics
        result = await llm.analyze(
            content={
                "text": "Test content",
                "metadata": {
                    "domain": "test_domain"
                }
            },
            template="analytics_processing"
        )
        
        # Verify response
        assert result["response"] == "Analytics insights"
        assert result["confidence"] == 0.9
        assert result["metadata"]["domain"] == "test_domain"

@pytest.mark.asyncio
async def test_parsing_analysis():
    """Test parsing analysis template."""
    with patch("openai.OpenAI") as mock_openai, \
         patch("outlines.generate.json") as mock_generator:
        
        # Setup mock response
        mock_response = LLMAnalysisResult(
            response="Parsing analysis",
            concepts=[
                LLMConcept(
                    name="test_concept",
                    type="test_type",
                    description="test description",
                    related=["related1", "related2"]
                )
            ],
            key_points=["point1", "point2"],
            implications=["implication1"],
            uncertainties=["uncertainty1"],
            reasoning=["reason1", "reason2"]
        )
        mock_generator.return_value = MagicMock(return_value=mock_response)
        
        # Create LLM instance
        llm = LMStudioLLM("test_model", "test_embeddings")
        
        # Test parsing
        result = await llm.analyze(
            content={
                "text": "Test content",
                "metadata": {
                    "domain": "test_domain"
                }
            },
            template="parsing_analysis"
        )
        
        # Verify response
        assert result["response"] == "Parsing analysis"
        assert len(result["concepts"]) == 1
        assert result["concepts"][0]["name"] == "test_concept"
        assert len(result["key_points"]) == 2
        assert len(result["implications"]) == 1
        assert len(result["uncertainties"]) == 1
        assert len(result["reasoning"]) == 2
        assert result["metadata"]["domain"] == "test_domain"

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in analysis."""
    with patch("openai.OpenAI") as mock_openai, \
         patch("outlines.generate.json") as mock_generator:
        
        # Setup mock to raise error
        mock_generator.side_effect = Exception("Test error")
        
        # Create LLM instance
        llm = LMStudioLLM("test_model", "test_embeddings")
        
        # Test error handling
        result = await llm.analyze(
            content={
                "text": "Test content",
                "metadata": {
                    "domain": "test_domain"
                }
            },
            template="parsing_analysis"
        )
        
        # Verify error response structure
        assert "Error analyzing content" in result["response"]
        assert len(result["concepts"]) == 1
        assert result["concepts"][0]["type"] == "error"
        assert "Test error" in result["concepts"][0]["description"]
        assert result["concepts"][0]["confidence"] == 0.0
        assert "Error occurred during analysis" in result["key_points"]

@pytest.mark.asyncio
async def test_invalid_template():
    """Test handling of invalid template."""
    # Create LLM instance
    llm = LMStudioLLM("test_model", "test_embeddings")
    
    # Test invalid template
    with pytest.raises(ValueError) as exc_info:
        await llm.analyze(
            content={"text": "test"},
            template="invalid_template"
        )
    
    assert "Unknown template: invalid_template" in str(exc_info.value)
