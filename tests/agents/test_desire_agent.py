"""Tests for the specialized DesireAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.desire_agent import DesireAgent
from src.nia.nova.core.desire import DesireResult

@pytest.fixture
def desire_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a DesireAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestDesire_{request.node.name}"
    
    # Update mock memory system for desire agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "statement": "Complete this task",
                "type": "desire",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9
            },
            {
                "statement": "Need more resources",
                "type": "motivation_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "motivations": {
            "reasons": ["reason1"],
            "drivers": ["driver1"],
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ]
        }
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return DesireAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(desire_agent):
    """Test agent initialization."""
    assert "TestDesire" in desire_agent.name
    assert desire_agent.domain == "professional"
    assert desire_agent.agent_type == "desire"
    
    # Verify attributes were initialized
    attributes = desire_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify domain-specific attributes
    assert "Maintain domain boundaries" in attributes["desires"]
    assert "towards_domain" in attributes["emotions"]
    assert "domain_validation" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(desire_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await desire_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in desire_agent.emotions
    assert "domain_state" in desire_agent.emotions
    assert any("Address" in desire for desire in desire_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(desire_agent, mock_memory_system):
    """Test desire analysis with domain awareness."""
    content = {
        "content": "I want to achieve this goal",
        "type": "statement"
    }
    
    result = await desire_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, DesireResult)
    assert len(result.desires) > 0
    assert result.confidence > 0
    assert result.motivations is not None
    
    # Verify memory storage
    assert hasattr(desire_agent, "store_memory")
    
    # Verify reflection was recorded (high confidence case)
    if result.confidence > 0.8:
        mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(desire_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await desire_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await desire_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(desire_agent):
    """Test analysis with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await desire_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await desire_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(desire_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await desire_agent.analyze_and_store({"content": "test"})
    
    # Verify error handling
    assert isinstance(result, DesireResult)
    assert result.confidence == 0.0
    assert len(result.desires) == 0
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(desire_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "statement": "Important goal",
                "type": "desire",
                "confidence": 0.9,
                "domain_relevance": 0.9
            }
        ],
        "motivations": {
            "reasons": ["important reason"],
            "drivers": ["key driver"],
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ]
        }
    })
    
    result = await desire_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence desire analysis completed in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "statement": "Unclear goal",
                "type": "desire",
                "confidence": 0.2,
                "domain_relevance": 0.5
            }
        ],
        "motivations": {
            "reasons": ["unclear reason"],
            "drivers": ["weak driver"],
            "priority_factors": []
        }
    })
    
    result = await desire_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Low confidence desire analysis in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(desire_agent):
    """Test emotion updates based on analysis."""
    content = {"text": "Test content"}
    
    await desire_agent.process(content)
    
    # Verify emotion updates
    assert desire_agent.emotions["analysis_state"] == "positive"
    assert desire_agent.emotions["domain_state"] == "highly_relevant"

@pytest.mark.asyncio
async def test_desire_updates(desire_agent):
    """Test desire updates based on motivation needs."""
    content = {"text": "Test content"}
    
    await desire_agent.process(content)
    
    # Verify desire updates
    assert any("Address" in desire for desire in desire_agent.desires)

@pytest.mark.asyncio
async def test_priority_reflection(desire_agent, mock_memory_system):
    """Test reflection recording for priority factors."""
    content = {"content": "test"}
    
    # Configure mock LLM response with high priority factors
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "statement": "Critical goal",
                "type": "desire",
                "confidence": 0.9,
                "domain_relevance": 0.9
            }
        ],
        "motivations": {
            "reasons": ["critical reason"],
            "drivers": ["urgent driver"],
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.95
                },
                {
                    "factor": "importance",
                    "weight": 0.9
                }
            ]
        }
    })
    
    result = await desire_agent.analyze_and_store(content)
    
    # Verify priority reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High priority factors identified in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
