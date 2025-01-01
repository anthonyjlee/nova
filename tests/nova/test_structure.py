"""Tests for Nova's structure analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.structure import StructureAgent, StructureResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "response": "Structure analysis complete",
        "concepts": [
            {
                "name": "TestStructure",
                "type": "section",
                "description": "A test structure",
                "confidence": 0.8,
                "level": 1
            }
        ],
        "key_points": [
            "Valid structure detected",
            "Nested elements present"
        ]
    })
    return llm

@pytest.fixture
def structure_agent(mock_llm):
    """Create a StructureAgent instance with mock dependencies."""
    return StructureAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock(),
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_structure_with_llm(structure_agent, mock_llm):
    """Test structure analysis using LLM."""
    text = "test:\n    nested: value"
    result = await structure_agent.analyze_structure(text)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, StructureResult)
    assert result.response == "Structure analysis complete"
    assert len(result.concepts) == 1
    assert len(result.key_points) == 2
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert "has_schema" in result.metadata

@pytest.mark.asyncio
async def test_analyze_structure_without_llm():
    """Test structure analysis without LLM (fallback mode)."""
    agent = StructureAgent()  # No LLM provided
    text = "section:\n    key: value\n    another: value"
    
    result = await agent.analyze_structure(text)
    
    # Verify basic analysis worked
    assert isinstance(result, StructureResult)
    assert len(result.concepts) > 0
    assert all(c["type"] in ["section", "assignment"] for c in result.concepts)
    assert result.confidence >= 0

@pytest.mark.asyncio
async def test_analyze_with_schema(structure_agent):
    """Test structure analysis with schema validation."""
    text = "test: value"
    schema = {
        "type": "object",
        "properties": {
            "test": {"type": "string"}
        }
    }
    
    result = await structure_agent.analyze_structure(text, expected_schema=schema)
    
    # Verify schema validation was included
    assert "has_schema" in result.metadata
    assert result.metadata["has_schema"]
    assert result.validation is not None

@pytest.mark.asyncio
async def test_schema_validation(structure_agent):
    """Test schema validation functionality."""
    schema = {
        "type": "object",
        "properties": {
            "test": {
                "type": "object",
                "properties": {
                    "nested": {"type": "string"}
                }
            }
        }
    }
    
    result = await structure_agent.validate_schema(schema)
    
    assert "is_valid" in result
    assert "issues" in result
    assert "domain" in result
    assert "timestamp" in result

def test_basic_analysis(structure_agent):
    """Test basic structure analysis without LLM."""
    text = """
section1:
    key1: value1
    key2: value2
section2:
    nested:
        key3: value3
    """
    
    result = structure_agent._basic_analysis(text, None)
    
    assert "concepts" in result
    assert "key_points" in result
    assert any(c["type"] == "section" for c in result["concepts"])
    assert any("indentation levels" in kp.lower() for kp in result["key_points"])

def test_extract_concepts(structure_agent):
    """Test concept extraction and validation."""
    analysis = {
        "concepts": [
            {
                "name": "Valid",
                "type": "section",
                "confidence": 0.8,
                "level": 1
            },
            {
                "name": "NoType"  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    concepts = structure_agent._extract_concepts(analysis)
    
    assert len(concepts) == 2  # Invalid one should be filtered out
    assert all("type" in c for c in concepts)
    assert any(c["type"] == "structure" for c in concepts)  # Default type
    assert any("level" in c for c in concepts)

def test_validate_schema_structure(structure_agent):
    """Test schema structure validation."""
    schema = {
        "valid": {
            "nested": {
                "array": []
            }
        },
        123: "invalid_key",  # Non-string key
    }
    
    issues = []
    structure_agent._validate_schema_structure(schema, "", issues)
    
    assert len(issues) > 0
    assert any("Invalid key type" in issue for issue in issues)
    assert any("Empty array" in issue for issue in issues)

def test_calculate_confidence(structure_agent):
    """Test confidence calculation."""
    concepts = [
        {"confidence": 0.8},
        {"confidence": 0.6}
    ]
    
    validation = {
        "issues": ["Issue 1", "Issue 2"]
    }
    
    confidence = structure_agent._calculate_confidence(concepts, validation)
    
    assert 0 <= confidence <= 1
    # Should be weighted average with validation penalty
    # Concept confidence: 0.7
    # Validation confidence: 0.8 (1.0 - 0.2 for 2 issues)
    # Final: (0.7 * 0.7) + (0.3 * 0.8) ≈ 0.73
    assert 0.72 <= confidence <= 0.74

@pytest.mark.asyncio
async def test_error_handling(structure_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    structure_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await structure_agent.analyze_structure("Test content")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, StructureResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata
    assert result.validation.get("error") is not None

@pytest.mark.asyncio
async def test_domain_awareness(structure_agent):
    """Test domain awareness in analysis and validation."""
    # Test analysis
    result = await structure_agent.analyze_structure("Test content")
    assert result.metadata["domain"] == "professional"
    
    # Test validation
    validation = await structure_agent.validate_schema({"test": "schema"})
    assert validation["domain"] == "professional"

if __name__ == "__main__":
    pytest.main([__file__])
