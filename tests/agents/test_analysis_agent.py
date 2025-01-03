"""Tests for the specialized AnalysisAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.analysis_agent import AnalysisAgent
from src.nia.nova.core.analysis import AnalysisResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "analysis": {
            "type": "text",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content"
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
                "type": "analysis_need",
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
            "content": {"content": "Similar analysis"},
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
def analysis_agent(mock_memory_system, mock_world, request):
    """Create an AnalysisAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestAnalysis_{request.node.name}"
    return AnalysisAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(analysis_agent):
    """Test agent initialization."""
    assert "TestAnalysis" in analysis_agent.name
    assert analysis_agent.domain == "professional"
    assert analysis_agent.agent_type == "analysis"
    
    # Verify attributes were initialized
    attributes = analysis_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify analysis-specific attributes
    assert "Extract meaningful insights" in attributes["desires"]
    assert "towards_content" in attributes["emotions"]
    assert "content_analysis" in attributes["capabilities"]

@pytest.mark.asyncio
async def test_process_content(analysis_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {"text": "Test content"}
    metadata = {"source": "test"}
    
    response = await analysis_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in analysis_agent.emotions
    assert "domain_state" in analysis_agent.emotions
    assert any("Investigate" in desire for desire in analysis_agent.desires)

@pytest.mark.asyncio
async def test_analyze_and_store(analysis_agent, mock_memory_system):
    """Test content analysis with domain awareness."""
    content = {
        "text": "Content to analyze",
        "type": "text"
    }
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, AnalysisResult)
    assert result.analysis["type"] == "text"
    assert len(result.analysis["components"]) == 1
    assert len(result.insights) > 0
    assert len(result.issues) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(analysis_agent, "store_memory")
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called()

@pytest.mark.asyncio
async def test_domain_access_validation(analysis_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await analysis_agent.validate_domain_access("professional")
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await analysis_agent.validate_domain_access("restricted")

@pytest.mark.asyncio
async def test_analyze_with_different_domains(analysis_agent):
    """Test analysis with different domain configurations."""
    content = {"text": "test"}
    
    # Test professional domain
    prof_result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"

@pytest.mark.asyncio
async def test_error_handling(analysis_agent, mock_memory_system):
    """Test error handling during analysis."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await analysis_agent.analyze_and_store(
        {"content": "test"},
        analysis_type="text"
    )
    
    # Verify error handling
    assert isinstance(result, AnalysisResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_reflection_recording(analysis_agent, mock_memory_system):
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
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
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
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify failure reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Analysis failed" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_critical_issue_reflection(analysis_agent, mock_memory_system):
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
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify critical issue reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Critical analysis issues" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_important_insight_reflection(analysis_agent, mock_memory_system):
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
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify important insight reflection
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any("Important insights discovered" in str(call) for call in reflection_calls)

@pytest.mark.asyncio
async def test_emotion_updates(analysis_agent):
    """Test emotion updates based on analysis results."""
    content = {"text": "Test content"}
    
    await analysis_agent.process(content)
    
    # Verify emotion updates
    assert "analysis_state" in analysis_agent.emotions
    assert "domain_state" in analysis_agent.emotions

@pytest.mark.asyncio
async def test_desire_updates(analysis_agent):
    """Test desire updates based on analysis needs."""
    content = {"text": "Test content"}
    
    await analysis_agent.process(content)
    
    # Verify desire updates
    assert any("Investigate" in desire for desire in analysis_agent.desires)

if __name__ == "__main__":
    pytest.main([__file__])
