"""Tests for Nova's validation functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.validation import ValidationAgent, ValidationResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "validations": [
            {
                "rule": "test_rule",
                "passed": True,
                "confidence": 0.8,
                "description": "Test validation",
                "details": "Validation details",
                "domain_relevance": 0.9,
                "severity": "low",
                "similar_count": 3
            }
        ],
        "issues": [
            {
                "type": "test_issue",
                "severity": "medium",
                "description": "Test issue",
                "details": "Issue details",
                "domain_impact": 0.3,
                "suggested_fix": "Fix suggestion",
                "related_rules": ["rule1", "rule2"]
            }
        ]
    })
    return llm

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar validation"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def validation_agent(mock_llm, mock_vector_store):
    """Create a ValidationAgent instance with mock dependencies."""
    return ValidationAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_validate_content_with_llm(validation_agent, mock_llm):
    """Test content validation using LLM."""
    content = {
        "content": "Test content",
        "type": "test",
        "metadata": {"key": "value"}
    }
    
    result = await validation_agent.validate_content(content, "structure")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ValidationResult)
    assert len(result.validations) == 1
    assert len(result.issues) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata
    assert result.is_valid is not None

@pytest.mark.asyncio
async def test_validate_content_without_llm():
    """Test content validation without LLM (fallback mode)."""
    agent = ValidationAgent()  # No LLM provided
    content = {
        "content": "test",
        "type": "test",
        "metadata": {}
    }
    
    result = await agent.validate_content(content, "structure")
    
    # Verify basic validation worked
    assert isinstance(result, ValidationResult)
    assert len(result.validations) > 0
    assert all(v["rule"] in ["has_content", "has_type", "has_metadata"] for v in result.validations)
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_validations(validation_agent, mock_vector_store):
    """Test similar validation retrieval."""
    content = {"content": "test content"}
    validation_type = "structure"
    
    validations = await validation_agent._get_similar_validations(content, validation_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "validation",
            "validation_type": "structure"
        }
    )
    assert len(validations) == 1
    assert "content" in validations[0]
    assert validations[0]["similarity"] == 0.9

def test_basic_validation_structure(validation_agent):
    """Test basic structure validation."""
    content = {
        "content": "test",
        "type": "test",
        "metadata": {}
    }
    
    result = validation_agent._basic_validation(content, "structure", [])
    
    assert "validations" in result
    assert "issues" in result
    assert len(result["validations"]) == 3  # has_content, has_type, has_metadata
    assert all(v["passed"] for v in result["validations"])
    assert len(result["issues"]) == 0

def test_basic_validation_format(validation_agent):
    """Test basic format validation."""
    content = {"test": "value"}
    similar_validations = [
        {
            "content": {"content": "Similar"},
            "similarity": 0.8
        }
    ]
    
    result = validation_agent._basic_validation(content, "format", similar_validations)
    
    assert "validations" in result
    assert "issues" in result
    assert len(result["validations"]) == 2  # is_dict, similar_formats
    assert all(v["passed"] for v in result["validations"])
    assert len(result["issues"]) == 0

def test_basic_validation_domain(validation_agent):
    """Test basic domain validation."""
    content = {
        "domain": "professional",
        "content": "test"
    }
    
    result = validation_agent._basic_validation(content, "domain", [])
    
    assert "validations" in result
    assert "issues" in result
    assert len(result["validations"]) == 2  # has_domain, domain_match
    assert all(v["passed"] for v in result["validations"])
    assert len(result["issues"]) == 0

def test_extract_validations(validation_agent):
    """Test validation extraction and validation."""
    analysis = {
        "validations": [
            {
                "rule": "test_rule",
                "passed": True,
                "confidence": 0.8,
                "description": "Test",
                "domain_relevance": 0.9,
                "severity": "low"
            },
            {
                "rule": "basic_rule",
                "passed": True,
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    validations = validation_agent._extract_validations(analysis)
    
    assert len(validations) == 2  # Invalid one should be filtered out
    assert all("rule" in v for v in validations)
    assert all("passed" in v for v in validations)
    assert all("confidence" in v for v in validations)
    assert all(isinstance(v["confidence"], (int, float)) for v in validations)
    assert all(0 <= v["confidence"] <= 1 for v in validations)
    assert any("domain_relevance" in v for v in validations)

def test_extract_issues(validation_agent):
    """Test issue extraction and validation."""
    analysis = {
        "issues": [
            {
                "type": "test_issue",
                "severity": "high",
                "description": "Test",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Fix",
                "related_rules": ["rule1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = validation_agent._extract_issues(analysis)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(validation_agent):
    """Test confidence calculation."""
    validations = [
        {
            "confidence": 0.8,
            "passed": True
        },
        {
            "confidence": 0.6,
            "passed": True
        }
    ]
    
    issues = [
        {
            "severity": "low",
            "type": "minor"
        },
        {
            "severity": "medium",
            "type": "warning"
        }
    ]
    
    confidence = validation_agent._calculate_confidence(validations, issues)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Validation confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(validation_agent):
    """Test validity determination."""
    validations = [
        {
            "passed": True,
            "confidence": 0.8
        },
        {
            "passed": True,
            "confidence": 0.7
        },
        {
            "passed": False,
            "confidence": 0.6
        }
    ]
    
    # Test with no critical issues
    issues = [
        {
            "severity": "low",
            "type": "minor"
        }
    ]
    
    is_valid = validation_agent._determine_validity(validations, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed validations
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = validation_agent._determine_validity(validations, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(validation_agent):
    """Test error handling during validation."""
    # Make LLM raise an error
    validation_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await validation_agent.validate_content({"content": "test"}, "structure")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.validations) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(validation_agent):
    """Test domain awareness in validation."""
    content = {"content": "test"}
    result = await validation_agent.validate_content(content, "structure")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    validation_agent.domain = "personal"
    result = await validation_agent.validate_content(content, "structure")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
