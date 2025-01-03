"""Tests for the enhanced MonitoringAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.monitoring_agent import MonitoringAgent
from src.nia.nova.core.monitoring import MonitoringResult
from src.nia.memory.memory_types import AgentResponse

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
                "agent1": {
                    "type": "task",
                    "priority": 0.8,
                    "metrics": ["metric1"]
                }
            },
            "metrics": {
                "metric1": {
                    "type": "gauge",
                    "value": 75.0
                }
            }
        },
        "metrics": [
            {
                "type": "performance",
                "description": "CPU usage",
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
            "content": {"content": "Previous monitoring"},
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
def monitoring_agent(mock_memory_system, mock_world, request):
    """Create a MonitoringAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestMonitoring_{request.node.name}"
    return MonitoringAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(monitoring_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestMonitoring" in monitoring_agent.name
    assert monitoring_agent.domain == "professional"
    assert monitoring_agent.agent_type == "monitoring"
    
    # Verify enhanced attributes
    attributes = monitoring_agent.get_attributes()
    assert attributes["occupation"] == "Advanced System Monitor"
    assert "Collect real-time metrics" in attributes["desires"]
    assert "towards_metrics" in attributes["emotions"]
    assert "alert_management" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(monitoring_agent.active_metrics, dict)
    assert isinstance(monitoring_agent.health_checks, dict)
    assert isinstance(monitoring_agent.alert_states, dict)
    assert isinstance(monitoring_agent.incident_tracking, dict)
    assert isinstance(monitoring_agent.trend_analysis, dict)
    assert isinstance(monitoring_agent.thresholds, dict)

@pytest.mark.asyncio
async def test_process_with_metric_tracking(monitoring_agent, mock_memory_system):
    """Test content processing with metric state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "monitoring_result",
                "description": "successful"
            },
            {
                "type": "metric_state",
                "state": "normal"
            },
            {
                "type": "health_state",
                "state": "healthy"
            },
            {
                "type": "alert_state",
                "state": "clear"
            }
        ]
    }
    
    content = {
        "metric_id": "cpu_usage",
        "metric_value": 75.0,
        "metric_unit": "percent",
        "metric_type": "gauge",
        "metric_metadata": {"host": "server1"},
        "metric_thresholds": {
            "warning": {"max": 80.0},
            "critical": {"max": 90.0}
        }
    }
    
    response = await monitoring_agent.process(content)
    
    # Verify metric state tracking
    assert "cpu_usage" in monitoring_agent.active_metrics
    metric_state = monitoring_agent.active_metrics["cpu_usage"]
    assert metric_state["value"] == 75.0
    assert metric_state["unit"] == "percent"
    assert metric_state["type"] == "gauge"
    assert metric_state["metadata"]["host"] == "server1"
    assert len(metric_state["history"]) == 1
    assert not metric_state["needs_attention"]
    
    # Verify emotional updates
    assert monitoring_agent.emotions["metric_state"] == "normal"
    assert monitoring_agent.emotions["health_state"] == "healthy"
    assert monitoring_agent.emotions["alert_state"] == "clear"

@pytest.mark.asyncio
async def test_health_check_handling(monitoring_agent):
    """Test health check handling and alert generation."""
    content = {
        "check_id": "api_health",
        "check_status": "failing",
        "check_type": "http",
        "check_metadata": {"endpoint": "/api/health"},
        "severity": "high"
    }
    
    await monitoring_agent._update_health_check("api_health", content)
    
    # Verify health check tracking
    assert "api_health" in monitoring_agent.health_checks
    check_state = monitoring_agent.health_checks["api_health"]
    assert check_state["status"] == "failing"
    assert check_state["check_type"] == "http"
    assert check_state["metadata"]["endpoint"] == "/api/health"
    assert len(check_state["history"]) == 1
    
    # Verify alert generation
    alert_id = "alert_api_health"
    assert alert_id in monitoring_agent.alert_states
    alert_state = monitoring_agent.alert_states[alert_id]
    assert alert_state["status"] == "triggered"
    assert alert_state["severity"] == "high"
    
    # Verify incident creation
    incident_id = "incident_api_health"
    assert incident_id in monitoring_agent.incident_tracking
    incident_state = monitoring_agent.incident_tracking[incident_id]
    assert incident_state["status"] == "unresolved"
    assert incident_state["severity"] == "high"

@pytest.mark.asyncio
async def test_threshold_management(monitoring_agent):
    """Test threshold configuration and management."""
    thresholds = {
        "cpu_threshold": {
            "type": "static",
            "min": 0.0,
            "max": 90.0,
            "unit": "percent",
            "metadata": {"component": "cpu"}
        },
        "memory_threshold": {
            "type": "dynamic",
            "min": 100.0,
            "max": 1000.0,
            "unit": "MB",
            "metadata": {"component": "memory"}
        }
    }
    
    monitoring_agent._update_thresholds(thresholds)
    
    # Verify threshold tracking
    assert "cpu_threshold" in monitoring_agent.thresholds
    cpu_threshold = monitoring_agent.thresholds["cpu_threshold"]
    assert cpu_threshold["type"] == "static"
    assert cpu_threshold["min"] == 0.0
    assert cpu_threshold["max"] == 90.0
    assert cpu_threshold["unit"] == "percent"
    assert cpu_threshold["metadata"]["component"] == "cpu"
    
    assert "memory_threshold" in monitoring_agent.thresholds
    memory_threshold = monitoring_agent.thresholds["memory_threshold"]
    assert memory_threshold["type"] == "dynamic"
    assert memory_threshold["min"] == 100.0
    assert memory_threshold["max"] == 1000.0
    assert memory_threshold["unit"] == "MB"

@pytest.mark.asyncio
async def test_trend_analysis(monitoring_agent):
    """Test trend analysis tracking."""
    trends = {
        "cpu_trend": {
            "type": "moving_average",
            "window": "1h",
            "aggregation": "avg",
            "data_points": [
                {"value": 75.0, "timestamp": "2024-01-01T00:00:00Z"},
                {"value": 80.0, "timestamp": "2024-01-01T00:15:00Z"}
            ],
            "needs_attention": True,
            "metadata": {"component": "cpu"}
        }
    }
    
    await monitoring_agent._update_trend_analysis(trends)
    
    # Verify trend tracking
    assert "cpu_trend" in monitoring_agent.trend_analysis
    trend_state = monitoring_agent.trend_analysis["cpu_trend"]
    assert trend_state["type"] == "moving_average"
    assert trend_state["window"] == "1h"
    assert trend_state["aggregation"] == "avg"
    assert len(trend_state["data_points"]) == 2
    assert trend_state["needs_attention"] is True
    assert trend_state["metadata"]["component"] == "cpu"

@pytest.mark.asyncio
async def test_monitor_and_store_with_enhancements(monitoring_agent, mock_memory_system):
    """Test enhanced monitoring and storage."""
    content = {
        "metric_id": "cpu_usage",
        "metric_value": 85.0,
        "thresholds": {
            "cpu_threshold": {
                "type": "static",
                "max": 80.0
            }
        },
        "trends": {
            "cpu_trend": {
                "type": "moving_average",
                "needs_attention": True
            }
        }
    }
    
    result = await monitoring_agent.monitor_and_store(content, "performance")
    
    # Verify monitoring result
    assert isinstance(result, MonitoringResult)
    assert result.is_valid is True
    
    # Verify metric tracking
    assert "cpu_usage" in monitoring_agent.active_metrics
    assert monitoring_agent.active_metrics["cpu_usage"]["value"] == 85.0
    
    # Verify threshold tracking
    assert "cpu_threshold" in monitoring_agent.thresholds
    
    # Verify trend tracking
    assert "cpu_trend" in monitoring_agent.trend_analysis
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence monitoring completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_metric_threshold_violation(monitoring_agent, mock_memory_system):
    """Test metric threshold violation handling."""
    content = {
        "metric_id": "memory_usage",
        "metric_value": 95.0,
        "metric_thresholds": {
            "critical": {"max": 90.0}
        }
    }
    
    await monitoring_agent._update_metric_state("memory_usage", content)
    
    # Verify attention flag
    assert monitoring_agent.active_metrics["memory_usage"]["needs_attention"] is True
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Metric memory_usage requires attention in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_incident_tracking(monitoring_agent, mock_memory_system):
    """Test incident tracking and management."""
    # Create failing health check
    check_content = {
        "check_id": "database",
        "check_status": "failing",
        "severity": "high"
    }
    
    await monitoring_agent._update_health_check("database", check_content)
    
    # Verify incident tracking
    incident_id = "incident_database"
    assert incident_id in monitoring_agent.incident_tracking
    assert monitoring_agent.incident_tracking[incident_id]["status"] == "unresolved"
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Incident incident_database unresolved in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(monitoring_agent, mock_memory_system):
    """Test error handling during monitoring."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await monitoring_agent.monitor_and_store({"type": "test"}, "performance")
    
    # Verify error handling
    assert isinstance(result, MonitoringResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Monitoring failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(monitoring_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await monitoring_agent.monitor_and_store(
        {"type": "test"},
        "performance",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await monitoring_agent.monitor_and_store(
            {"type": "test"},
            "performance",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
