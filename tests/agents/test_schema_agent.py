"""Tests for the specialized SchemaAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from pydantic import BaseModel

from src.nia.agents.specialized.schema_agent import SchemaAgent
from src.nia.nova.core.schema import SchemaResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True,
                    "description": "User's name"
                },
                "age": {
                    "type": "integer",
                    "default": 0
                }
            }
        },
        "validations": [
            {
                "rule": "has_fields",
                "passed": True,
                "confidence": 0.8,
                "description": "positive",
                "domain_relevance": 0.9,
                "severity": "low"
            },
            {
                "rule": "schema_need",
                "passed": False,
                "confidence": 0.7,
                "description": "requires attention"
            }
        ],
        "issues": [
            {
                "type": "missing_validation",
                "severity": "medium",
                "description": "Missing validation",
                "domain_impact": 0.3
            }
        ]
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar schema"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def schema_agent(mock_memory_system, mock_world):
    """Create a SchemaAgent instance with mock dependencies."""
    return SchemaAgent(
        name="TestSchema",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(schema_agent):
    """Test agent initialization."""
    assert schema_agent.name == "TestSchema"
    assert schema_agent.domain == "professional"
    assert schema_agent.agent_type == "schema"
    
    # Verify attributes were initialized
    attributes = schema_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify schema-specific attributes
    assert "Maintain schema integrity" in attributes["desires"]
    assert "towards_schema" in attributes["emotions"]
    assert "schema_analysis" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(schema_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await schema_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "schema_state" in schema_agent.emotions
    assert "domain_state" in schema_agent.emotions
    assert any("Improve" in desire for desire in schema_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(schema_agent, mock_memory_system):
    """Test schema analysis with domain awareness."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": False}
        }
    }
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, SchemaResult)
    assert result.schema["type"] == "data"
    assert len(result.schema["fields"]) == 2
    assert result.confidence > 0
    assert len(result.issues) > 0
    
    # Verify memory storage
    assert hasattr(schema_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(schema_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await schema_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await schema_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(schema_agent):
    """Test schema analysis with different domain configurations."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        }
    }
    
    # Test professional domain
    prof_result = await schema_agent.analyze_and_store(
        content,
        schema_type="data",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await schema_agent.analyze_and_store(
        content,
        schema_type="data",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(schema_agent, mock_memory_system):
    """Test error handling during schema analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await schema_agent.analyze_and_store(
        {"content": "test"},
        schema_type="data"
    )
    
    # Verify error handling
    assert isinstance(result, SchemaResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.validations) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(schema_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        }
    }
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["validations"] = [
        {
            "rule": "test_rule",
            "passed": True,
            "confidence": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["validations"] = [
        {
            "rule": "test_rule",
            "passed": False,
            "confidence": 0.5
        }
    ]
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Schema validation failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(schema_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        }
    }
    
    # Add critical issue
    mock_memory_system.llm.analyze.return_value["issues"] = [
        {
            "type": "critical_issue",
            "severity": "high",
            "description": "Critical problem"
        }
    ]
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical schema issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_generate_model(schema_agent, mock_memory_system):
    """Test Pydantic model generation with domain awareness."""
    content = {
        "fields": {
            "name": {
                "type": "string",
                "required": True
            },
            "age": {
                "type": "integer",
                "default": 0
            }
        }
    }
    
    # Force valid schema result
    mock_memory_system.llm.analyze.return_value["validations"] = [
        {
            "rule": "test_rule",
            "passed": True,
            "confidence": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    model = await schema_agent.generate_model(
        content,
        "TestModel",
        target_domain="professional"
    )
    
    # Verify model structure
    assert issubclass(model, BaseModel)
    assert "name" in model.__fields__
    assert "age" in model.__fields__
    assert model.__fields__["name"].required is True
    assert model.__fields__["age"].default == 0
    
    # Verify reflection was recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Generated Pydantic model" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_generate_model_with_invalid_schema(schema_agent, mock_memory_system):
    """Test model generation with invalid schema."""
    content = {
        "fields": {
            "name": {"type": "invalid"}
        }
    }
    
    # Force invalid schema result
    mock_memory_system.llm.analyze.return_value["validations"] = [
        {
            "rule": "test_rule",
            "passed": False,
            "confidence": 0.3
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = [
        {
            "type": "invalid_type",
            "severity": "high",
            "description": "Invalid field type"
        }
    ]
    
    with pytest.raises(ValueError):
        await schema_agent.generate_model(
            content,
            "TestModel",
            target_domain="professional"
        )

@pytest.mark.asyncio
async def test_emotion_updates(schema_agent):
    """Test emotion updates based on schema results."""
    content = {"text": "Test content"}
    
    await schema_agent.process(content)
    
    # Verify emotion updates
    assert "schema_state" in schema_agent.emotions
    assert "domain_state" in schema_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(schema_agent):
    """Test desire updates based on schema needs."""
    content = {"text": "Test content"}
    
    await schema_agent.process(content)
    
    # Verify desire updates
    assert any("Improve" in desire for desire in schema_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
