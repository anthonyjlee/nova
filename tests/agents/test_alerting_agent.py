"""Tests for the specialized AlertingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.alerting_agent import AlertingAgent
from src.nia.nova.core.alerting import AlertingResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "alerting": {
            "type": "notification",
            "alerts": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main alert"
                }
            }
        },
        "alerts": [
            {
                "type": "alert",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "alerting_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_rule",
                "severity": "medium",
                "description": "Missing rule",
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
            "content": {"content": "Similar alerting"},
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
def alerting_agent(mock_memory_system, mock_world):
    """Create an AlertingAgent instance with mock dependencies."""
    return AlertingAgent(
        name="TestAlerting",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(alerting_agent):
    """Test agent initialization."""
    assert alerting_agent.name == "TestAlerting"
    assert alerting_agent.domain == "professional"
    assert alerting_agent.agent_type == "alerting"
    
    # Verify attributes were initialized
    attributes = alerting_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify alerting-specific attributes
    assert "Process alerts effectively" in attributes["desires"]
    assert "towards_alerts" in attributes["emotions"]
    assert "alert_processing" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(alerting_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await alerting_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "alerting_state" in alerting_agent.emotions
    assert "domain_state" in alerting_agent.emotions
    assert any("Process" in desire for desire in alerting_agent.desires)

@pytest.mark.asyncio
async def test_process_and_store(alerting_agent, mock_memory_system):
    """Test alert processing with domain awareness."""
    content = {
        "text": "Content to process",
        "type": "notification"
    }
    
    result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, AlertingResult)
    assert result.alerting["type"] == "notification"
    assert len(result.alerting["alerts"]) == 1
    assert len(result.alerts) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(alerting_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(alerting_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await alerting_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await alerting_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_process_with_different_domains(alerting_agent):
    """Test processing with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(alerting_agent, mock_memory_system):
    """Test error handling during processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await alerting_agent.process_and_store(
        {"content": "test"},
        alerting_type="notification"
    )
    
    # Verify error handling
    assert isinstance(result, AlertingResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.alerts) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(alerting_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["alerts"] = [
        {
            "type": "test_alert",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["alerts"] = [
        {
            "type": "test_alert",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Alerting failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(alerting_agent, mock_memory_system):
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
    
    result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical alerting issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_alert_reflection(alerting_agent, mock_memory_system):
    """Test reflection recording for important alerts."""
    content = {"text": "test"}
    
    # Add important alert
    mock_memory_system.llm.analyze.return_value["alerts"] = [
        {
            "type": "important_alert",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical alert"
        }
    ]
    
    result = await alerting_agent.process_and_store(
        content,
        alerting_type="notification"
    )
    
    # Verify important alert reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important alerts processed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(alerting_agent):
    """Test emotion updates based on alerting results."""
    content = {"text": "Test content"}
    
    await alerting_agent.process(content)
    
    # Verify emotion updates
    assert "alerting_state" in alerting_agent.emotions
    assert "domain_state" in alerting_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(alerting_agent):
    """Test desire updates based on alerting needs."""
    content = {"text": "Test content"}
    
    await alerting_agent.process(content)
    
    # Verify desire updates
    assert any("Process" in desire for desire in alerting_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
