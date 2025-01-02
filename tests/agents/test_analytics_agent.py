"""Tests for the enhanced AnalyticsAgent implementation."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.analytics_agent import AnalyticsAgent
from src.nia.nova.core.analytics import AnalyticsResult
from src.nia.memory.memory_types import AgentResponse

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
                "analysis1": {
                    "type": "pattern",
                    "value": 0.8,
                    "confidence": 0.9
                }
            },
            "metadata": {
                "source": "test_source"
            }
        },
        "insights": [
            {
                "type": "pattern",
                "description": "Recurring pattern detected",
                "confidence": 0.8,
                "importance": 0.9
            }
        ],
        "issues": []
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
            "content": {"content": "Previous analysis"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    world = MagicMock()
    world.notify_agent = AsyncMock()
    return world

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
    """Test agent initialization with enhanced attributes."""
    assert analytics_agent.name == "TestAnalytics"
    assert analytics_agent.domain == "professional"
    assert analytics_agent.agent_type == "analytics"
    
    # Verify enhanced attributes
    attributes = analytics_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Analytics Manager"
    assert "Analyze data efficiently" in attributes["desires"]
    assert "towards_analysis" in attributes["emotions"]
    assert "analysis_optimization" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(analytics_agent.active_analyses, dict)
    assert isinstance(analytics_agent.analysis_strategies, dict)
    assert isinstance(analytics_agent.pattern_templates, dict)
    assert isinstance(analytics_agent.insight_models, dict)
    assert isinstance(analytics_agent.trend_detectors, dict)

@pytest.mark.asyncio
async def test_process_with_analysis_tracking(analytics_agent, mock_memory_system):
    """Test content processing with analysis state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "analytics_result",
                "description": "successful"
            },
            {
                "type": "analysis_state",
                "state": "optimal"
            },
            {
                "type": "pattern_state",
                "state": "detected"
            },
            {
                "type": "insight_state",
                "state": "generated"
            }
        ]
    }
    
    content = {
        "analysis_id": "analysis1",
        "analysis_type": "pattern",
        "analysis_data": np.array([[1, 2], [3, 4]]),
        "analysis_metadata": {"source": "test_source"},
        "analysis_patterns": {
            "pattern1": {"priority": 0.9}
        }
    }
    
    response = await analytics_agent.process(content)
    
    # Verify analysis state tracking
    assert "analysis1" in analytics_agent.active_analyses
    analysis_state = analytics_agent.active_analyses["analysis1"]
    assert analysis_state["type"] == "pattern"
    assert analysis_state["metadata"]["source"] == "test_source"
    assert len(analysis_state["history"]) == 1
    assert analysis_state["needs_attention"] is True
    
    # Verify emotional updates
    assert analytics_agent.emotions["analysis_state"] == "optimal"
    assert analytics_agent.emotions["pattern_state"] == "detected"
    assert analytics_agent.emotions["insight_state"] == "generated"

@pytest.mark.asyncio
async def test_analysis_strategy_management(analytics_agent):
    """Test analysis strategy management."""
    # Set up test strategy
    strategies = {
        "strategy1": {
            "type": "statistical",
            "method": "regression",
            "parameters": {"alpha": 0.05},
            "needs_optimization": True,
            "metadata": {"source": "test_source"}
        }
    }
    
    analytics_agent._update_analysis_strategies(strategies)
    
    # Verify strategy tracking
    assert "strategy1" in analytics_agent.analysis_strategies
    strategy_state = analytics_agent.analysis_strategies["strategy1"]
    assert strategy_state["type"] == "statistical"
    assert strategy_state["method"] == "regression"
    assert strategy_state["parameters"]["alpha"] == 0.05
    assert strategy_state["needs_optimization"] is True
    assert strategy_state["metadata"]["source"] == "test_source"

@pytest.mark.asyncio
async def test_pattern_template_management(analytics_agent):
    """Test pattern template management."""
    templates = {
        "template1": {
            "type": "static",
            "pattern": ".*trend.*",
            "recognition": {
                "pattern": r"\d+\s*%\s*increase"
            },
            "needs_tuning": True,
            "metadata": {"confidence": 0.8}
        }
    }
    
    analytics_agent._update_pattern_templates(templates)
    
    # Verify template tracking
    assert "template1" in analytics_agent.pattern_templates
    template_state = analytics_agent.pattern_templates["template1"]
    assert template_state["type"] == "static"
    assert template_state["pattern"] == ".*trend.*"
    assert template_state["recognition"]["pattern"] == r"\d+\s*%\s*increase"
    assert template_state["needs_tuning"] is True
    assert template_state["metadata"]["confidence"] == 0.8

@pytest.mark.asyncio
async def test_insight_model_management(analytics_agent):
    """Test insight model management."""
    models = {
        "model1": {
            "type": "static",
            "algorithm": "clustering",
            "parameters": {
                "n_clusters": 3,
                "required_fields": ["data"]
            },
            "needs_update": True,
            "metadata": {"description": "Cluster analysis"}
        }
    }
    
    analytics_agent._update_insight_models(models)
    
    # Verify model tracking
    assert "model1" in analytics_agent.insight_models
    model_state = analytics_agent.insight_models["model1"]
    assert model_state["type"] == "static"
    assert model_state["algorithm"] == "clustering"
    assert model_state["parameters"]["n_clusters"] == 3
    assert model_state["needs_update"] is True
    assert model_state["metadata"]["description"] == "Cluster analysis"

