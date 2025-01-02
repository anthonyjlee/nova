"""Tests for the specialized AnalyticsAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.analytics_agent import AnalyticsAgent
from src.nia.nova.core.analytics import AnalyticsResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "analytics": {
            "type": "behavioral",
            "analytics": {
                "main": {
                    "type": "pattern",
                    "value": 85.5,
                    "confidence": 0.8
                }
            }
        },
        "insights": [
            {
                "type": "pattern",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "analytics_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_pattern",
                "severity": "medium",
                "description": "Missing pattern",
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
            "content": {"content": "Similar analytics"},
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
def analytics_agent(mock_memory_system, mock_world):
    """Create an AnalyticsAgent instance with mock dependencies."""
    return AnalyticsAgent(
        name="TestAnalytics",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(analytics_agent):
    """Test agent initialization."""
    assert analytics_agent.name == "TestAnalytics"
    assert analytics_agent.domain == "professional"
    assert analytics_agent.agent_type == "analytics"
    
    # Verify attributes were initialized
    attributes = analytics_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify analytics-specific attributes
    assert "Process analytics effectively" in attributes["desires"]
    assert "towards_analytics" in attributes["emotions"]
    assert "analytics_processing" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(analytics_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await analytics_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analytics_state" in analytics_agent.emotions
    assert "domain_state" in analytics_agent.emotions
    assert any("Analyze" in desire for desire in analytics_agent.desires)

@pytest.mark.asyncio
async def test_process_and_store(analytics_agent, mock_memory_system):
    """Test analytics processing with domain awareness."""
    content = {
        "text": "Content to process",
        "type": "behavioral"
    }
    
    result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, AnalyticsResult)
    assert result.analytics["type"] == "behavioral"
    assert len(result.analytics["analytics"]) == 1
    assert len(result.insights) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(analytics_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(analytics_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await analytics_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await analytics_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_process_with_different_domains(analytics_agent):
    """Test processing with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(analytics_agent, mock_memory_system):
    """Test error handling during processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await analytics_agent.process_and_store(
        {"content": "test"},
        analytics_type="behavioral"
    )
    
    # Verify error handling
    assert isinstance(result, AnalyticsResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(analytics_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["insights"] = [
        {
            "type": "test_insight",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["insights"] = [
        {
            "type": "test_insight",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Analytics failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(analytics_agent, mock_memory_system):
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
    
    result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical analytics issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_insight_reflection(analytics_agent, mock_memory_system):
    """Test reflection recording for important insights."""
    content = {"text": "test"}
    
    # Add important insight
    mock_memory_system.llm.analyze.return_value["insights"] = [
        {
            "type": "important_insight",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical insight"
        }
    ]
    
    result = await analytics_agent.process_and_store(
        content,
        analytics_type="behavioral"
    )
    
    # Verify important insight reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important analytics insights discovered" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(analytics_agent):
    """Test emotion updates based on analytics results."""
    content = {"text": "Test content"}
    
    await analytics_agent.process(content)
    
    # Verify emotion updates
    assert "analytics_state" in analytics_agent.emotions
    assert "domain_state" in analytics_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(analytics_agent):
    """Test desire updates based on analytics needs."""
    content = {"text": "Test content"}
    
    await analytics_agent.process(content)
    
    # Verify desire updates
    assert any("Analyze" in desire for desire in analytics_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
