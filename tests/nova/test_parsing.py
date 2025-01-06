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
                "statement": "Key concept",
                "type": "core_concept",
                "description": "Important idea",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "complexity": 0.7,
                "category": "principle",
                "relations": ["related1", "related2"]
            }
        ],
        "key_points": [
            {
                "statement": "Main point",
                "type": "core_point",
                "description": "Critical insight",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "importance": 0.8,
                "category": "finding",
                "dependencies": ["dep1"]
            }
        ],
        "structure": {
            "similar_parses": [
                {
                    "content": "Related parse",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "sections": ["section1", "section2"],
            "relationships": ["rel1"],
            "domain_factors": {
                "relevance": "high",
                "formality": "medium"
            },
            "complexity_factors": [
                {
                    "factor": "readability",
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
            "content": {"content": "Similar parse"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def parser(mock_llm, mock_vector_store):
    """Create a NovaParser instance with mock dependencies."""
    return NovaParser(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_parse_text_with_llm(parser, mock_llm):
    """Test text parsing using LLM."""
    text = "Text content to parse"
    
    result = await parser.parse_text(text)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ParseResult)
    assert len(result.concepts) == 1
    assert len(result.key_points) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata
    assert result.structure is not None

@pytest.mark.asyncio
async def test_parse_text_without_llm():
    """Test text parsing without LLM (fallback mode)."""
    parser = NovaParser()  # No LLM provided
    text = "This definition explains and that example shows"
    
    result = await parser.parse_text(text)
    
    # Verify basic analysis worked
    assert isinstance(result, ParseResult)
    assert len(result.concepts) > 0
    assert any(c["type"] == "inferred_definition" for c in result.concepts)
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "similar_parses" not in result.structure  # No vector store

@pytest.mark.asyncio
async def test_get_similar_parses(parser, mock_vector_store):
    """Test similar parse retrieval."""
    text = "test text"
    
    parses = await parser._get_similar_parses(text)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        text,
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "parse"
        }
    )
    assert len(parses) == 1
    assert "content" in parses[0]
    assert parses[0]["similarity"] == 0.9

def test_basic_analysis(parser):
    """Test basic text parsing without LLM."""
    text = "This definition explains X and that example shows Y"
    
    similar_parses = [
        {
            "content": {"content": "Similar parse"},
            "similarity": 0.8,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    result = parser._basic_analysis(text, similar_parses)
    
    assert "concepts" in result
    assert "key_points" in result
    assert "structure" in result
    assert len(result["concepts"]) == 2  # "definition" and "example"
    assert all(c["type"].startswith("inferred_") for c in result["concepts"])
    assert "similar_parses" in result["structure"]

def test_extract_concepts(parser):
    """Test concept extraction and validation."""
    analysis = {
        "concepts": [
            {
                "statement": "Valid",
                "type": "core_concept",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "complexity": 0.7,
                "category": "principle",
                "relations": ["rel1", "rel2"]
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    concepts = parser._extract_concepts(analysis)
    
    assert len(concepts) == 2  # Invalid one should be filtered out
    assert all("type" in c for c in concepts)
    assert any(c["type"] == "concept" for c in concepts)  # Default type
    assert any("domain_relevance" in c for c in concepts)
    assert any("complexity" in c for c in concepts)
    assert all("confidence" in c for c in concepts)
    assert all(isinstance(c["confidence"], (int, float)) for c in concepts)
    assert all(0 <= c["confidence"] <= 1 for c in concepts)

def test_extract_key_points(parser):
    """Test key point extraction and validation."""
    analysis = {
        "key_points": [
            {
                "statement": "Valid",
                "type": "core_point",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.8,
                "category": "finding",
                "dependencies": ["dep1"]
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    key_points = parser._extract_key_points(analysis)
    
    assert len(key_points) == 2  # Invalid one should be filtered out
    assert all("type" in p for p in key_points)
    assert any(p["type"] == "key_point" for p in key_points)  # Default type
    assert any("domain_relevance" in p for p in key_points)
    assert any("importance" in p for p in key_points)
    assert all("confidence" in p for p in key_points)
    assert all(isinstance(p["confidence"], (int, float)) for p in key_points)
    assert all(0 <= p["confidence"] <= 1 for p in key_points)

def test_extract_structure(parser):
    """Test structure extraction and validation."""
    analysis = {
        "structure": {
            "similar_parses": [
                {
                    "content": "parse1",
                    "similarity": 0.8,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "sections": ["section1", "section2"],
            "relationships": ["rel1"],
            "domain_factors": {
                "relevance": "high",
                "formality": "medium"
            },
            "complexity_factors": [
                {
                    "factor": "readability",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    structure = parser._extract_structure(analysis)
    
    assert "similar_parses" in structure
    assert "sections" in structure
    assert "relationships" in structure
    assert "domain_factors" in structure
    assert "complexity_factors" in structure
    assert len(structure["sections"]) == 2
    assert len(structure["complexity_factors"]) == 1
    assert "invalid" not in structure

def test_calculate_confidence(parser):
    """Test confidence calculation."""
    concepts = [
        {
            "confidence": 0.8,
            "complexity": 0.7
        },
        {
            "confidence": 0.6,
            "complexity": 0.8
        }
    ]
    
    key_points = [
        {
            "confidence": 0.7,
            "importance": 0.8
        }
    ]
    
    structure = {
        "similar_parses": [
            {
                "content": "parse1",
                "similarity": 0.8,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ],
        "sections": ["section1", "section2"],
        "relationships": ["rel1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "complexity_factors": [
            {
                "factor": "readability",
                "weight": 0.8
            }
        ]
    }
    
    confidence = parser._calculate_confidence(concepts, key_points, structure)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Base confidence (0.7 average from concepts and key points)
    # - Similar parses (0.2 from 1 parse)
    # - Sections (0.3 from 2 sections)
    # - Relationships (0.1 from 1 relationship)
    # - Domain factors (0.2 from 2 factors)
    # - Complexity factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

@pytest.mark.asyncio
async def test_error_handling(parser):
    """Test error handling during parsing."""
    # Make LLM raise an error
    parser.llm.analyze.side_effect = Exception("Test error")
    
    result = await parser.parse_text("test")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ParseResult)
    assert result.confidence == 0.0
    assert len(result.concepts) == 0
    assert len(result.key_points) == 0
    assert "error" in result.metadata
    assert "error" in result.structure

@pytest.mark.asyncio
async def test_domain_awareness(parser):
    """Test domain awareness in parsing."""
    text = "test"
    result = await parser.parse_text(text)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    parser.domain = "personal"
    result = await parser.parse_text(text)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
