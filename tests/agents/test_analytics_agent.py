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
def analytics_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create an AnalyticsAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestAnalytics_{request.node.name}"
    
    # Update mock memory system for analytics agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
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
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return AnalyticsAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(analytics_agent, mock_memory_system):
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
                "value": "Advanced Analytics Manager",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Analyze data efficiently",
                "secondary": ["Maintain domain boundaries", "Optimize analytics processes"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_analysis": "focused",
                "towards_domain": "aligned",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "analysis_optimization",
                "supporting": ["domain_validation", "pattern_recognition"],
                "confidence": 0.94
            }
        },
        "system_validation": {
            "tracking_systems": {
                "active_analyses": {"status": "ready", "confidence": 0.95},
                "analysis_strategies": {"status": "ready", "confidence": 0.94},
                "pattern_templates": {"status": "ready", "confidence": 0.93},
                "insight_models": {"status": "ready", "confidence": 0.92},
                "trend_detectors": {"status": "ready", "confidence": 0.91}
            }
        },
        "readiness_assessment": {
            "overall_status": "operational",
            "confidence": 0.95,
            "metrics": {
                "system_health": 0.94,
                "initialization_quality": 0.93,
                "operational_readiness": 0.92
            }
        }
    })
    
    # Verify basic attributes
    assert "TestAnalytics" in analytics_agent.name
    assert analytics_agent.domain == "professional"
    assert analytics_agent.agent_type == "analytics"
    
    # Verify enhanced attributes
    attributes = analytics_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Analytics Manager"
    assert "Analyze data efficiently" in attributes["desires"]
    assert "towards_analysis" in attributes["emotions"]
    assert "analysis_optimization" in attributes["capabilities"]
    
    # Verify domain-specific attributes
    assert "Maintain domain boundaries" in attributes["desires"]
    assert "towards_domain" in attributes["emotions"]
    assert "domain_validation" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(analytics_agent.active_analyses, dict)
    assert isinstance(analytics_agent.analysis_strategies, dict)
    assert isinstance(analytics_agent.pattern_templates, dict)
    assert isinstance(analytics_agent.insight_models, dict)
    assert isinstance(analytics_agent.trend_detectors, dict)
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analytics agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analytics capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analytics tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analytics agent ready for operation in professional domain",
        domain="professional"
    )
    
    # Verify system health reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong system health confirmed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High initialization quality achieved in professional domain",
        domain="professional"
    )
    
    # Verify operational reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Operational readiness verified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_with_analysis_tracking(analytics_agent, mock_memory_system):
    """Test content processing with analysis state tracking."""
    # Configure mock LLM response with detailed analysis results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "processing_state": {
            "status": "completed",
            "confidence": 0.95,
            "metrics": {
                "processing_quality": 0.93,
                "analysis_depth": 0.94,
                "tracking_accuracy": 0.92
            }
        },
        "analysis_tracking": {
            "active_analyses": {
                "analysis1": {
                    "type": "pattern",
                    "status": "active",
                    "confidence": 0.91,
                    "metrics": {
                        "pattern_strength": 0.92,
                        "detection_quality": 0.93,
                        "validation_score": 0.94
                    }
                }
            },
            "tracking_metrics": {
                "state_consistency": 0.95,
                "history_completeness": 0.92,
                "attention_accuracy": 0.93
            }
        },
        "emotional_state": {
            "analysis_state": {
                "value": "optimal",
                "confidence": 0.94,
                "stability": 0.92
            },
            "pattern_state": {
                "value": "detected",
                "confidence": 0.93,
                "reliability": 0.91
            },
            "insight_state": {
                "value": "generated",
                "confidence": 0.95,
                "quality": 0.94
            }
        },
        "tracking_assessment": {
            "overall_quality": 0.93,
            "strengths": [
                "state_management",
                "history_tracking"
            ],
            "areas_for_improvement": [
                "attention_mechanism"
            ],
            "metrics": {
                "tracking_efficiency": 0.92,
                "state_reliability": 0.94,
                "history_integrity": 0.93
            }
        }
    })
    
    content = {
        "analysis_id": "analysis1",
        "analysis_type": "pattern",
        "analysis_data": np.array([[1, 2], [3, 4]]),
        "analysis_metadata": {
            "source": "test_source",
            "importance": "high",
            "tracking_requirements": {
                "history_depth": "complete",
                "attention_level": "high",
                "state_persistence": "required"
            }
        },
        "analysis_patterns": {
            "pattern1": {
                "priority": 0.9,
                "confidence": 0.92,
                "validation": {
                    "method": "statistical",
                    "threshold": 0.9
                }
            }
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
    
    # Verify processing reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality processing completed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong state tracking maintained in professional domain",
        domain="professional"
    )
    
    # Verify analysis reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Deep analysis achieved in professional domain",
        domain="professional"
    )
    
    # Verify pattern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence pattern detected in professional domain",
        domain="professional"
    )
    
    # Verify history reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Complete history tracking confirmed in professional domain",
        domain="professional"
    )
    
    # Verify attention reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Attention mechanism needs enhancement in professional domain",
        domain="professional"
    )
    
    # Verify state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Reliable state management demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong tracking efficiency maintained in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analysis_strategy_management(analytics_agent, mock_memory_system):
    """Test analysis strategy management."""
    # Configure mock LLM response with detailed strategy analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "strategy_analysis": {
            "status": "validated",
            "confidence": 0.95,
            "metrics": {
                "strategy_quality": 0.93,
                "optimization_potential": 0.94,
                "implementation_readiness": 0.92
            }
        },
        "strategy_validation": {
            "strategy1": {
                "type": "statistical",
                "confidence": 0.95,
                "metrics": {
                    "method_suitability": 0.92,
                    "parameter_optimization": 0.94,
                    "statistical_power": 0.91
                }
            }
        },
        "optimization_assessment": {
            "current_state": {
                "efficiency": 0.88,
                "accuracy": 0.92,
                "robustness": 0.90
            },
            "improvement_potential": {
                "efficiency_gain": 0.15,
                "accuracy_boost": 0.08,
                "robustness_enhancement": 0.10
            }
        },
        "implementation_metrics": {
            "readiness": 0.93,
            "complexity": 0.85,
            "maintainability": 0.92,
            "scalability": {
                "current": 0.89,
                "potential": 0.95
            }
        }
    })
    
    # Set up test strategy
    strategies = {
        "strategy1": {
            "type": "statistical",
            "method": "regression",
            "parameters": {
                "alpha": 0.05,
                "regularization": "l2",
                "iterations": 1000
            },
            "needs_optimization": True,
            "metadata": {
                "source": "test_source",
                "confidence": 0.92,
                "domain_relevance": 0.94,
                "optimization_priority": "high"
            },
            "validation": {
                "method": "cross_validation",
                "folds": 5,
                "metrics": ["mse", "r2"]
            }
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
    
    # Verify validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strategy validation completed successfully in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High strategy quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strategy optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify suitability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong method suitability demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Efficiency improvement opportunity detected in professional domain",
        domain="professional"
    )
    
    # Verify robustness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Robustness enhancement potential confirmed in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High implementation readiness achieved in professional domain",
        domain="professional"
    )
    
    # Verify scalability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong scalability potential identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_pattern_template_management(analytics_agent, mock_memory_system):
    """Test pattern template management."""
    # Configure mock LLM response with detailed template analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "template_analysis": {
            "status": "validated",
            "confidence": 0.95,
            "metrics": {
                "template_quality": 0.93,
                "recognition_accuracy": 0.94,
                "tuning_potential": 0.92
            }
        },
        "pattern_validation": {
            "template1": {
                "type": "static",
                "confidence": 0.95,
                "metrics": {
                    "pattern_strength": 0.92,
                    "recognition_precision": 0.94,
                    "matching_recall": 0.91
                }
            }
        },
        "tuning_assessment": {
            "current_state": {
                "accuracy": 0.88,
                "coverage": 0.92,
                "specificity": 0.90
            },
            "improvement_potential": {
                "accuracy_gain": 0.12,
                "coverage_boost": 0.08,
                "specificity_enhancement": 0.10
            }
        },
        "implementation_metrics": {
            "readiness": 0.93,
            "complexity": 0.85,
            "maintainability": 0.92,
            "adaptability": {
                "current": 0.89,
                "potential": 0.95
            }
        }
    })
    
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "pattern": ".*trend.*",
            "recognition": {
                "pattern": r"\d+\s*%\s*increase",
                "flags": ["ignorecase", "multiline"],
                "validation": {
                    "min_confidence": 0.8,
                    "max_distance": 0.2
                }
            },
            "needs_tuning": True,
            "metadata": {
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": "high",
                "tuning_priority": "medium"
            },
            "constraints": {
                "max_matches": 5,
                "min_length": 10,
                "context_window": 50
            }
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
    
    # Verify validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Pattern template validation completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High template quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify recognition reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong recognition accuracy achieved in professional domain",
        domain="professional"
    )
    
    # Verify tuning reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Template tuning potential identified in professional domain",
        domain="professional"
    )
    
    # Verify precision reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High recognition precision demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify coverage reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Coverage improvement opportunity detected in professional domain",
        domain="professional"
    )
    
    # Verify adaptability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong adaptability potential confirmed in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High implementation readiness achieved in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_insight_model_management(analytics_agent, mock_memory_system):
    """Test insight model management."""
    # Configure mock LLM response with detailed model analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "model_analysis": {
            "status": "validated",
            "confidence": 0.95,
            "metrics": {
                "model_quality": 0.93,
                "update_potential": 0.94,
                "implementation_readiness": 0.92
            }
        },
        "model_validation": {
            "model1": {
                "type": "static",
                "confidence": 0.95,
                "metrics": {
                    "algorithm_suitability": 0.92,
                    "parameter_optimization": 0.94,
                    "clustering_quality": 0.91
                }
            }
        },
        "update_assessment": {
            "current_state": {
                "accuracy": 0.88,
                "stability": 0.92,
                "robustness": 0.90
            },
            "improvement_potential": {
                "accuracy_gain": 0.12,
                "stability_boost": 0.08,
                "robustness_enhancement": 0.10
            }
        },
        "implementation_metrics": {
            "readiness": 0.93,
            "complexity": 0.85,
            "maintainability": 0.92,
            "adaptability": {
                "current": 0.89,
                "potential": 0.95
            }
        }
    })
    
    # Set up test model
    models = {
        "model1": {
            "type": "static",
            "algorithm": "clustering",
            "parameters": {
                "n_clusters": 3,
                "required_fields": ["data"],
                "initialization": "k-means++",
                "max_iterations": 1000,
                "convergence_threshold": 0.001
            },
            "needs_update": True,
            "metadata": {
                "description": "Cluster analysis",
                "confidence": 0.92,
                "domain_relevance": 0.94,
                "update_priority": "high"
            },
            "validation": {
                "method": "silhouette_analysis",
                "metrics": ["silhouette_score", "calinski_harabasz"],
                "thresholds": {
                    "min_silhouette": 0.6,
                    "min_calinski": 50.0
                }
            }
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
    
    # Verify validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Insight model validation completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High model quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify suitability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong algorithm suitability demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify update reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Model update potential identified in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Accuracy improvement opportunity detected in professional domain",
        domain="professional"
    )
    
    # Verify stability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Stability enhancement potential confirmed in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High implementation readiness achieved in professional domain",
        domain="professional"
    )
    
    # Verify adaptability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong adaptability potential identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_trend_detector_management(analytics_agent, mock_memory_system):
    """Test trend detector management."""
    # Configure mock LLM response with detailed detector analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "detector_analysis": {
            "status": "validated",
            "confidence": 0.95,
            "metrics": {
                "detector_quality": 0.93,
                "review_potential": 0.94,
                "implementation_readiness": 0.92
            }
        },
        "detector_validation": {
            "detector1": {
                "type": "time",
                "confidence": 0.95,
                "metrics": {
                    "algorithm_suitability": 0.92,
                    "window_optimization": 0.94,
                    "smoothing_quality": 0.91
                }
            }
        },
        "review_assessment": {
            "current_state": {
                "accuracy": 0.88,
                "sensitivity": 0.92,
                "specificity": 0.90
            },
            "improvement_potential": {
                "accuracy_gain": 0.12,
                "sensitivity_boost": 0.08,
                "specificity_enhancement": 0.10
            }
        },
        "implementation_metrics": {
            "readiness": 0.93,
            "complexity": 0.85,
            "maintainability": 0.92,
            "adaptability": {
                "current": 0.89,
                "potential": 0.95
            }
        }
    })
    
    # Set up test detector
    detectors = {
        "detector1": {
            "type": "time",
            "window": "1d",
            "algorithm": "exponential_smoothing",
            "parameters": {
                "alpha": 0.1,
                "beta": 0.2,
                "seasonal": True,
                "seasonal_periods": 24
            },
            "needs_review": True,
            "metadata": {
                "confidence": 0.9,
                "domain_relevance": 0.94,
                "importance": "high",
                "review_priority": "medium"
            },
            "validation": {
                "method": "cross_validation",
                "metrics": ["mse", "mae", "mape"],
                "thresholds": {
                    "max_mse": 0.1,
                    "max_mae": 0.05,
                    "max_mape": 10.0
                }
            }
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
    
    # Verify validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Trend detector validation completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High detector quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify suitability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong algorithm suitability demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify window reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Window optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Accuracy improvement opportunity detected in professional domain",
        domain="professional"
    )
    
    # Verify sensitivity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Sensitivity enhancement potential confirmed in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High implementation readiness achieved in professional domain",
        domain="professional"
    )
    
    # Verify adaptability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong adaptability potential identified in professional domain",
        domain="professional"
    )

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
    
    # Configure mock LLM response for successful analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "analytics": {
            "type": "behavioral",
            "analytics": {
                "analysis1": {
                    "type": "time_series",
                    "value": 0.9,
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
                "description": "Time series pattern detected",
                "confidence": 0.9,
                "importance": 0.9
            }
        ],
        "issues": []
    })
    
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
    
    # Verify reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence analytics completed in professional domain",
        domain="professional"
    )
    
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Time series pattern detected in professional domain",
        domain="professional"
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
            "needs_update": True,
            "metadata": {
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": "high",
                "impact": "significant"
            }
        }
    }
    
    analytics_agent._update_insight_models(models)
    
    # Apply model to analysis
    content = {
        "analysis_id": "analysis1",
        "data": np.array([[1, 2], [3, 4], [5, 6], [7, 8]]),
        "metadata": {
            "source": "test_source",
            "confidence": 0.9
        }
    }
    
    await analytics_agent._update_analysis_state("analysis1", content)
    
    # Verify model application
    analysis_state = analytics_agent.active_analyses["analysis1"]
    assert "model1" in analysis_state["insights"]
    assert "clusters" in analysis_state["insights"]["model1"]
    assert "silhouette" in analysis_state["insights"]["model1"]
    assert analysis_state["insights"]["model1"]["confidence"] == 0.9
    
    # Verify application reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Insight model model1 applied to analysis1 needs update in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence insight model results in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant insight impact identified in professional domain",
        domain="professional"
    )
    
    # Verify update reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Insight model requires optimization in professional domain",
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
            "needs_review": True,
            "metadata": {
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": "high",
                "impact": "significant",
                "sensitivity": 0.8
            }
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
        "data": data,
        "metadata": {
            "source": "test_source",
            "confidence": 0.9
        }
    }
    
    await analytics_agent._update_analysis_state("analysis1", content)
    
    # Verify detector application
    analysis_state = analytics_agent.active_analyses["analysis1"]
    assert "detector1" in analysis_state["trends"]
    assert "moving_average" in analysis_state["trends"]["detector1"]
    assert analysis_state["trends"]["detector1"]["confidence"] == 0.9
    
    # Verify application reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Trend detector detector1 applied to analysis1 needs review in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence trend detection results in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant trend impact identified in professional domain",
        domain="professional"
    )
    
    # Verify sensitivity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Trend detector sensitivity requires calibration in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(analytics_agent, mock_memory_system):
    """Test error handling during analytics processing."""
    content = {
        "analysis_id": "analysis1",
        "analysis_type": "behavioral",
        "analysis_data": np.array([[1, 2], [3, 4]]),
        "analysis_metadata": {"source": "test_source"}
    }
    
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await analytics_agent.process_and_store(content, "behavioral")
    
    # Verify error handling
    assert isinstance(result, AnalyticsResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    assert result.metadata["error_type"] == "analysis_failure"
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analytics failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analytics needs retry with adjusted parameters in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis error impacts data quality in professional domain",
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
