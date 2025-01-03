"""Tests for the enhanced MetricsAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.metrics_agent import MetricsAgent
from src.nia.nova.core.metrics import MetricsResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def metrics_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a MetricsAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestMetrics_{request.node.name}"
    
    # Update mock memory system for metrics agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "metrics": {
            "type": "performance",
            "metrics": {
                "metric1": {
                    "type": "latency",
                    "value": 100.0,
                    "unit": "ms"
                }
            },
            "metadata": {
                "service": "test_service"
            }
        },
        "values": [
            {
                "type": "threshold",
                "description": "Latency within limits",
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
    
    return MetricsAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(metrics_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestMetrics" in metrics_agent.name
    assert metrics_agent.domain == "professional"
    assert metrics_agent.agent_type == "metrics"
    
    # Verify enhanced attributes
    attributes = metrics_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Metrics Manager"
    assert "Collect metrics efficiently" in attributes["desires"]
    assert "towards_collection" in attributes["emotions"]
    assert "collection_optimization" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(metrics_agent.active_metrics, dict)
    assert isinstance(metrics_agent.collection_strategies, dict)
    assert isinstance(metrics_agent.aggregation_rules, dict)
    assert isinstance(metrics_agent.calculation_templates, dict)
    assert isinstance(metrics_agent.retention_policies, dict)

@pytest.mark.asyncio
async def test_process_with_metric_tracking(metrics_agent, mock_memory_system):
    """Test content processing with metric state tracking."""
    # Configure mock LLM response
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "type": "metrics_result",
                "description": "successful"
            },
            {
                "type": "collection_state",
                "state": "optimal"
            },
            {
                "type": "aggregation_state",
                "state": "efficient"
            },
            {
                "type": "calculation_state",
                "state": "accurate"
            }
        ]
    })
    
    content = {
        "metric_id": "metric1",
        "metric_type": "latency",
        "metric_value": 100.0,
        "metric_unit": "ms",
        "metric_metadata": {"service": "test_service"},
        "metric_aggregations": {
            "hourly": {"priority": 0.9}
        }
    }
    
    response = await metrics_agent.process(content)
    
    # Verify metric state tracking
    assert "metric1" in metrics_agent.active_metrics
    metric_state = metrics_agent.active_metrics["metric1"]
    assert metric_state["type"] == "latency"
    assert metric_state["value"] == 100.0
    assert metric_state["unit"] == "ms"
    assert metric_state["metadata"]["service"] == "test_service"
    assert len(metric_state["history"]) == 1
    assert metric_state["needs_attention"] is True
    
    # Verify emotional updates
    assert metrics_agent.emotions["collection_state"] == "optimal"
    assert metrics_agent.emotions["aggregation_state"] == "efficient"
    assert metrics_agent.emotions["calculation_state"] == "accurate"

@pytest.mark.asyncio
async def test_collection_strategy_management(metrics_agent):
    """Test collection strategy management."""
    # Set up test strategy
    strategies = {
        "strategy1": {
            "type": "time",
            "interval": "5m",
            "batch_size": 50,
            "needs_optimization": True,
            "metadata": {"source": "test_service"}
        }
    }
    
    metrics_agent._update_collection_strategies(strategies)
    
    # Verify strategy tracking
    assert "strategy1" in metrics_agent.collection_strategies
    strategy_state = metrics_agent.collection_strategies["strategy1"]
    assert strategy_state["type"] == "time"
    assert strategy_state["interval"] == "5m"
    assert strategy_state["batch_size"] == 50
    assert strategy_state["needs_optimization"] is True
    assert strategy_state["metadata"]["source"] == "test_service"

@pytest.mark.asyncio
async def test_aggregation_rule_management(metrics_agent):
    """Test aggregation rule management."""
    rules = {
        "rule1": {
            "type": "static",
            "function": "percentile",
            "window": "5m",
            "needs_tuning": True,
            "metadata": {"percentile": 95}
        }
    }
    
    metrics_agent._update_aggregation_rules(rules)
    
    # Verify rule tracking
    assert "rule1" in metrics_agent.aggregation_rules
    rule_state = metrics_agent.aggregation_rules["rule1"]
    assert rule_state["type"] == "static"
    assert rule_state["function"] == "percentile"
    assert rule_state["window"] == "5m"
    assert rule_state["needs_tuning"] is True
    assert rule_state["metadata"]["percentile"] == 95

@pytest.mark.asyncio
async def test_calculation_template_management(metrics_agent):
    """Test calculation template management."""
    templates = {
        "template1": {
            "type": "static",
            "formula": "value * 2",
            "variables": {
                "value": {"type": "number"}
            },
            "needs_update": True,
            "metadata": {"description": "Double value"}
        }
    }
    
    metrics_agent._update_calculation_templates(templates)
    
    # Verify template tracking
    assert "template1" in metrics_agent.calculation_templates
    template_state = metrics_agent.calculation_templates["template1"]
    assert template_state["type"] == "static"
    assert template_state["formula"] == "value * 2"
    assert template_state["variables"]["value"]["type"] == "number"
    assert template_state["needs_update"] is True
    assert template_state["metadata"]["description"] == "Double value"

@pytest.mark.asyncio
async def test_retention_policy_management(metrics_agent):
    """Test retention policy management."""
    policies = {
        "policy1": {
            "type": "time",
            "duration": "7d",
            "compression": "gzip",
            "needs_review": True,
            "metadata": {"max_size": "1GB"}
        }
    }
    
    metrics_agent._update_retention_policies(policies)
    
    # Verify policy tracking
    assert "policy1" in metrics_agent.retention_policies
    policy_state = metrics_agent.retention_policies["policy1"]
    assert policy_state["type"] == "time"
    assert policy_state["duration"] == "7d"
    assert policy_state["compression"] == "gzip"
    assert policy_state["needs_review"] is True
    assert policy_state["metadata"]["max_size"] == "1GB"

@pytest.mark.asyncio
async def test_process_and_store_with_enhancements(metrics_agent, mock_memory_system):
    """Test enhanced metrics processing and storage."""
    # Configure mock LLM response
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "metrics": {
            "type": "performance",
            "metrics": {
                "metric1": {
                    "type": "latency",
                    "value": 100.0,
                    "unit": "ms"
                }
            }
        },
        "values": [
            {
                "type": "threshold",
                "description": "Latency within limits",
                "confidence": 0.9,
                "importance": 0.8
            }
        ],
        "issues": []
    })
    
    content = {
        "metric_id": "metric1",
        "metric_type": "latency",
        "collection_strategies": {
            "strategy1": {
                "type": "time",
                "interval": "5m"
            }
        },
        "aggregation_rules": {
            "rule1": {
                "type": "static",
                "function": "avg"
            }
        }
    }
    
    result = await metrics_agent.process_and_store(content, "performance")
    
    # Verify metrics result
    assert isinstance(result, MetricsResult)
    assert result.is_valid is True
    
    # Verify metric tracking
    assert "metric1" in metrics_agent.active_metrics
    assert metrics_agent.active_metrics["metric1"]["type"] == "latency"
    
    # Verify rule tracking
    assert "strategy1" in metrics_agent.collection_strategies
    assert "rule1" in metrics_agent.aggregation_rules
    
    # Verify reflections were recorded
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence metrics completed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_calculation_template_application(metrics_agent, mock_memory_system):
    """Test calculation template application and reflection."""
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "formula": "value * 2",
            "variables": {
                "value": {"type": "number"}
            },
            "needs_update": True
        }
    }
    
    metrics_agent._update_calculation_templates(templates)
    
    # Apply template to metric
    content = {
        "metric_id": "metric1",
        "value": 100.0
    }
    
    await metrics_agent._update_metric_state("metric1", content)
    
    # Verify template application
    metric_state = metrics_agent.active_metrics["metric1"]
    assert metric_state["value"] == 200.0  # 100 * 2
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Calculation template template1 applied to metric1 needs update",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(metrics_agent, mock_memory_system):
    """Test error handling during metrics processing."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await metrics_agent.process_and_store({"type": "test"}, "performance")
    
    # Verify error handling
    assert isinstance(result, MetricsResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Metrics failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(metrics_agent, mock_memory_system):
    """Test domain access validation."""
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Test allowed domain
    result = await metrics_agent.process_and_store(
        {"type": "test"},
        "performance",
        target_domain="professional"
    )
    assert result.is_valid is True
    
    # Test denied domain
    with pytest.raises(PermissionError):
        await metrics_agent.process_and_store(
            {"type": "test"},
            "performance",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
