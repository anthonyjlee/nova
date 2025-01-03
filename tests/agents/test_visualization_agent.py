"""Tests for the enhanced VisualizationAgent implementation."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.visualization_agent import VisualizationAgent
from src.nia.nova.core.visualization import VisualizationResult
from src.nia.memory.memory_types import AgentResponse

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
                "visual1": {
                    "type": "line",
                    "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
                    "style": {"color": "blue"}
                }
            },
            "metadata": {
                "source": "test_source"
            }
        },
        "elements": [
            {
                "type": "axis",
                "description": "X-axis configuration",
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
            "content": {"content": "Previous visualization"},
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
def visualization_agent(mock_memory_system, mock_world, request):
    """Create a VisualizationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestVisualization_{request.node.name}"
    return VisualizationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(visualization_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestVisualization" in visualization_agent.name
    assert visualization_agent.domain == "professional"
    assert visualization_agent.agent_type == "visualization"
    
    # Verify enhanced attributes
    attributes = visualization_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Visualization Manager"
    assert "Visualize data efficiently" in attributes["desires"]
    assert "towards_data" in attributes["emotions"]
    assert "data_visualization" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(visualization_agent.active_visualizations, dict)
    assert isinstance(visualization_agent.visualization_strategies, dict)
    assert isinstance(visualization_agent.layout_templates, dict)
    assert isinstance(visualization_agent.chart_templates, dict)
    assert isinstance(visualization_agent.rendering_engines, dict)

@pytest.mark.asyncio
async def test_process_with_visualization_tracking(visualization_agent, mock_memory_system):
    """Test content processing with visualization state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "visualization_result",
                "description": "successful"
            },
            {
                "type": "data_state",
                "state": "processed"
            },
            {
                "type": "layout_state",
                "state": "optimized"
            },
            {
                "type": "chart_state",
                "state": "rendered"
            }
        ]
    }
    
    content = {
        "visualization_id": "visual1",
        "visualization_type": "line",
        "visualization_data": {"x": [1, 2, 3], "y": [4, 5, 6]},
        "visualization_metadata": {"source": "test_source"},
        "visualization_rendering": {
            "engine1": {"priority": 0.9}
        }
    }
    
    response = await visualization_agent.process(content)
    
    # Verify visualization state tracking
    assert "visual1" in visualization_agent.active_visualizations
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert visualization_state["type"] == "line"
    assert visualization_state["metadata"]["source"] == "test_source"
    assert len(visualization_state["history"]) == 1
    assert visualization_state["needs_attention"] is True
    
    # Verify emotional updates
    assert visualization_agent.emotions["data_state"] == "processed"
    assert visualization_agent.emotions["layout_state"] == "optimized"
    assert visualization_agent.emotions["chart_state"] == "rendered"

@pytest.mark.asyncio
async def test_visualization_strategy_management(visualization_agent):
    """Test visualization strategy management."""
    # Set up test strategy
    strategies = {
        "strategy1": {
            "type": "dynamic",
            "method": "responsive",
            "parameters": {"breakpoint": 768},
            "needs_optimization": True,
            "metadata": {"source": "test_source"}
        }
    }
    
    visualization_agent._update_visualization_strategies(strategies)
    
    # Verify strategy tracking
    assert "strategy1" in visualization_agent.visualization_strategies
    strategy_state = visualization_agent.visualization_strategies["strategy1"]
    assert strategy_state["type"] == "dynamic"
    assert strategy_state["method"] == "responsive"
    assert strategy_state["parameters"]["breakpoint"] == 768
    assert strategy_state["needs_optimization"] is True
    assert strategy_state["metadata"]["source"] == "test_source"

@pytest.mark.asyncio
async def test_layout_template_management(visualization_agent):
    """Test layout template management."""
    templates = {
        "template1": {
            "type": "static",
            "layout": "grid",
            "composition": {
                "required_elements": ["header", "main", "footer"]
            },
            "needs_tuning": True,
            "metadata": {"columns": 12}
        }
    }
    
    visualization_agent._update_layout_templates(templates)
    
    # Verify template tracking
    assert "template1" in visualization_agent.layout_templates
    template_state = visualization_agent.layout_templates["template1"]
    assert template_state["type"] == "static"
    assert template_state["layout"] == "grid"
    assert "header" in template_state["composition"]["required_elements"]
    assert template_state["needs_tuning"] is True
    assert template_state["metadata"]["columns"] == 12

@pytest.mark.asyncio
async def test_chart_template_management(visualization_agent):
    """Test chart template management."""
    templates = {
        "template1": {
            "type": "static",
            "chart": "line",
            "style": {
                "color": "blue",
                "lineWidth": 2
            },
            "needs_update": True,
            "metadata": {"description": "Time series"}
        }
    }
    
    visualization_agent._update_chart_templates(templates)
    
    # Verify template tracking
    assert "template1" in visualization_agent.chart_templates
    template_state = visualization_agent.chart_templates["template1"]
    assert template_state["type"] == "static"
    assert template_state["chart"] == "line"
    assert template_state["style"]["color"] == "blue"
    assert template_state["needs_update"] is True
    assert template_state["metadata"]["description"] == "Time series"

@pytest.mark.asyncio
async def test_rendering_engine_management(visualization_agent):
    """Test rendering engine management."""
    engines = {
        "engine1": {
            "type": "webgl",
            "engine": "three.js",
            "optimization": {
                "antialias": True,
                "precision": "highp"
            },
            "needs_review": True,
            "metadata": {"version": "r128"}
        }
    }
    
    visualization_agent._update_rendering_engines(engines)
    
    # Verify engine tracking
    assert "engine1" in visualization_agent.rendering_engines
    engine_state = visualization_agent.rendering_engines["engine1"]
    assert engine_state["type"] == "webgl"
    assert engine_state["engine"] == "three.js"
    assert engine_state["optimization"]["antialias"] is True
    assert engine_state["needs_review"] is True
    assert engine_state["metadata"]["version"] == "r128"

@pytest.mark.asyncio
async def test_process_and_store_with_enhancements(visualization_agent, mock_memory_system):
    """Test enhanced visualization processing and storage."""
    content = {
        "visualization_id": "visual1",
        "visualization_type": "line",
        "visualization_data": {"x": [1, 2, 3], "y": [4, 5, 6]},
        "visualization_strategies": {
            "strategy1": {
                "type": "dynamic",
                "method": "responsive"
            }
        },
        "layout_templates": {
            "template1": {
                "type": "static",
                "layout": "grid"
            }
        }
    }
    
    result = await visualization_agent.process_and_store(content, "chart")
    
    # Verify visualization result
    assert isinstance(result, VisualizationResult)
    assert result.is_valid is True
    
    # Verify visualization tracking
    assert "visual1" in visualization_agent.active_visualizations
    assert visualization_agent.active_visualizations["visual1"]["type"] == "line"
    
    # Verify rule tracking
    assert "strategy1" in visualization_agent.visualization_strategies
    assert "template1" in visualization_agent.layout_templates
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence visualization completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_layout_template_application(visualization_agent, mock_memory_system):
    """Test layout template application and reflection."""
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "layout": "grid",
            "composition": {
                "required_elements": ["header", "main"]
            },
            "needs_tuning": True
        }
    }
    
    visualization_agent._update_layout_templates(templates)
    
    # Apply template to visualization
    content = {
        "visualization_id": "visual1",
        "visualization_layout": {
            "header": {"height": 60},
            "main": {"height": 400}
        }
    }
    
    await visualization_agent._update_visualization_state("visual1", content)
    
    # Verify template application
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert "header" in visualization_state["layout"]
    assert "main" in visualization_state["layout"]
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Layout template template1 applied to visual1 needs tuning",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_chart_template_application(visualization_agent, mock_memory_system):
    """Test chart template application and reflection."""
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "chart": "line",
            "style": {
                "color": "blue",
                "lineWidth": 2
            },
            "needs_update": True
        }
    }
    
    visualization_agent._update_chart_templates(templates)
    
    # Apply template to visualization
    content = {
        "visualization_id": "visual1",
        "visualization_type": "line"
    }
    
    await visualization_agent._update_visualization_state("visual1", content)
    
    # Verify template application
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert visualization_state["chart"].get("color") == "blue"
    assert visualization_state["chart"].get("lineWidth") == 2
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Chart template template1 applied to visual1 needs update",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_rendering_engine_application(visualization_agent, mock_memory_system):
    """Test rendering engine application and reflection."""
    # Set up test engine
    engines = {
        "engine1": {
            "type": "webgl",
            "engine": "three.js",
            "optimization": {
                "antialias": True,
                "precision": "highp"
            },
            "needs_review": True
        }
    }
    
    visualization_agent._update_rendering_engines(engines)
    
    # Apply engine to visualization
    content = {
        "visualization_id": "visual1",
        "visualization_rendering": {
            "type": "webgl"
        }
    }
    
    await visualization_agent._update_visualization_state("visual1", content)
    
    # Verify engine application
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert visualization_state["rendering"].get("antialias") is True
    assert visualization_state["rendering"].get("precision") == "highp"
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Rendering engine engine1 applied to visual1 needs review",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(visualization_agent, mock_memory_system):
    """Test error handling during visualization processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await visualization_agent.process_and_store({"type": "test"}, "chart")
    
    # Verify error handling
    assert isinstance(result, VisualizationResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Visualization failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(visualization_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await visualization_agent.process_and_store(
        {"type": "test"},
        "chart",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await visualization_agent.process_and_store(
            {"type": "test"},
            "chart",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
