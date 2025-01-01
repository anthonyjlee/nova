"""Tests for the ParsingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.parsing_agent import ParsingAgent
from src.nia.nova.core.parsing import ParseResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "name": "TestConcept",
                "type": "test",
                "description": "A test concept",
                "confidence": 0.8
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
def parsing_agent(mock_memory_system, mock_world):
    """Create a ParsingAgent instance with mock dependencies."""
    return ParsingAgent(
        name="TestParser",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(parsing_agent):
    """Test agent initialization."""
    assert parsing_agent.name == "TestParser"
    assert parsing_agent.domain == "professional"
    assert parsing_agent.agent_type == "parsing"
    
    # Verify attributes were initialized
    attributes = parsing_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"

@pytest.mark.asyncio
async def test_process_content(parsing_agent, mock_memory_system):
    """Test content processing."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await parsing_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    if hasattr(response, "concepts"):
        for concept in response.concepts:
            if concept.get("type") == "complexity":
                assert "content_complexity" in parsing_agent.emotions

@pytest.mark.asyncio
async def test_parse_and_store(parsing_agent, mock_memory_system):
    """Test parsing and storing results."""
    text = "Test content for parsing"
    
    result = await parsing_agent.parse_and_store(text)
    
    # Verify parsing result
    assert isinstance(result, ParseResult)
    assert len(result.concepts) > 0
    assert len(result.key_points) > 0
    
    # Verify memory storage
    assert hasattr(parsing_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called_once()

@pytest.mark.asyncio
async def test_domain_access(parsing_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    mock_memory_system.semantic.store.get_domain_access.return_value = True
    assert await parsing_agent.get_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    assert not await parsing_agent.get_domain_access("restricted")
    
    # Test domain validation
    with pytest.raises(PermissionError):
        await parsing_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_reflection_recording(parsing_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    reflection = "Test reflection"
    await parsing_agent.record_reflection(reflection)
    
    # Verify reflection was recorded with domain
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        content=reflection,
        domain=parsing_agent.domain
    )

@pytest.mark.asyncio
async def test_parse_with_different_domains(mock_memory_system, mock_world):
    """Test parsing with different domain configurations."""
    # Create agents for different domains
    professional_agent = ParsingAgent(
        name="ProfessionalParser",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )
    
    personal_agent = ParsingAgent(
        name="PersonalParser",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="personal"
    )
    
    text = "Test content"
    
    # Test professional domain parsing
    prof_result = await professional_agent.parse_and_store(text)
    assert prof_result.metadata.get("domain") == "professional"
    
    # Test personal domain parsing
    pers_result = await personal_agent.parse_and_store(text)
    assert pers_result.metadata.get("domain") == "personal"

@pytest.mark.asyncio
async def test_error_handling(parsing_agent, mock_memory_system):
    """Test error handling during parsing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    # Should still get a valid result with zero confidence
    result = await parsing_agent.parse_and_store("Test content")
    assert isinstance(result, ParseResult)
    assert result.confidence == 0.0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_memory_system_integration(parsing_agent):
    """Test integration with memory system components."""
    # Verify LLM integration
    assert parsing_agent.llm is not None
    
    # Verify store integration
    assert parsing_agent.store is not None
    assert parsing_agent.vector_store is not None
    
    # Verify schema validator initialization
    assert parsing_agent.schema_validator is not None
    assert "concepts" in parsing_agent.schema_validator
    assert "key_points" in parsing_agent.schema_validator

if __name__ == "__main__":
    pytest.main([__file__])
