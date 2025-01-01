"""Tests for Nova's parsing functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from src.nia.nova.core.parsing import NovaParser, ParseResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "name": "TestConcept",
                "type": "test",
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
def parser(mock_llm):
    """Create a NovaParser instance with mock dependencies."""
    return NovaParser(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock()
    )

@pytest.mark.asyncio
async def test_parse_text_with_llm(parser, mock_llm):
    """Test parsing text using LLM."""
    result = await parser.parse_text("Test content")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ParseResult)
    assert len(result.concepts) == 1
    assert len(result.key_points) == 2
    assert result.confidence > 0
    assert "source_length" in result.metadata

@pytest.mark.asyncio
async def test_parse_text_without_llm():
    """Test parsing text without LLM (fallback mode)."""
    parser = NovaParser()  # No LLM provided
    text = "This is a Test sentence with Multiple Capitalized Words."
    
    result = await parser.parse_text(text)
    
    # Verify basic parsing worked
    assert isinstance(result, ParseResult)
    assert len(result.concepts) > 0
    assert all(c["type"] == "extracted_term" for c in result.concepts)
    assert result.confidence >= 0

@pytest.mark.asyncio
async def test_parse_text_error_handling(parser):
    """Test error handling during parsing."""
    # Make LLM raise an error
    parser.llm.analyze.side_effect = Exception("Test error")
    
    result = await parser.parse_text("Test content")
    
    # Verify we get a valid but empty result
    assert isinstance(result, ParseResult)
    assert len(result.concepts) == 0
    assert len(result.key_points) == 0
    assert result.confidence == 0.0
    assert "error" in result.metadata

def test_validate_concepts(parser):
    """Test concept validation."""
    test_concepts = [
        {
            "name": "Valid",
            "type": "test",
            "confidence": 0.8
        },
        {
            "name": "Invalid",  # Missing type
            "confidence": 0.5
        },
        {
            "name": "ValidWithInvalidConfidence",
            "type": "test",
            "confidence": 1.5  # Should be clamped to 1.0
        }
    ]
    
    valid_concepts = parser._validate_concepts(test_concepts)
    
    assert len(valid_concepts) == 2  # One invalid concept should be filtered out
    assert all("name" in c and "type" in c for c in valid_concepts)
    assert any(c["confidence"] == 1.0 for c in valid_concepts)  # Clamped value

def test_validate_key_points(parser):
    """Test key points validation."""
    test_points = [
        "Valid point",
        "",  # Too short
        "A" * 600,  # Too long
        123,  # Non-string (should be converted)
        "  Spaces  "  # Should be stripped
    ]
    
    valid_points = parser._validate_key_points(test_points)
    
    assert len(valid_points) == 2  # Only two should be valid
    assert all(isinstance(p, str) for p in valid_points)
    assert all(1 <= len(p) <= 500 for p in valid_points)
    assert "Spaces" in valid_points

def test_calculate_confidence(parser):
    """Test confidence calculation."""
    concepts = [
        {"confidence": 0.8},
        {"confidence": 0.6}
    ]
    key_points = ["Point 1", "Point 2"]
    
    confidence = parser._calculate_confidence(concepts, key_points)
    
    assert 0 <= confidence <= 1
    # Should be weighted average: (0.7 * 0.7 + 0.3 * 0.2) ≈ 0.55
    assert 0.54 <= confidence <= 0.56

def test_basic_parse(parser):
    """Test basic parsing without LLM."""
    text = "This is a Test sentence. Another Sentence with Keywords."
    
    result = parser._basic_parse(text)
    
    assert "concepts" in result
    assert "key_points" in result
    assert len(result["concepts"]) <= 10  # Should respect limit
    assert len(result["key_points"]) <= 5  # Should respect limit
    assert all(c["type"] == "extracted_term" for c in result["concepts"])

def test_schema_validator_initialization(parser):
    """Test schema validator initialization."""
    schema = parser.schema_validator
    
    assert "concepts" in schema
    assert "key_points" in schema
    assert "confidence" in schema
    assert "required" in schema["concepts"]
    assert "optional" in schema["concepts"]
    assert "min_length" in schema["key_points"]
    assert "max_length" in schema["key_points"]

if __name__ == "__main__":
    pytest.main([__file__])