@pytest.mark.asyncio
async def test_trend_detector_management(analytics_agent):
    """Test trend detector management."""
    detectors = {
        "detector1": {
            "type": "time",
            "window": "1d",
            "algorithm": "exponential_smoothing",
            "needs_review": True,
            "metadata": {"confidence": 0.9}
        }
    }
    
    analytics_agent._update_trend_detectors(detectors)
    
    # Verify detector tracking
    assert "detector1" in analytics_agent.trend_detectors
    detector_state = analytics_agent.trend_detectors["detector1"]
    assert detector_state["type"] == "time"
    assert detector_state["window"] == "1d"
    assert detector_state["algorithm"] == "exponential_smoothing"
    assert detector_state["needs_review"] is True
    assert detector_state["metadata"]["confidence"] == 0.9

@pytest.mark.asyncio
async def test_process_and_store_with_enhancements(analytics_agent, mock_memory_system):
    """Test enhanced analytics processing and storage."""
    # Create test data
    data = pd.DataFrame({
        "timestamp": pd.date_range(start="2024-01-01", periods=10, freq="H"),
        "value": np.random.randn(10)
    })
    
    content = {
        "analysis_id": "analysis1",
        "analysis_type": "time_series",
        "analysis_data": data.to_dict(),
        "analysis_strategies": {
            "strategy1": {
                "type": "statistical",
                "method": "regression"
            }
        },
        "pattern_templates": {
            "template1": {
                "type": "static",
                "pattern": ".*trend.*"
            }
        }
    }
    
    result = await analytics_agent.process_and_store(content, "behavioral")
    
    # Verify analytics result
    assert isinstance(result, AnalyticsResult)
    assert result.is_valid is True
    
    # Verify analysis tracking
    assert "analysis1" in analytics_agent.active_analyses
    assert analytics_agent.active_analyses["analysis1"]["type"] == "time_series"
    
    # Verify rule tracking
    assert "strategy1" in analytics_agent.analysis_strategies
    assert "template1" in analytics_agent.pattern_templates
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence analytics completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_pattern_template_application(analytics_agent, mock_memory_system):
    """Test pattern template application and reflection."""
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "pattern": ".*trend.*",
            "recognition": {
                "pattern": r"\d+\s*%\s*increase"
            },
            "needs_tuning": True
        }
    }
    
    analytics_agent._update_pattern_templates(templates)
    
    # Apply template to analysis
    content = {
        "analysis_id": "analysis1",
        "data": "Found 25% increase in trend"
    }
    
    await analytics_agent._update_analysis_state("analysis1", content)
    
    # Verify template application
    analysis_state = analytics_agent.active_analyses["analysis1"]
    assert "template1" in analysis_state["patterns"]
    assert analysis_state["patterns"]["template1"]["matches"] == ["25% increase"]
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Pattern template template1 applied to analysis1 needs tuning",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_insight_model_application(analytics_agent, mock_memory_system):
    """Test insight model application and reflection."""
    # Set up test model
    models = {
        "model1": {
            "type": "static",
            "algorithm": "clustering",
            "parameters": {
                "n_clusters": 3,
                "required_fields": ["data"]
            },
            "needs_update": True
        }
    }
    
    analytics_agent._update_insight_models(models)
    
    # Apply model to analysis
    content = {
        "analysis_id": "analysis1",
        "data": np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    }
    
    await analytics_agent._update_analysis_state("analysis1", content)
    
    # Verify model application
    analysis_state = analytics_agent.active_analyses["analysis1"]
    assert "model1" in analysis_state["insights"]
    assert "clusters" in analysis_state["insights"]["model1"]
    assert "silhouette" in analysis_state["insights"]["model1"]
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Insight model model1 applied to analysis1 needs update",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_trend_detector_application(analytics_agent, mock_memory_system):
    """Test trend detector application and reflection."""
    # Set up test detector
    detectors = {
        "detector1": {
            "type": "time",
            "window": "2h",
            "algorithm": "moving_average",
            "needs_review": True
        }
    }
    
    analytics_agent._update_trend_detectors(detectors)
    
    # Apply detector to analysis
    data = pd.DataFrame({
        "timestamp": pd.date_range(start="2024-01-01", periods=10, freq="H"),
        "value": np.random.randn(10)
    })
    
    content = {
        "analysis_id": "analysis1",
        "data": data
    }
    
    await analytics_agent._update_analysis_state("analysis1", content)
    
    # Verify detector application
    analysis_state = analytics_agent.active_analyses["analysis1"]
    assert "detector1" in analysis_state["trends"]
    assert "moving_average" in analysis_state["trends"]["detector1"]
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Trend detector detector1 applied to analysis1 needs review",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(analytics_agent, mock_memory_system):
    """Test error handling during analytics processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await analytics_agent.process_and_store({"type": "test"}, "behavioral")
    
    # Verify error handling
    assert isinstance(result, AnalyticsResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Analytics failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(analytics_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await analytics_agent.process_and_store(
        {"type": "test"},
        "behavioral",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await analytics_agent.process_and_store(
            {"type": "test"},
            "behavioral",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
