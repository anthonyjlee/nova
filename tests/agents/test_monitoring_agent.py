"""Tests for the specialized MonitoringAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.monitoring_agent import MonitoringAgent
from src.nia.nova.core.monitoring import MonitoringResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "monitoring": {
            "type": "performance",
            "agents": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main agent"
                }
            }
        },
        "metrics": [
            {
                "type": "metric",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "monitoring_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_metric",
                "severity": "medium",
                "description": "Missing metric",
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
            "content": {"content": "Similar monitoring"},
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
def monitoring_agent(mock_memory_system, mock_world):
    """Create a MonitoringAgent instance with mock dependencies."""
    return MonitoringAgent(
        name="TestMonitoring",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(monitoring_agent):
    """Test agent initialization."""
    assert monitoring_agent.name == "TestMonitoring"
    assert monitoring_agent.domain == "professional"
    assert monitoring_agent.agent_type == "monitoring"
    
    # Verify attributes were initialized
    attributes = monitoring_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify monitoring-specific attributes
    assert "Monitor agents effectively" in attributes["desires"]
    assert "towards_agents" in attributes["emotions"]
    assert "agent_monitoring" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(monitoring_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await monitoring_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "monitoring_state" in monitoring_agent.emotions
    assert "domain_state" in monitoring_agent.emotions
    assert any("Monitor" in desire for desire in monitoring_agent.desires)

@pytest.mark.asyncio
async def test_monitor_and_store(monitoring_agent, mock_memory_system):
    """Test agent monitoring with domain awareness."""
    content = {
        "text": "Content to monitor",
        "type": "performance"
    }
    
    result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, MonitoringResult)
    assert result.monitoring["type"] == "performance"
    assert len(result.monitoring["agents"]) == 1
    assert len(result.metrics) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(monitoring_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(monitoring_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await monitoring_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await monitoring_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_monitor_with_different_domains(monitoring_agent):
    """Test monitoring with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(monitoring_agent, mock_memory_system):
    """Test error handling during monitoring."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await monitoring_agent.monitor_and_store(
        {"content": "test"},
        monitoring_type="performance"
    )
    
    # Verify error handling
    assert isinstance(result, MonitoringResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.metrics) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(monitoring_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["metrics"] = [
        {
            "type": "test_metric",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["metrics"] = [
        {
            "type": "test_metric",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Monitoring failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(monitoring_agent, mock_memory_system):
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
    
    result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical monitoring issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_metric_reflection(monitoring_agent, mock_memory_system):
    """Test reflection recording for important metrics."""
    content = {"text": "test"}
    
    # Add important metric
    mock_memory_system.llm.analyze.return_value["metrics"] = [
        {
            "type": "important_metric",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical metric"
        }
    ]
    
    result = await monitoring_agent.monitor_and_store(
        content,
        monitoring_type="performance"
    )
    
    # Verify important metric reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important monitoring metrics recorded" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(monitoring_agent):
    """Test emotion updates based on monitoring results."""
    content = {"text": "Test content"}
    
    await monitoring_agent.process(content)
    
    # Verify emotion updates
    assert "monitoring_state" in monitoring_agent.emotions
    assert "domain_state" in monitoring_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(monitoring_agent):
    """Test desire updates based on monitoring needs."""
    content = {"text": "Test content"}
    
    await monitoring_agent.process(content)
    
    # Verify desire updates
    assert any("Monitor" in desire for desire in monitoring_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
