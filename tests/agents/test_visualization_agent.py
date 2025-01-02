"""Tests for the specialized VisualizationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.visualization_agent import VisualizationAgent
from src.nia.nova.core.visualization import VisualizationResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "visualization": {
            "type": "chart",
            "visualization": {
                "main": {
                    "type": "bar",
                    "data": {"values": [1, 2, 3]},
                    "style": {"color": "blue"}
                }
            }
        },
        "elements": [
            {
                "type": "chart",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "visualization_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_legend",
                "severity": "medium",
                "description": "Missing legend",
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
            "content": {"content": "Similar visualization"},
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
def visualization_agent(mock_memory_system, mock_world):
    """Create a VisualizationAgent instance with mock dependencies."""
    return VisualizationAgent(
        name="TestVisualization",
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(visualization_agent):
    """Test agent initialization."""
    assert visualization_agent.name == "TestVisualization"
    assert visualization_agent.domain == "professional"
    assert visualization_agent.agent_type == "visualization"
    
    # Verify attributes were initialized
    attributes = visualization_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify visualization-specific attributes
    assert "Process visualizations effectively" in attributes["desires"]
    assert "towards_visualization" in attributes["emotions"]
    assert "visualization_processing" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(visualization_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await visualization_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "visualization_state" in visualization_agent.emotions
    assert "domain_state" in visualization_agent.emotions
    assert any("Visualize" in desire for desire in visualization_agent.desires)

@pytest.mark.asyncio
async def test_process_and_store(visualization_agent, mock_memory_system):
    """Test visualization processing with domain awareness."""
    content = {
        "text": "Content to process",
        "type": "chart"
    }
    
    result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, VisualizationResult)
    assert result.visualization["type"] == "chart"
    assert len(result.visualization["visualization"]) == 1
    assert len(result.elements) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(visualization_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(visualization_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await visualization_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await visualization_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_process_with_different_domains(visualization_agent):
    """Test processing with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(visualization_agent, mock_memory_system):
    """Test error handling during processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await visualization_agent.process_and_store(
        {"content": "test"},
        visualization_type="chart"
    )
    
    # Verify error handling
    assert isinstance(result, VisualizationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.elements) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(visualization_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Force valid result with high confidence
    mock_memory_system.llm.analyze.return_value["elements"] = [
        {
            "type": "test_element",
            "confidence": 0.9,
            "importance": 0.9
        }
    ]
    mock_memory_system.llm.analyze.return_value["issues"] = []
    
    result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart"
    )
    
    # Verify high confidence reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("High confidence" in str(call) for call in reflection_calls)
    
    # Test invalid result
    mock_memory_system.llm.analyze.return_value["elements"] = [
        {
            "type": "test_element",
            "confidence": 0.5,
            "importance": 0.5
        }
    ]
    
    result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Visualization failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(visualization_agent, mock_memory_system):
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
    
    result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical visualization issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_element_reflection(visualization_agent, mock_memory_system):
    """Test reflection recording for important elements."""
    content = {"text": "test"}
    
    # Add important element
    mock_memory_system.llm.analyze.return_value["elements"] = [
        {
            "type": "important_element",
            "confidence": 0.9,
            "importance": 0.9,
            "description": "Critical element"
        }
    ]
    
    result = await visualization_agent.process_and_store(
        content,
        visualization_type="chart"
    )
    
    # Verify important element reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important visualization elements created" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(visualization_agent):
    """Test emotion updates based on visualization results."""
    content = {"text": "Test content"}
    
    await visualization_agent.process(content)
    
    # Verify emotion updates
    assert "visualization_state" in visualization_agent.emotions
    assert "domain_state" in visualization_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(visualization_agent):
    """Test desire updates based on visualization needs."""
    content = {"text": "Test content"}
    
    await visualization_agent.process(content)
    
    # Verify desire updates
    assert any("Visualize" in desire for desire in visualization_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
