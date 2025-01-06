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
    assert isinstance(result, StructureResult), "Result should be a StructureResult instance"
    
    # Verify response
    assert isinstance(result.response, str), "Response should be a string"
    assert result.response == "Structure analysis complete", \
        "Response should match expected analysis completion message"
    
    # Verify concepts
    assert isinstance(result.concepts, list), "Concepts should be a list"
    assert len(result.concepts) >= 1, "Should have at least one concept"
    
    # Verify concept structure
    concept = result.concepts[0]
    assert isinstance(concept, dict), "Each concept should be a dictionary"
    assert "name" in concept, "Each concept should have a name"
    assert "type" in concept, "Each concept should have a type"
    assert "description" in concept, "Each concept should have a description"
    assert "confidence" in concept, "Each concept should have a confidence score"
    assert isinstance(concept["confidence"], (int, float)), \
        "Confidence should be numeric"
    assert 0 <= concept["confidence"] <= 1, \
        "Confidence should be between 0 and 1"
    
    # Verify key points
    assert isinstance(result.key_points, list), "Key points should be a list"
    assert len(result.key_points) >= 2, "Should have at least two key points"
    assert all(isinstance(kp, str) for kp in result.key_points), \
        "Each key point should be a string"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"
    assert "has_schema" in result.metadata, "Metadata should indicate schema presence"

@pytest.mark.asyncio
async def test_analyze_structure_without_llm():
    """Test structure analysis without LLM (fallback mode)."""
    agent = StructureAgent()  # No LLM provided
    text = "section:\n    key: value\n    another: value"
    
    result = await agent.analyze_structure(text)
    
    # Verify basic analysis worked
    assert isinstance(result, StructureResult), "Result should be a StructureResult instance"
    
    # Verify concepts
    assert isinstance(result.concepts, list), "Concepts should be a list"
    assert len(result.concepts) > 0, "Should have at least one concept"
    
    # Verify concept types
    assert all(isinstance(c, dict) for c in result.concepts), \
        "Each concept should be a dictionary"
    assert all("type" in c for c in result.concepts), \
        "Each concept should have a type"
    assert all(c["type"] in ["section", "assignment"] for c in result.concepts), \
        "Each concept should have a valid type (section or assignment)"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify basic structure
    assert isinstance(result.response, str), "Response should be a string"
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert result.validation is None, "Validation should be None without schema"

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
    
    # Verify result structure
    assert isinstance(result, StructureResult), "Result should be a StructureResult instance"
    
    # Verify metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "has_schema" in result.metadata, "Metadata should indicate schema presence"
    assert result.metadata["has_schema"] is True, \
        "Schema presence flag should be True"
    
    # Verify validation
    assert result.validation is not None, "Validation should be present"
    assert isinstance(result.validation, dict), "Validation should be a dictionary"
    assert "is_valid" in result.validation, "Validation should include validity status"
    assert isinstance(result.validation["is_valid"], bool), \
        "Validation status should be boolean"
    
    # Verify schema-specific metadata
    assert "schema_version" in result.metadata, "Metadata should include schema version"
    assert isinstance(result.metadata["schema_version"], str), \
        "Schema version should be a string"
    
    # Verify confidence reflects schema validation
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    assert result.confidence > 0, "Confidence should be positive with valid schema"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    
    # Verify validation status
    assert "is_valid" in result, "Result should include validation status"
    assert isinstance(result["is_valid"], bool), "Validation status should be boolean"
    
    # Verify issues
    assert "issues" in result, "Result should include issues"
    assert isinstance(result["issues"], list), "Issues should be a list"
    assert all(isinstance(issue, str) for issue in result["issues"]), \
        "Each issue should be a string"
    
    # Verify metadata
    assert "domain" in result, "Result should include domain"
    assert result["domain"] == "professional", \
        "Domain should be set to 'professional'"
    assert "timestamp" in result, "Result should include timestamp"
    assert isinstance(result["timestamp"], str), "Timestamp should be a string"
    
    # Verify schema-specific fields
    assert "schema_type" in result, "Result should include schema type"
    assert result["schema_type"] == "object", "Schema type should be 'object'"
    assert "property_count" in result, "Result should include property count"
    assert isinstance(result["property_count"], int), "Property count should be integer"
    assert result["property_count"] > 0, "Should have at least one property"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "concepts" in result, "Result should contain concepts"
    assert "key_points" in result, "Result should contain key points"
    
    # Verify concepts
    assert isinstance(result["concepts"], list), "Concepts should be a list"
    assert len(result["concepts"]) > 0, "Should have at least one concept"
    
    # Verify concept structure
    for concept in result["concepts"]:
        assert isinstance(concept, dict), "Each concept should be a dictionary"
        assert "type" in concept, "Each concept should have a type"
        assert "level" in concept, "Each concept should have a level"
        assert isinstance(concept["level"], int), "Level should be an integer"
        assert concept["level"] >= 0, "Level should be non-negative"
    
    # Verify section concepts
    assert any(c["type"] == "section" for c in result["concepts"]), \
        "Should have at least one section concept"
    
    # Verify key points
    assert isinstance(result["key_points"], list), "Key points should be a list"
    assert len(result["key_points"]) > 0, "Should have at least one key point"
    assert all(isinstance(kp, str) for kp in result["key_points"]), \
        "Each key point should be a string"
    assert any("indentation levels" in kp.lower() for kp in result["key_points"]), \
        "Should mention indentation levels in key points"
    
    # Verify nested structure detection
    nested_concepts = [c for c in result["concepts"] if c["level"] > 0]
    assert len(nested_concepts) > 0, "Should detect nested structure"

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
    
    # Verify basic structure
    assert isinstance(concepts, list), "Should return a list of concepts"
    assert len(concepts) == 2, "Should have exactly two valid concepts (invalid one filtered)"
    
    # Verify each concept
    for concept in concepts:
        assert isinstance(concept, dict), "Each concept should be a dictionary"
        assert "type" in concept, "Each concept should have a type"
        assert "confidence" in concept, "Each concept should have a confidence score"
        assert isinstance(concept["confidence"], (int, float)), \
            "Confidence should be numeric"
        assert 0 <= concept["confidence"] <= 1, \
            "Confidence should be between 0 and 1"
        assert "name" in concept, "Each concept should have a name"
    
    # Verify type assignment
    assert any(c["type"] == "section" for c in concepts), \
        "Should preserve explicit section type"
    assert any(c["type"] == "structure" for c in concepts), \
        "Should assign default structure type"
    
    # Verify level handling
    assert any("level" in c for c in concepts), \
        "Should preserve level when provided"
    assert all(c.get("level", 0) >= 0 for c in concepts), \
        "Level should be non-negative"
    
    # Verify no invalid concepts included
    assert all(isinstance(c, dict) for c in concepts), \
        "Should filter out non-dictionary concepts"

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
    
    # Verify issues list
    assert isinstance(issues, list), "Issues should be a list"
    assert len(issues) > 0, "Should detect schema issues"
    assert all(isinstance(issue, str) for issue in issues), \
        "Each issue should be a string"
    
    # Verify specific issues
    assert any("Invalid key type" in issue for issue in issues), \
        "Should detect non-string key issue"
    assert any("Empty array" in issue for issue in issues), \
        "Should detect empty array issue"
    
    # Verify issue format
    for issue in issues:
        assert len(issue) > 0, "Issue message should not be empty"
        assert issue[0].isupper(), "Issue message should start with capital letter"
        assert issue.strip() == issue, "Issue message should not have leading/trailing spaces"
    
    # Verify no duplicate issues
    assert len(issues) == len(set(issues)), "Should not have duplicate issues"
    
    # Verify path handling
    path_issues = [issue for issue in issues if "at path" in issue.lower()]
    assert len(path_issues) > 0, "Should include path information in issues"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence components and some validation issues,
    # confidence should be above threshold but not maximum
    assert confidence >= 0.5, \
        f"Confidence {confidence} should be >= 0.5 given strong input values"
    assert confidence < 1.0, \
        f"Confidence {confidence} should be < 1.0 with validation issues"
    
    # Test with empty inputs
    empty_confidence = structure_agent._calculate_confidence([], {})
    assert isinstance(empty_confidence, (int, float)), \
        "Empty confidence should be numeric"
    assert 0 <= empty_confidence <= 1, \
        "Empty confidence should be between 0 and 1"
    assert empty_confidence < confidence, \
        "Empty input should result in lower confidence than valid input"
    
    # Test with low confidence concepts
    low_concepts = [
        {"confidence": 0.3},
        {"confidence": 0.2}
    ]
    low_confidence = structure_agent._calculate_confidence(low_concepts, validation)
    assert isinstance(low_confidence, (int, float)), \
        "Low confidence should be numeric"
    assert 0 <= low_confidence <= 1, \
        "Low confidence should be between 0 and 1"
    assert low_confidence < confidence, \
        "Low confidence components should result in lower overall confidence"
    
    # Test with more validation issues
    many_issues = {"issues": ["Issue 1", "Issue 2", "Issue 3", "Issue 4"]}
    issue_confidence = structure_agent._calculate_confidence(concepts, many_issues)
    assert isinstance(issue_confidence, (int, float)), \
        "Issue confidence should be numeric"
    assert 0 <= issue_confidence <= 1, \
        "Issue confidence should be between 0 and 1"
    assert issue_confidence < confidence, \
        "More validation issues should result in lower confidence"

