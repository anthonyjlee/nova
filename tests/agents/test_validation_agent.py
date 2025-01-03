"""Tests for the specialized ValidationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.validation_agent import ValidationAgent
from src.nia.nova.core.validation import ValidationResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    # Mock LLM responses
    def mock_analyze(*args, **kwargs):
        if "validation_type" in kwargs:
            # For validation_and_store
            return {
                "is_valid": True,
                "validations": [{
                    "rule": "test_rule",
                    "passed": True,
                    "confidence": 0.8,
                    "description": "positive"
                }],
                "confidence": 0.8,
                "metadata": {"domain": kwargs.get("metadata", {}).get("domain", "professional")},
                "issues": [{
                    "type": "test_issue",
                    "severity": "medium",
                    "description": "Test issue"
                }]
            }
        else:
            # For process
            response = AgentResponse(
                content="Test validation result",
                confidence=0.8,
                metadata={
                    "domain": "professional",
                    "agent_type": "validation",
                    "timestamp": datetime.now().isoformat()
                }
            )
            # Add concepts directly to response
            response.concepts = [{
                "name": "Validation Analysis",
                "type": "validation_result",
                "description": "Test validation result",
                "domain_relevance": 0.8,
                "related": []
            }, {
                "name": "Test Need",
                "type": "validation_need",
                "description": "Requires validation",
                "domain_relevance": 0.7,
                "related": []
            }]
            return response
    
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(side_effect=mock_analyze)
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    memory.semantic.store.store_concept = AsyncMock()
    memory.semantic.driver = memory.semantic.store
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar validation"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    # Mock store method
    memory.store = AsyncMock()
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture(autouse=True)
def clear_tinyperson_registry():
    """Clear TinyPerson's agent registry before each test."""
    from tinytroupe import TinyPerson
    TinyPerson.all_agents.clear()
    yield
    TinyPerson.all_agents.clear()

@pytest.fixture
def validation_agent(mock_memory_system, mock_world, clear_tinyperson_registry, request):
    """Create a ValidationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestValidation_{request.node.name}"
    return ValidationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(validation_agent):
    """Test agent initialization."""
    assert "TestValidation" in validation_agent.name
    assert validation_agent.domain == "professional"
    assert validation_agent.agent_type == "validation"
    
    # Verify attributes were initialized
    attributes = validation_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify validation-specific attributes
    assert "Ensure content quality" in attributes["desires"]
    assert "towards_validation" in attributes["emotions"]
    assert "content_validation" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(validation_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await validation_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "validation_state" in validation_agent.emotions
    assert "domain_state" in validation_agent.emotions
    assert any("Address" in desire for desire in validation_agent.desires)

@pytest.mark.asyncio
async def test_validate_and_store(validation_agent, mock_memory_system):
    """Test content validation with domain awareness."""
    content = {
        "content": "Content to validate",
        "type": "test"
    }
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ValidationResult)
    assert len(result.validations) > 0
    assert result.confidence > 0
    assert len(result.issues) > 0
    
    # Verify memory storage
    assert hasattr(validation_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(validation_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await validation_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await validation_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_validate_with_different_domains(validation_agent):
    """Test validation with different domain configurations."""
    content = {"content": "test"}
    
    # Test professional domain
    prof_result = await validation_agent.validate_and_store(
        content,
        validation_type="structure",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await validation_agent.validate_and_store(
        content,
        validation_type="structure",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(validation_agent, mock_memory_system):
    """Test error handling during validation."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await validation_agent.validate_and_store(
        {"content": "test"},
        validation_type="structure"
    )
    
    # Verify error handling
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.validations) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(validation_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Force valid result with high confidence
    def mock_analyze_valid(*args, **kwargs):
        if "validation_type" in kwargs:
            return {
                "is_valid": True,
                "validations": [{
                    "rule": "test_rule",
                    "passed": True,
                    "confidence": 0.9,
                    "description": "positive"
                }],
                "confidence": 0.9,
                "metadata": {"domain": kwargs.get("metadata", {}).get("domain", "professional")},
                "issues": []
            }
        else:
            return AgentResponse(
                content="Test validation result",
                confidence=0.9,
                metadata={
                    "domain": "professional",
                    "agent_type": "validation",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    mock_memory_system.llm.analyze = AsyncMock(side_effect=mock_analyze_valid)
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    def mock_analyze_invalid(*args, **kwargs):
        if "validation_type" in kwargs:
            return {
                "is_valid": False,
                "validations": [{
                    "rule": "test_rule",
                    "passed": False,
                    "confidence": 0.5,
                    "description": "negative"
                }],
                "confidence": 0.5,
                "metadata": {"domain": kwargs.get("metadata", {}).get("domain", "professional")},
                "issues": [{
                    "type": "test_issue",
                    "severity": "medium",
                    "description": "Test issue"
                }]
            }
        else:
            return AgentResponse(
                content="Test validation result",
                confidence=0.5,
                metadata={
                    "domain": "professional",
                    "agent_type": "validation",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    mock_memory_system.llm.analyze = AsyncMock(side_effect=mock_analyze_invalid)
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Validation failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(validation_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {"content": "test"}
    
    # Add critical issue
    def mock_analyze_critical(*args, **kwargs):
        return {
            "is_valid": False,
            "validations": [],
            "confidence": 0.5,
            "metadata": {"domain": kwargs.get("metadata", {}).get("domain", "professional")},
            "issues": [{
                "type": "critical_issue",
                "severity": "high",
                "description": "Critical problem"
            }]
        }
    
    mock_memory_system.llm.analyze = AsyncMock(side_effect=mock_analyze_critical)
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical validation issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(validation_agent):
    """Test emotion updates based on validation results."""
    content = {"text": "Test content"}
    
    await validation_agent.process(content)
    
    # Verify emotion updates
    assert "validation_state" in validation_agent.emotions
    assert "domain_state" in validation_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(validation_agent):
    """Test desire updates based on validation needs."""
    content = {"text": "Test content"}
    
    await validation_agent.process(content)
    
    # Verify desire updates
    assert any("Address" in desire for desire in validation_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
