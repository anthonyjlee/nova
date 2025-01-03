"""Tests for the specialized ParsingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.parsing_agent import ParsingAgent
from src.nia.nova.core.parsing import ParseResult

@pytest.fixture(autouse=True)
def clear_agent_registry():
    """Clear TinyTroupe agent registry between tests."""
    from tinytroupe.agent import TinyPerson
    TinyPerson.all_agents.clear()

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = AsyncMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "statement": "Key concept",
                "type": "concept",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "complexity": 0.7
            },
            {
                "statement": "Need validation",
                "type": "validation_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "key_points": [
            {
                "statement": "Main point",
                "type": "key_point",
                "confidence": 0.8,
                "importance": 0.9
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
            "complexity_factors": [
                {
                    "factor": "readability",
                    "weight": 0.8
                }
            ]
        }
    })
    
    # Mock semantic store
    memory.semantic = AsyncMock()
    memory.semantic.store = AsyncMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    memory.semantic.store.store_memory = AsyncMock()
    
    # Mock episodic store
    memory.episodic = AsyncMock()
    memory.episodic.store = AsyncMock()
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar parse"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    memory.episodic.store.store_memory = AsyncMock()
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def parsing_agent(mock_memory_system, mock_world, request):
    """Create a ParsingAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestParsing_{request.node.name}"
    return ParsingAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(parsing_agent):
    """Test agent initialization."""
    assert "TestParsing" in parsing_agent.name
    assert parsing_agent.domain == "professional"
    assert parsing_agent.agent_type == "parsing"
    
    # Verify attributes were initialized
    attributes = parsing_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify parsing-specific attributes
    assert "Extract structured information" in attributes["desires"]
    assert attributes["emotions"]["towards_content"] == "focused"
    assert "text_parsing" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(parsing_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await parsing_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "content_complexity" in parsing_agent.emotions
    assert any("Validate" in desire for desire in parsing_agent.desires)

@pytest.mark.asyncio
async def test_parse_and_store(parsing_agent, mock_memory_system):
    """Test text parsing with domain awareness."""
    text = "Text content to parse"
    context = {"setting": "test"}
    
    result = await parsing_agent.parse_and_store(text, context)
    
    # Verify result structure
    assert isinstance(result, ParseResult)
    assert len(result.concepts) > 0
    assert len(result.key_points) > 0
    assert result.confidence > 0
    assert result.structure is not None
    
    # Verify memory storage was attempted
    mock_memory_system.episodic.store.store_memory.assert_called_once()
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(parsing_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await parsing_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await parsing_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_parse_with_different_domains(parsing_agent):
    """Test parsing with different domain configurations."""
    text = "test content"
    
    # Test professional domain
    prof_result = await parsing_agent.parse_and_store(
        text,
        {"domain": "professional"}
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    parsing_agent.domain = "personal"
    pers_result = await parsing_agent.parse_and_store(
        text,
        {"domain": "personal"}
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(parsing_agent, mock_memory_system):
    """Test error handling during parsing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await parsing_agent.parse_and_store("test")
    
    # Verify error handling
    assert isinstance(result, ParseResult)
    assert result.confidence == 0.0
    assert len(result.concepts) == 1
    assert result.concepts[0]["type"] == "error"
    assert len(result.key_points) == 1
    assert result.key_points[0]["type"] == "error"
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(parsing_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    text = "test content"
    
    # Force high confidence result
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [{"type": "concept", "description": "positive"}],
        "key_points": [],
        "confidence": 0.9,
        "structure": {}
    }
    
    result = await parsing_agent.parse_and_store(text)
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call.args[0]) for call in reflection_calls)
    
    # Test low confidence case
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [{"type": "concept", "description": "negative"}],
        "key_points": [],
        "confidence": 0.2,
        "structure": {}
    }
    
    result = await parsing_agent.parse_and_store(text)
    
    # Verify low confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Low confidence" in str(call.args[0]) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(parsing_agent):
    """Test emotion updates based on content complexity."""
    content = {"text": "Test content"}
    
    await parsing_agent.process(content)
    
    # Verify emotion updates
    assert "content_complexity" in parsing_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(parsing_agent):
    """Test desire updates based on validation needs."""
    content = {"text": "Test content"}
    
    await parsing_agent.process(content)
    
    # Verify desire updates
    assert any("Validate" in desire for desire in parsing_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
