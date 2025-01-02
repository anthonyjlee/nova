"""Tests for the specialized LoggingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.logging_agent import LoggingAgent
from src.nia.nova.core.logging import LoggingResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "logging": {
            "type": "debug",
            "logs": {
                "main": {
                    "type": "processor",
                    "level": "debug",
                    "message": "Main log"
                }
            }
        },
        "logs": [
            {
                "type": "log",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "logging_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_context",
                "severity": "medium",
                "description": "Missing context",
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
            "content": {"content": "Similar logging"},
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
def logging_agent(mock_memory_system, mock_world):
    """Create a LoggingAgent instance with mock dependencies."""
    return LoggingAgent(
        name="TestLogging",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(logging_agent):
    """Test agent initialization."""
    assert logging_agent.name == "TestLogging"
    assert logging_agent.domain == "professional"
    assert logging_agent.agent_type == "logging"
    
    # Verify attributes were initialized
    attributes = logging_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify logging-specific attributes
    assert "Process logs effectively" in attributes["desires"]
    assert "towards_logs" in attributes["emotions"]
    assert "log_processing" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(logging_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await logging_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "logging_state" in logging_agent.emotions
    assert "domain_state" in logging_agent.emotions
    assert any("Process" in desire for desire in logging_agent.desires)

@pytest.mark.asyncio
async def test_process_and_store(logging_agent, mock_memory_system):
    """Test log processing with domain awareness."""
    content = {
        "text": "Content to process",
        "type": "debug"
    }
    
    result = await logging_agent.process_and_store(
        content,
        logging_type="debug",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, LoggingResult)
    assert result.logging["type"] == "debug"
    assert len(result.logging["logs"]) == 1
    assert len(result.logs) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(logging_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(logging_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await logging_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await logging_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_process_with_different_domains(logging_agent):
    """Test processing with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await logging_agent.process_and_store(
        content,
        logging_type="debug",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await logging_agent.process_and_store(
        content,
        logging_type="debug",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(logging_agent, mock_memory_system):
    """Test error handling during processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await logging_agent.process_and_store(
        {"content": "test"},
        logging_type="debug"
    )
    
    # Verify error handling
    assert isinstance(result, LoggingResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.logs) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(logging_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["logs"] = [
        {
            "type": "test_log",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await logging_agent.process_and_store(
        content,
        logging_type="debug"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["logs"] = [
        {
            "type": "test_log",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await logging_agent.process_and_store(
        content,
        logging_type="debug"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Logging failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(logging_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {"text": "test"}
    
    # Add critical issue
    mock_memory_system.llm.analyze.return_value["issues"] = [
        {
            "type": "critical_issue",
            "severity": "high",
            "description": "Critical problem"
        }
    ]
    
    result = await logging_agent.process_and_store(
        content,
        logging_type="debug"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical logging issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_log_reflection(logging_agent, mock_memory_system):
    """Test reflection recording for important logs."""
    content = {"text": "test"}
    
    # Add important log
    mock_memory_system.llm.analyze.return_value["logs"] = [
        {
            "type": "important_log",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical log"
        }
    ]
    
    result = await logging_agent.process_and_store(
        content,
        logging_type="debug"
    )
    
    # Verify important log reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important logs processed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(logging_agent):
    """Test emotion updates based on logging results."""
    content = {"text": "Test content"}
    
    await logging_agent.process(content)
    
    # Verify emotion updates
    assert "logging_state" in logging_agent.emotions
    assert "domain_state" in logging_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(logging_agent):
    """Test desire updates based on logging needs."""
    content = {"text": "Test content"}
    
    await logging_agent.process(content)
    
    # Verify desire updates
    assert any("Process" in desire for desire in logging_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
