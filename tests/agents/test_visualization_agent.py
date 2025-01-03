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
def visualization_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a VisualizationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestVisualization_{request.node.name}"
    
    # Update mock memory system for visualization agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
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
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return VisualizationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(visualization_agent, mock_memory_system):
    """Test agent initialization with enhanced attributes."""
    # Configure mock LLM response with detailed initialization results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "initialization_state": {
            "status": "completed",
            "confidence": 0.95,
            "metrics": {
                "setup_quality": 0.93,
                "attribute_completeness": 0.94,
                "capability_readiness": 0.92
            }
        },
        "attribute_validation": {
            "occupation": {
                "value": "Advanced Visualization Manager",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Visualize data efficiently",
                "secondary": ["Optimize rendering", "Maintain quality"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_data": "analytical",
                "towards_quality": "focused",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "data_visualization",
                "supporting": ["rendering", "optimization"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "active_visualizations": {"status": "ready", "confidence": 0.95},
                "visualization_strategies": {"status": "ready", "confidence": 0.94},
                "layout_templates": {"status": "ready", "confidence": 0.93},
                "chart_templates": {"status": "ready", "confidence": 0.92},
                "rendering_engines": {"status": "ready", "confidence": 0.91}
            }
        }
    })
    
    # Verify basic attributes
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
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "State tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_with_visualization_tracking(visualization_agent, mock_memory_system):
    """Test content processing with visualization state tracking."""
    # Configure mock LLM response with detailed processing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "visualization_state": {
            "status": "active",
            "confidence": 0.95,
            "metrics": {
                "data_quality": 0.92,
                "visual_clarity": 0.94,
                "responsiveness": 0.91,
                "performance": 0.93
            }
        },
        "processing_states": {
            "data_state": {
                "status": "processed",
                "metrics": {
                    "completeness": 0.93,
                    "accuracy": 0.95,
                    "consistency": 0.92,
                    "validation": 0.94
                }
            },
            "layout_state": {
                "status": "optimized",
                "metrics": {
                    "efficiency": 0.94,
                    "balance": 0.92,
                    "readability": 0.95,
                    "adaptability": 0.91
                }
            },
            "chart_state": {
                "status": "rendered",
                "metrics": {
                    "performance": 0.93,
                    "interactivity": 0.91,
                    "accessibility": 0.94,
                    "responsiveness": 0.92
                }
            }
        },
        "quality_analysis": {
            "overall_score": 0.93,
            "areas_of_excellence": [
                "data_representation",
                "visual_hierarchy",
                "layout_optimization"
            ],
            "areas_for_improvement": [
                "animation_smoothness",
                "interaction_feedback"
            ],
            "impact_assessment": {
                "user_experience": 0.92,
                "performance_impact": 0.94,
                "resource_utilization": 0.91
            }
        },
        "processing_metrics": {
            "execution_time": 0.15,
            "memory_usage": 0.45,
            "optimization_level": 0.92,
            "resource_efficiency": 0.93
        }
    })
    
    content = {
        "visualization_id": "visual1",
        "visualization_type": "line",
        "visualization_data": {"x": [1, 2, 3], "y": [4, 5, 6]},
        "visualization_metadata": {
            "source": "test_source",
            "importance": "high",
            "impact": "significant",
            "quality_requirements": {
                "performance": "critical",
                "accessibility": "high",
                "responsiveness": "essential"
            }
        },
        "visualization_rendering": {
            "engine1": {
                "priority": 0.9,
                "optimization_level": "high",
                "performance_targets": {
                    "fps": 60,
                    "latency": "low",
                    "memory_footprint": "optimized"
                }
            }
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
    
    # Verify state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Active visualization state established in professional domain",
        domain="professional"
    )
    
    # Verify data quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong data quality achieved in visualization in professional domain",
        domain="professional"
    )
    
    # Verify layout reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Optimal layout efficiency demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify rendering reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High performance rendering achieved in professional domain",
        domain="professional"
    )
    
    # Verify accessibility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong accessibility standards maintained in professional domain",
        domain="professional"
    )
    
    # Verify responsiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Essential responsiveness requirements met in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization optimization opportunities identified in professional domain",
        domain="professional"
    )
    
    # Verify interaction reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Interaction feedback enhancement needed in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant user experience impact achieved in professional domain",
        domain="professional"
    )
    
    # Verify resource reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Efficient resource utilization confirmed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_visualization_strategy_management(visualization_agent, mock_memory_system):
    """Test visualization strategy management."""
    # Configure mock LLM response with detailed strategy results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "strategy_analysis": {
            "status": "active",
            "confidence": 0.95,
            "metrics": {
                "effectiveness": 0.92,
                "adaptability": 0.94,
                "performance": 0.91
            }
        },
        "optimization_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["responsiveness", "adaptability"],
            "areas_for_improvement": ["performance_tuning"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test strategy with detailed configuration
    strategies = {
        "strategy1": {
            "type": "dynamic",
            "method": "responsive",
            "parameters": {
                "breakpoint": 768,
                "transition_duration": 300,
                "animation_easing": "ease-in-out"
            },
            "needs_optimization": True,
            "metadata": {
                "source": "test_source",
                "confidence": 0.9,
                "importance": "high",
                "impact": "significant"
            },
            "performance_metrics": {
                "response_time": 0.15,
                "memory_usage": 0.45,
                "cpu_utilization": 0.35
            },
            "quality_indicators": {
                "visual_consistency": 0.92,
                "user_experience": 0.89,
                "accessibility": 0.94
            }
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
    
    # Verify strategy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization strategy activated in professional domain",
        domain="professional"
    )
    
    # Verify effectiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong strategy effectiveness demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify adaptability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High strategy adaptability confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strategy optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify performance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Performance tuning enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term strategy impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_layout_template_management(visualization_agent, mock_memory_system):
    """Test layout template management."""
    # Configure mock LLM response with detailed template results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "template_analysis": {
            "status": "active",
            "confidence": 0.95,
            "metrics": {
                "flexibility": 0.92,
                "reusability": 0.94,
                "maintainability": 0.91
            }
        },
        "tuning_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["grid_system", "component_organization"],
            "areas_for_improvement": ["responsive_behavior"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test template with detailed configuration
    templates = {
        "template1": {
            "type": "static",
            "layout": "grid",
            "composition": {
                "required_elements": ["header", "main", "footer"],
                "optional_elements": ["sidebar", "overlay"],
                "spacing": {
                    "gap": 20,
                    "margin": 16,
                    "padding": 24
                }
            },
            "needs_tuning": True,
            "metadata": {
                "columns": 12,
                "confidence": 0.9,
                "importance": "high",
                "impact": "significant"
            },
            "performance_metrics": {
                "render_time": 0.15,
                "reflow_count": 2,
                "paint_time": 0.08
            },
            "quality_indicators": {
                "layout_consistency": 0.92,
                "visual_hierarchy": 0.89,
                "accessibility": 0.94
            }
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
    
    # Verify template reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Layout template activated in professional domain",
        domain="professional"
    )
    
    # Verify flexibility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong template flexibility demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify reusability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High template reusability confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Template optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify responsiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Responsive behavior enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term template impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_chart_template_management(visualization_agent, mock_memory_system):
    """Test chart template management."""
    # Configure mock LLM response with detailed template results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "template_analysis": {
            "status": "active",
            "confidence": 0.95,
            "metrics": {
                "versatility": 0.92,
                "customization": 0.94,
                "scalability": 0.91
            }
        },
        "update_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["data_visualization", "style_consistency"],
            "areas_for_improvement": ["animation_transitions"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test template with detailed configuration
    templates = {
        "template1": {
            "type": "static",
            "chart": "line",
            "style": {
                "color": "blue",
                "lineWidth": 2,
                "markers": {
                    "type": "circle",
                    "size": 6,
                    "fill": true
                },
                "animation": {
                    "duration": 300,
                    "easing": "ease-in-out"
                }
            },
            "needs_update": True,
            "metadata": {
                "description": "Time series",
                "confidence": 0.9,
                "importance": "high",
                "impact": "significant"
            },
            "performance_metrics": {
                "render_time": 0.15,
                "update_time": 0.08,
                "memory_usage": 0.45
            },
            "quality_indicators": {
                "visual_clarity": 0.92,
                "data_density": 0.89,
                "interactivity": 0.94
            }
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
    
    # Verify template reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Chart template activated in professional domain",
        domain="professional"
    )
    
    # Verify versatility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong template versatility demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify customization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High template customization confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Template optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify animation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Animation transitions enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term template impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_rendering_engine_management(visualization_agent, mock_memory_system):
    """Test rendering engine management."""
    # Configure mock LLM response with detailed engine results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "engine_analysis": {
            "status": "active",
            "confidence": 0.95,
            "metrics": {
                "performance": 0.92,
                "compatibility": 0.94,
                "stability": 0.91
            }
        },
        "review_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["rendering_quality", "hardware_acceleration"],
            "areas_for_improvement": ["memory_management"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test engine with detailed configuration
    engines = {
        "engine1": {
            "type": "webgl",
            "engine": "three.js",
            "optimization": {
                "antialias": True,
                "precision": "highp",
                "shadows": {
                    "enabled": True,
                    "type": "PCFSoft",
                    "resolution": 2048
                },
                "postProcessing": {
                    "enabled": True,
                    "effects": ["FXAA", "bloom"]
                }
            },
            "needs_review": True,
            "metadata": {
                "version": "r128",
                "confidence": 0.9,
                "importance": "high",
                "impact": "significant"
            },
            "performance_metrics": {
                "fps": 60,
                "drawCalls": 500,
                "triangles": 100000,
                "memory_usage": 0.45
            },
            "quality_indicators": {
                "visual_fidelity": 0.92,
                "frame_consistency": 0.89,
                "resource_efficiency": 0.94
            }
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
    
    # Verify engine reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Rendering engine activated in professional domain",
        domain="professional"
    )
    
    # Verify performance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong engine performance demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify compatibility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High engine compatibility confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Engine optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify memory reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Memory management enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term engine impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_and_store_with_enhancements(visualization_agent, mock_memory_system):
    """Test enhanced visualization processing and storage."""
    # Configure mock LLM response with detailed processing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "visualization": {
            "type": "chart",
            "visualization": {
                "visual1": {
                    "type": "line",
                    "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
                    "style": {"color": "blue"}
                }
            },
            "quality_metrics": {
                "clarity": 0.92,
                "accuracy": 0.94,
                "effectiveness": 0.91
            }
        },
        "elements": [
            {
                "type": "axis",
                "description": "X-axis configuration",
                "confidence": 0.9,
                "importance": 0.8,
                "metrics": {
                    "readability": 0.93,
                    "alignment": 0.92,
                    "spacing": 0.94
                }
            }
        ],
        "processing_metrics": {
            "performance": 0.93,
            "memory_usage": 0.45,
            "optimization_level": 0.92
        },
        "quality_analysis": {
            "overall_score": 0.93,
            "strengths": [
                "data_representation",
                "visual_hierarchy"
            ],
            "improvement_areas": [
                "interactivity"
            ]
        },
        "issues": []
    })
    
    content = {
        "visualization_id": "visual1",
        "visualization_type": "line",
        "visualization_data": {"x": [1, 2, 3], "y": [4, 5, 6]},
        "visualization_strategies": {
            "strategy1": {
                "type": "dynamic",
                "method": "responsive",
                "confidence": 0.9,
                "importance": "high"
            }
        },
        "layout_templates": {
            "template1": {
                "type": "static",
                "layout": "grid",
                "quality": "high",
                "impact": "significant"
            }
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "medium"
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
    
    # Verify success reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence visualization completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong visualization quality achieved in professional domain",
        domain="professional"
    )
    
    # Verify clarity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High visual clarity demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify effectiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong visualization effectiveness confirmed in professional domain",
        domain="professional"
    )
    
    # Verify performance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Optimal visualization performance maintained in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization interactivity enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_layout_template_application(visualization_agent, mock_memory_system):
    """Test layout template application and reflection."""
    # Set up test template with detailed configuration
    templates = {
        "template1": {
            "type": "static",
            "layout": "grid",
            "composition": {
                "required_elements": ["header", "main"],
                "optional_elements": ["sidebar", "footer"],
                "spacing": {"gap": 20, "margin": 16}
            },
            "needs_tuning": True,
            "metadata": {
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": "high",
                "impact": "significant",
                "responsiveness": "critical"
            }
        }
    }
    
    visualization_agent._update_layout_templates(templates)
    
    # Apply template to visualization with detailed content
    content = {
        "visualization_id": "visual1",
        "visualization_layout": {
            "header": {"height": 60, "sticky": True},
            "main": {"height": 400, "columns": 12},
            "sidebar": {"width": 240, "visible": True}
        },
        "metadata": {
            "source": "test_service",
            "confidence": 0.9
        }
    }
    
    await visualization_agent._update_visualization_state("visual1", content)
    
    # Verify template application
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert "header" in visualization_state["layout"]
    assert "main" in visualization_state["layout"]
    assert "sidebar" in visualization_state["layout"]
    assert visualization_state["layout"]["header"]["sticky"] is True
    assert visualization_state["layout"]["main"]["columns"] == 12
    
    # Verify application reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Layout template template1 applied to visual1 needs tuning in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence layout template results in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant layout impact identified in professional domain",
        domain="professional"
    )
    
    # Verify responsiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Layout responsiveness requires monitoring in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_chart_template_application(visualization_agent, mock_memory_system):
    """Test chart template application and reflection."""
    # Set up test template with detailed configuration
    templates = {
        "template1": {
            "type": "static",
            "chart": "line",
            "style": {
                "color": "blue",
                "lineWidth": 2,
                "markers": "circle",
                "grid": true
            },
            "needs_update": True,
            "metadata": {
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": "high",
                "impact": "significant",
                "complexity": "medium"
            }
        }
    }
    
    visualization_agent._update_chart_templates(templates)
    
    # Apply template to visualization with detailed content
    content = {
        "visualization_id": "visual1",
        "visualization_type": "line",
        "metadata": {
            "source": "test_service",
            "confidence": 0.9
        }
    }
    
    await visualization_agent._update_visualization_state("visual1", content)
    
    # Verify template application
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert visualization_state["chart"].get("color") == "blue"
    assert visualization_state["chart"].get("lineWidth") == 2
    assert visualization_state["chart"].get("markers") == "circle"
    assert visualization_state["chart"].get("grid") is True
    
    # Verify application reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Chart template template1 applied to visual1 needs update in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence chart template results in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant chart impact identified in professional domain",
        domain="professional"
    )
    
    # Verify update reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Chart template requires optimization in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_rendering_engine_application(visualization_agent, mock_memory_system):
    """Test rendering engine application and reflection."""
    # Set up test engine with detailed configuration
    engines = {
        "engine1": {
            "type": "webgl",
            "engine": "three.js",
            "optimization": {
                "antialias": True,
                "precision": "highp",
                "shadows": True,
                "postProcessing": True
            },
            "needs_review": True,
            "metadata": {
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": "high",
                "impact": "significant",
                "performance": "critical"
            }
        }
    }
    
    visualization_agent._update_rendering_engines(engines)
    
    # Apply engine to visualization with detailed content
    content = {
        "visualization_id": "visual1",
        "visualization_rendering": {
            "type": "webgl",
            "requirements": ["shadows", "postProcessing"]
        },
        "metadata": {
            "source": "test_service",
            "confidence": 0.9
        }
    }
    
    await visualization_agent._update_visualization_state("visual1", content)
    
    # Verify engine application
    visualization_state = visualization_agent.active_visualizations["visual1"]
    assert visualization_state["rendering"].get("antialias") is True
    assert visualization_state["rendering"].get("precision") == "highp"
    assert visualization_state["rendering"].get("shadows") is True
    assert visualization_state["rendering"].get("postProcessing") is True
    
    # Verify application reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Rendering engine engine1 applied to visual1 needs review in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence rendering engine results in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant rendering impact identified in professional domain",
        domain="professional"
    )
    
    # Verify performance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Rendering performance requires monitoring in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(visualization_agent, mock_memory_system):
    """Test error handling during visualization processing."""
    content = {
        "visualization_id": "visual1",
        "visualization_type": "chart",
        "visualization_data": {
            "type": "line",
            "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
            "style": {"color": "blue"}
        },
        "metadata": {
            "importance": "high",
            "impact": "critical",
            "urgency": "immediate"
        }
    }
    
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await visualization_agent.process_and_store(content, "chart")
    
    # Verify error handling
    assert isinstance(result, VisualizationResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    assert result.metadata["error_type"] == "visualization_failure"
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization needs retry with adjusted parameters in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Visualization error impacts data quality in professional domain",
        domain="professional"
    )
    
    # Verify rendering reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Rendering state needs verification in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(visualization_agent, mock_memory_system):
    """Test domain access validation."""
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Configure mock LLM response with detailed domain validation results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "visualization": {
            "type": "chart",
            "visualization": {
                "visual1": {
                    "type": "line",
                    "data": {"x": [1, 2, 3], "y": [4, 5, 6]}
                }
            }
        },
        "domain_validation": {
            "access_level": "full",
            "confidence": 0.95,
            "validation_metrics": {
                "permission_strength": 0.92,
                "access_scope": 0.94,
                "security_level": 0.91
            }
        },
        "security_analysis": {
            "overall_score": 0.93,
            "compliance_level": "high",
            "risk_assessment": {
                "level": "low",
                "factors": ["validated_access", "proper_scope"]
            }
        },
        "access_metrics": {
            "validation_time": 0.15,
            "permission_depth": 0.92,
            "scope_coverage": 0.94
        }
    })
    
    # Test allowed domain
    content = {
        "type": "test",
        "metadata": {
            "importance": "high",
            "security_level": "standard",
            "access_requirements": "validated"
        }
    }
    
    result = await visualization_agent.process_and_store(
        content,
        "chart",
        target_domain="professional"
    )
    assert result.is_valid is True
    
    # Verify domain validation reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain access validated successfully in professional domain",
        domain="professional"
    )
    
    # Verify security reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High security compliance confirmed in professional domain",
        domain="professional"
    )
    
    # Verify permission reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong permission validation achieved in professional domain",
        domain="professional"
    )
    
    # Verify scope reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Full access scope verified in professional domain",
        domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_validation": {
            "access_level": "none",
            "confidence": 0.95,
            "validation_metrics": {
                "permission_strength": 0.0,
                "access_scope": 0.0,
                "security_level": 0.92
            }
        },
        "security_analysis": {
            "overall_score": 0.93,
            "compliance_level": "high",
            "risk_assessment": {
                "level": "high",
                "factors": ["unauthorized_access", "scope_violation"]
            }
        }
    })
    
    with pytest.raises(PermissionError):
        await visualization_agent.process_and_store(
            content,
            "chart",
            target_domain="restricted"
        )
    
    # Verify access denial reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain access denied for restricted domain",
        domain="professional"
    )
    
    # Verify security violation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Security compliance enforced for unauthorized access attempt",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
