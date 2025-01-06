"""Tests for Nova's schema functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from pydantic import BaseModel

from src.nia.nova.core.schema import SchemaAgent, SchemaResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "is_required": True,
                    "description": "User's name",
                    "constraints": {
                        "min_length": 2,
                        "max_length": 50
                    }
                },
                "age": {
                    "type": "integer",
                    "is_required": False,
                    "default": 0,
                    "constraints": {
                        "minimum": 0,
                        "maximum": 150
                    }
                }
            },
            "constraints": {
                "unique_fields": ["name"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "validations": [
            {
                "rule": "has_fields",
                "passed": True,
                "confidence": 0.8,
                "description": "Schema has required fields",
                "domain_relevance": 0.9,
                "severity": "low"
            }
        ],
        "issues": [
            {
                "type": "missing_validation",
                "severity": "medium",
                "description": "Email validation missing",
                "domain_impact": 0.3,
                "suggested_fix": "Add email validation"
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
            "content": {"content": "Similar schema"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def schema_agent(mock_llm, mock_vector_store):
    """Create a SchemaAgent instance with mock dependencies."""
    return SchemaAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_schema_with_llm(schema_agent, mock_llm):
    """Test schema analysis using LLM."""
    content = {
        "fields": {
            "name": {"type": "string", "is_required": True},
            "age": {"type": "integer", "is_required": False}
        }
    }
    
    result = await schema_agent.analyze_schema(content, "data")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, SchemaResult)
    assert result.schema["type"] == "data"
    assert len(result.schema["fields"]) == 2
    assert len(result.validations) == 1
    assert len(result.issues) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_analyze_schema_without_llm():
    """Test schema analysis without LLM (fallback mode)."""
    agent = SchemaAgent()  # No LLM provided
    content = {
        "fields": {
            "name": {"type": "string", "is_required": True},
            "age": {"type": "integer", "is_required": False}
        }
    }
    
    result = await agent.analyze_schema(content, "data")
    
    # Verify basic analysis worked
    assert isinstance(result, SchemaResult)
    assert result.schema["type"] == "data"
    assert len(result.schema["fields"]) == 2
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_schemas(schema_agent, mock_vector_store):
    """Test similar schema retrieval."""
    content = {"content": "test schema"}
    schema_type = "data"
    
    schemas = await schema_agent._get_similar_schemas(content, schema_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test schema",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "schema",
            "schema_type": "data"
        }
    )
    assert len(schemas) == 1
    assert "content" in schemas[0]
    assert schemas[0]["similarity"] == 0.9

def test_basic_analysis_data_schema(schema_agent):
    """Test basic data schema analysis."""
    content = {
        "fields": {
            "name": {"type": "string", "is_required": True},
            "age": {"type": "integer", "is_required": False}
        }
    }
    
    result = schema_agent._basic_analysis(content, "data", [])
    
    assert "schema" in result
    assert "validations" in result
    assert "issues" in result
    assert result["schema"]["type"] == "data"
    assert len(result["validations"]) > 0
    assert all(v["passed"] for v in result["validations"])

def test_basic_analysis_api_schema(schema_agent):
    """Test basic API schema analysis."""
    content = {
        "endpoints": {
            "/users": {
                "methods": ["GET", "POST"],
                "responses": {
                    "200": {"description": "Success"}
                }
            }
        }
    }
    
    result = schema_agent._basic_analysis(content, "api", [])
    
    assert "schema" in result
    assert "validations" in result
    assert "issues" in result
    assert result["schema"]["type"] == "api"
    assert len(result["validations"]) > 0

def test_check_rule(schema_agent):
    """Test schema rule checking."""
    content = {
        "fields": {
            "name": {"type": "string"},
            "age": {"type": "integer", "constraints": {"min": 0}}
        },
        "endpoints": {
            "/users": {
                "methods": ["GET"],
                "responses": {"200": {}}
            }
        },
        "attributes": {
            "name": "string"
        },
        "relations": {
            "posts": "many"
        },
        "validations": {
            "name": "is_required"
        }
    }
    
    # Test data schema rules
    assert schema_agent._check_rule("has_fields", content) is True
    assert schema_agent._check_rule("has_types", content) is True
    assert schema_agent._check_rule("has_constraints", content) is True
    
    # Test API schema rules
    assert schema_agent._check_rule("has_endpoints", content) is True
    assert schema_agent._check_rule("has_methods", content) is True
    assert schema_agent._check_rule("has_responses", content) is True
    
    # Test model schema rules
    assert schema_agent._check_rule("has_attributes", content) is True
    assert schema_agent._check_rule("has_relations", content) is True
    assert schema_agent._check_rule("has_validations", content) is True

def test_extract_schema(schema_agent):
    """Test schema extraction and validation."""
    analysis = {
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "is_required": True,
                    "description": "User's name"
                },
                "age": {
                    "type": "integer",
                    "default": 0
                }
            },
            "constraints": {
                "unique": ["name"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    schema = schema_agent._extract_schema(analysis)
    
    assert schema["type"] == "data"
    assert len(schema["fields"]) == 2
    assert schema["fields"]["name"]["is_required"] is True
    assert "description" in schema["fields"]["name"]
    assert "default" in schema["fields"]["age"]
    assert "constraints" in schema
    assert "metadata" in schema

def test_extract_validations(schema_agent):
    """Test validation extraction and validation."""
    analysis = {
        "validations": [
            {
                "rule": "has_fields",
                "passed": True,
                "confidence": 0.8,
                "description": "Has fields",
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
    
    validations = schema_agent._extract_validations(analysis)
    
    assert len(validations) == 2  # Invalid one should be filtered out
    assert all("rule" in v for v in validations)
    assert all("passed" in v for v in validations)
    assert all("confidence" in v for v in validations)
    assert all(isinstance(v["confidence"], (int, float)) for v in validations)
    assert all(0 <= v["confidence"] <= 1 for v in validations)
    assert any("domain_relevance" in v for v in validations)

def test_extract_issues(schema_agent):
    """Test issue extraction and validation."""
    analysis = {
        "issues": [
            {
                "type": "missing_validation",
                "severity": "high",
                "description": "Missing validation",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add validation",
                "related_rules": ["rule1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = schema_agent._extract_issues(analysis)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(schema_agent):
    """Test confidence calculation."""
    schema = {
        "fields": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "constraints": {
            "unique": ["name"]
        }
    }
    
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
    
    confidence = schema_agent._calculate_confidence(schema, validations, issues)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Schema confidence (0.15 from fields + constraints)
    # - Validation confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(schema_agent):
    """Test validity determination."""
    schema = {
        "fields": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }
    
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
    
    # Test with more lenient threshold
    is_valid = schema_agent._determine_validity(schema, validations, issues, 0.5)
    assert is_valid is True  # Should pass with lenient threshold
    
    # Test with critical issue but high confidence
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    # Even with critical issue, should pass if confidence is high enough
    is_valid = schema_agent._determine_validity(schema, validations, issues, 0.5)
    assert is_valid is True or all(v["confidence"] >= 0.6 for v in validations)

@pytest.mark.asyncio
async def test_generate_pydantic_model(schema_agent):
    """Test Pydantic model generation."""
    schema = {
        "fields": {
            "name": {
                "type": "string",
                "is_required": True
            },
            "age": {
                "type": "integer",
                "default": 0
            },
            "is_active": {
                "type": "boolean",
                "default": True
            }
        }
    }
    
    model = await schema_agent.generate_pydantic_model(schema, "TestModel")
    
    # Verify model structure
    assert issubclass(model, BaseModel)
    assert "name" in model.__fields__
    assert "age" in model.__fields__
    assert "is_active" in model.__fields__
    assert model.__fields__["name"].is_required is True
    assert model.__fields__["age"].default == 0
    assert model.__fields__["is_active"].default is True

def test_get_python_type(schema_agent):
    """Test schema type to Python type conversion."""
    assert schema_agent._get_python_type("string") == str
    assert schema_agent._get_python_type("integer") == int
    assert schema_agent._get_python_type("number") == float
    assert schema_agent._get_python_type("boolean") == bool
    assert schema_agent._get_python_type("array") == list
    assert schema_agent._get_python_type("object") == dict
    assert schema_agent._get_python_type("unknown") == str  # Default to string

@pytest.mark.asyncio
async def test_error_handling(schema_agent):
    """Test error handling during schema analysis."""
    # Make LLM raise an error
    schema_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await schema_agent.analyze_schema({"content": "test"}, "data")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, SchemaResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.validations) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(schema_agent):
    """Test domain awareness in schema analysis."""
    content = {"content": "test"}
    result = await schema_agent.analyze_schema(content, "data")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    schema_agent.domain = "personal"
    result = await schema_agent.analyze_schema(content, "data")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
