"""Tests for the specialized MetricsAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.metrics_agent import MetricsAgent
from src.nia.nova.core.metrics import MetricsResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "metrics": {
            "type": "performance",
            "metrics": {
                "main": {
                    "type": "processor",
                    "value": 85.5,
                    "unit": "percent"
                }
            }
        },
        "values": [
            {
                "type": "metric",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "metrics_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_threshold",
                "severity": "medium",
                "description": "Missing threshold",
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
            "content": {"content": "Similar metrics"},
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
def metrics_agent(mock_memory_system, mock_world):
    """Create a MetricsAgent instance with mock dependencies."""
    return MetricsAgent(
        name="TestMetrics",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(metrics_agent):
    """Test agent initialization."""
    assert metrics_agent.name == "TestMetrics"
    assert metrics_agent.domain == "professional"
    assert metrics_agent.agent_type == "metrics"
    
    # Verify attributes were initialized
    attributes = metrics_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify metrics-specific attributes
    assert "Process metrics effectively" in attributes["desires"]
    assert "towards_metrics" in attributes["emotions"]
    assert "metrics_processing" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(metrics_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await metrics_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "metrics_state" in metrics_agent.emotions
    assert "domain_state" in metrics_agent.emotions
    assert any("Track" in desire for desire in metrics_agent.desires)

@pytest.mark.asyncio
async def test_process_and_store(metrics_agent, mock_memory_system):
    """Test metrics processing with domain awareness."""
    content = {
        "text": "Content to process",
        "type": "performance"
    }
    
    result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, MetricsResult)
    assert result.metrics["type"] == "performance"
    assert len(result.metrics["metrics"]) == 1
    assert len(result.values) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(metrics_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(metrics_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await metrics_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await metrics_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_process_with_different_domains(metrics_agent):
    """Test processing with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(metrics_agent, mock_memory_system):
    """Test error handling during processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await metrics_agent.process_and_store(
        {"content": "test"},
        metrics_type="performance"
    )
    
    # Verify error handling
    assert isinstance(result, MetricsResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.values) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(metrics_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["values"] = [
        {
            "type": "test_value",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["values"] = [
        {
            "type": "test_value",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Metrics failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(metrics_agent, mock_memory_system):
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
    
    result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical metrics issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_value_reflection(metrics_agent, mock_memory_system):
    """Test reflection recording for important values."""
    content = {"text": "test"}
    
    # Add important value
    mock_memory_system.llm.analyze.return_value["values"] = [
        {
            "type": "important_value",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical value"
        }
    ]
    
    result = await metrics_agent.process_and_store(
        content,
        metrics_type="performance"
    )
    
    # Verify important value reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important metrics values processed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(metrics_agent):
    """Test emotion updates based on metrics results."""
    content = {"text": "Test content"}
    
    await metrics_agent.process(content)
    
    # Verify emotion updates
    assert "metrics_state" in metrics_agent.emotions
    assert "domain_state" in metrics_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(metrics_agent):
    """Test desire updates based on metrics needs."""
    content = {"text": "Test content"}
    
    await metrics_agent.process(content)
    
    # Verify desire updates
    assert any("Track" in desire for desire in metrics_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
