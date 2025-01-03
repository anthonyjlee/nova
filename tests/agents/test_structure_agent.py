"""Tests for the specialized StructureAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.structure_agent import StructureAgent
from src.nia.nova.core.structure import StructureResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "response": "Structure analysis complete",
        "concepts": [
            {
                "name": "TestStructure",
                "type": "complexity",
                "description": "moderate",
                "confidence": 0.8
            },
            {
                "name": "DomainValidation",
                "type": "domain_validation",
                "description": "stable",
                "confidence": 0.9
            }
        ],
        "key_points": ["Test point"]
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def structure_agent(mock_memory_system, mock_world, request):
    """Create a StructureAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestStructure_{request.node.name}"
    return StructureAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(structure_agent):
    """Test agent initialization."""
    assert "TestStructure" in structure_agent.name
    assert structure_agent.domain == "professional"
    assert structure_agent.agent_type == "structure"
    
    # Verify attributes were initialized
    attributes = structure_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify domain-specific attributes
    assert "Maintain domain boundaries" in attributes["desires"]
    assert "towards_validation" in attributes["emotions"]
    assert "domain_validation" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(structure_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await structure_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "structure_complexity" in structure_agent.emotions
    assert "validation_state" in structure_agent.emotions

@pytest.mark.asyncio
async def test_analyze_and_store(structure_agent, mock_memory_system):
    """Test structure analysis with domain awareness."""
    text = "test:\n    nested: value"
    schema = {"type": "object"}
    
    result = await structure_agent.analyze_and_store(
        text,
        expected_schema=schema,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, StructureResult)
    assert result.response == "Structure analysis complete"
    assert len(result.concepts) > 0
    assert len(result.key_points) > 0
    
    # Verify memory storage
    assert hasattr(structure_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_validate_and_store(structure_agent, mock_memory_system):
    """Test schema validation with domain awareness."""
    schema = {
        "type": "object",
        "properties": {
            "test": {"type": "string"}
        }
    }
    
    result = await structure_agent.validate_and_store(
        schema,
        target_domain="professional"
    )
    
    # Verify validation result
    assert "is_valid" in result
    assert "domain" in result
    assert result["domain"] == "professional"
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(structure_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await structure_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await structure_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(structure_agent):
    """Test analysis with different domain configurations."""
    text = "test: value"
    
    # Test professional domain
    prof_result = await structure_agent.analyze_and_store(
        text,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await structure_agent.analyze_and_store(
        text,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(structure_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await structure_agent.analyze_and_store("Test content")
    
    # Verify error handling
    assert isinstance(result, StructureResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(structure_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    text = "test: value"
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.9
    
    result = await structure_agent.analyze_and_store(text)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value["confidence"] = 0.2
    
    result = await structure_agent.analyze_and_store(text)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(structure_agent):
    """Test emotion updates based on analysis and validation."""
    content = {"text": "Test content"}
    
    await structure_agent.process(content)
    
    # Verify emotion updates
    assert structure_agent.emotions["structure_complexity"] == "moderate"
    assert structure_agent.emotions["validation_state"] == "stable"

if __name__ == "__main__":
    pytest.main([__file__])