@pytest.mark.asyncio
async def test_error_handling(structure_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    structure_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await structure_agent.analyze_structure("Test content")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, StructureResult), "Result should be a StructureResult instance"
    
    # Verify error state
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.concepts) == 0, "Should have no concepts when error occurs"
    
    # Verify error metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    assert "Test error" in result.metadata["error"], \
        "Error message should contain original error text"
    
    # Verify error validation
    assert isinstance(result.validation, dict), "Validation should be a dictionary"
    assert "error" in result.validation, "Validation should contain error information"
    assert isinstance(result.validation["error"], str), "Error should be a string message"
    assert "Test error" in result.validation["error"], \
        "Error message should contain original error text"

@pytest.mark.asyncio
async def test_domain_awareness(structure_agent):
    """Test domain awareness in analysis and validation."""
    # Test analysis with initial domain
    result = await structure_agent.analyze_structure("Test content")
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test validation with initial domain
    validation = await structure_agent.validate_schema({"test": "schema"})
    assert isinstance(validation, dict), "Validation should be a dictionary"
    assert "domain" in validation, "Validation should include domain"
    assert validation["domain"] == "professional", \
        "Validation domain should match agent domain"
    
    # Test domain change
    structure_agent.domain = "personal"
    
    # Verify analysis reflects domain change
    result = await structure_agent.analyze_structure("Test content")
    assert result.metadata["domain"] == "personal", \
        "Analysis domain should update after change"
    
    # Verify validation reflects domain change
    validation = await structure_agent.validate_schema({"test": "schema"})
    assert validation["domain"] == "personal", \
        "Validation domain should update after change"

if __name__ == "__main__":
    pytest.main([__file__])
