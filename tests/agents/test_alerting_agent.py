"""Tests for the enhanced AlertingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.alerting_agent import AlertingAgent
from src.nia.nova.core.alerting import AlertingResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "alerting": {
            "type": "notification",
            "alerts": {
                "alert1": {
                    "type": "system",
                    "priority": 0.8,
                    "rules": ["rule1"]
                }
            },
            "rules": {
                "rule1": {
                    "type": "threshold",
                    "value": 90.0
                }
            }
        },
        "alerts": [
            {
                "type": "threshold",
                "description": "CPU usage high",
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
            "content": {"content": "Previous alert"},
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
def alerting_agent(mock_memory_system, mock_world, request):
    """Create an AlertingAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestAlerting_{request.node.name}"
    return AlertingAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(alerting_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestAlerting" in alerting_agent.name
    assert alerting_agent.domain == "professional"
    assert alerting_agent.agent_type == "alerting"
    
    # Verify enhanced attributes
    attributes = alerting_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Alert Manager"
    assert "Route alerts efficiently" in attributes["desires"]
    assert "towards_routing" in attributes["emotions"]
    assert "route_optimization" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(alerting_agent.active_alerts, dict)
    assert isinstance(alerting_agent.routing_rules, dict)
    assert isinstance(alerting_agent.delivery_states, dict)
    assert isinstance(alerting_agent.filter_rules, dict)
    assert isinstance(alerting_agent.acknowledgments, dict)
    assert isinstance(alerting_agent.escalation_paths, dict)

@pytest.mark.asyncio
async def test_process_with_alert_tracking(alerting_agent, mock_memory_system):
    """Test content processing with alert state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "alerting_result",
                "description": "successful"
            },
            {
                "type": "routing_state",
                "state": "optimal"
            },
            {
                "type": "delivery_state",
                "state": "completed"
            },
            {
                "type": "filter_state",
                "state": "active"
            }
        ]
    }
    
    content = {
        "alert_id": "alert1",
        "alert_severity": "high",
        "alert_type": "system",
        "alert_channel": "email",
        "alert_metadata": {"host": "server1"},
        "alert_routing": {
            "team": {"priority": 0.9}
        }
    }
    
    response = await alerting_agent.process(content)
    
    # Verify alert state tracking
    assert "alert1" in alerting_agent.active_alerts
    alert_state = alerting_agent.active_alerts["alert1"]
    assert alert_state["severity"] == "high"
    assert alert_state["type"] == "system"
    assert alert_state["channel"] == "email"
    assert alert_state["metadata"]["host"] == "server1"
    assert len(alert_state["history"]) == 1
    assert alert_state["needs_attention"] is True
    
    # Verify emotional updates
    assert alerting_agent.emotions["routing_state"] == "optimal"
    assert alerting_agent.emotions["delivery_state"] == "completed"
    assert alerting_agent.emotions["filter_state"] == "active"

@pytest.mark.asyncio
async def test_routing_rule_management(alerting_agent):
    """Test routing rule management and application."""
    # Set up test rule
    rules = {
        "rule1": {
            "type": "static",
            "conditions": {
                "alert_type": "system",
                "alert_severity": "high"
            },
            "actions": [
                {
                    "type": "update_channel",
                    "channel": "slack"
                },
                {
                    "type": "set_attention",
                    "value": True
                }
            ],
            "priority": 0.8
        }
    }
    
    alerting_agent._update_routing_rules(rules)
    
    # Test matching content
    content = {
        "alert_id": "alert1",
        "alert_type": "system",
        "alert_severity": "high"
    }
    
    await alerting_agent._update_alert_state("alert1", content)
    
    # Verify rule application
    alert_state = alerting_agent.active_alerts["alert1"]
    assert alert_state["channel"] == "slack"
    assert alert_state["needs_attention"] is True

@pytest.mark.asyncio
async def test_delivery_tracking(alerting_agent):
    """Test delivery state tracking and escalation."""
    content = {
        "delivery_id": "delivery1",
        "delivery_status": "failed",
        "delivery_channel": "email",
        "delivery_metadata": {"recipient": "team@org.com"},
        "severity": "high"
    }
    
    await alerting_agent._update_delivery_state("delivery1", content)
    
    # Verify delivery tracking
    assert "delivery1" in alerting_agent.delivery_states
    delivery_state = alerting_agent.delivery_states["delivery1"]
    assert delivery_state["status"] == "failed"
    assert delivery_state["channel"] == "email"
    assert delivery_state["attempts"] == 1
    assert len(delivery_state["history"]) == 1
    
    # Verify acknowledgment creation
    ack_id = "ack_delivery1"
    assert ack_id in alerting_agent.acknowledgments
    assert alerting_agent.acknowledgments[ack_id]["status"] == "pending"
    assert alerting_agent.acknowledgments[ack_id]["severity"] == "high"

@pytest.mark.asyncio
async def test_filter_rule_management(alerting_agent):
    """Test filter rule management."""
    filters = {
        "filter1": {
            "type": "static",
            "pattern": ".*warning.*",
            "action": "ignore",
            "needs_tuning": True,
            "metadata": {"reason": "noise reduction"}
        }
    }
    
    alerting_agent._update_filter_rules(filters)
    
    # Verify filter tracking
    assert "filter1" in alerting_agent.filter_rules
    filter_state = alerting_agent.filter_rules["filter1"]
    assert filter_state["type"] == "static"
    assert filter_state["pattern"] == ".*warning.*"
    assert filter_state["action"] == "ignore"
    assert filter_state["needs_tuning"] is True
    assert filter_state["metadata"]["reason"] == "noise reduction"

@pytest.mark.asyncio
async def test_escalation_path_management(alerting_agent):
    """Test escalation path management."""
    paths = {
        "path1": {
            "type": "linear",
            "steps": [
                {"level": 1, "team": "ops"},
                {"level": 2, "team": "engineering"}
            ],
            "active": True,
            "metadata": {"priority": "high"}
        }
    }
    
    alerting_agent._update_escalation_paths(paths)
    
    # Verify path tracking
    assert "path1" in alerting_agent.escalation_paths
    path_state = alerting_agent.escalation_paths["path1"]
    assert path_state["type"] == "linear"
    assert len(path_state["steps"]) == 2
    assert path_state["current_step"] == 0
    assert path_state["active"] is True
    assert path_state["metadata"]["priority"] == "high"

@pytest.mark.asyncio
async def test_process_and_store_with_enhancements(alerting_agent, mock_memory_system):
    """Test enhanced alert processing and storage."""
    content = {
        "alert_id": "alert1",
        "alert_severity": "high",
        "routing_rules": {
            "rule1": {
                "type": "static",
                "conditions": {"severity": "high"},
                "actions": [{"type": "update_channel", "channel": "slack"}]
            }
        },
        "filter_rules": {
            "filter1": {
                "type": "static",
                "pattern": ".*info.*",
                "action": "ignore"
            }
        }
    }
    
    result = await alerting_agent.process_and_store(content, "notification")
    
    # Verify alerting result
    assert isinstance(result, AlertingResult)
    assert result.is_valid is True
    
    # Verify alert tracking
    assert "alert1" in alerting_agent.active_alerts
    assert alerting_agent.active_alerts["alert1"]["severity"] == "high"
    
    # Verify rule tracking
    assert "rule1" in alerting_agent.routing_rules
    assert "filter1" in alerting_agent.filter_rules
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence alerting completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_delivery_failure_handling(alerting_agent, mock_memory_system):
    """Test delivery failure handling and escalation."""
    content = {
        "delivery_id": "delivery1",
        "delivery_status": "failed",
        "severity": "high"
    }
    
    # Simulate multiple failed attempts
    for _ in range(3):
        await alerting_agent._update_delivery_state("delivery1", content)
    
    # Verify escalation path creation
    path_id = "escalation_delivery1"
    assert path_id in alerting_agent.escalation_paths
    assert alerting_agent.escalation_paths[path_id]["status"] == "active"
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Delivery delivery1 failed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_acknowledgment_tracking(alerting_agent, mock_memory_system):
    """Test acknowledgment tracking and management."""
    # Create failed delivery to trigger acknowledgment
    delivery_content = {
        "delivery_id": "delivery1",
        "delivery_status": "failed",
        "severity": "high"
    }
    
    await alerting_agent._update_delivery_state("delivery1", delivery_content)
    
    # Verify acknowledgment tracking
    ack_id = "ack_delivery1"
    assert ack_id in alerting_agent.acknowledgments
    assert alerting_agent.acknowledgments[ack_id]["status"] == "pending"
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Acknowledgment ack_delivery1 pending in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(alerting_agent, mock_memory_system):
    """Test error handling during alerting."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await alerting_agent.process_and_store({"type": "test"}, "notification")
    
    # Verify error handling
    assert isinstance(result, AlertingResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Alerting failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(alerting_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await alerting_agent.process_and_store(
        {"type": "test"},
        "notification",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await alerting_agent.process_and_store(
            {"type": "test"},
            "notification",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
