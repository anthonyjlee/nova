"""Tests for the enhanced LoggingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.logging_agent import LoggingAgent
from src.nia.nova.core.logging import LoggingResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "logging": {
            "type": "application",
            "logs": {
                "log1": {
                    "type": "info",
                    "level": "info",
                    "message": "Test message"
                }
            },
            "metadata": {
                "app": "test_app"
            }
        },
        "logs": [
            {
                "type": "format",
                "description": "Log format valid",
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
            "content": {"content": "Previous log"},
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
def logging_agent(mock_memory_system, mock_world, request):
    """Create a LoggingAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestLogging_{request.node.name}"
    return LoggingAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(logging_agent):
    """Test agent initialization with enhanced attributes."""
    assert "TestLogging" in logging_agent.name
    assert logging_agent.domain == "professional"
    assert logging_agent.agent_type == "logging"
    
    # Verify enhanced attributes
    attributes = logging_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Log Manager"
    assert "Structure logs efficiently" in attributes["desires"]
    assert "towards_structure" in attributes["emotions"]
    assert "structure_optimization" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(logging_agent.active_logs, dict)
    assert isinstance(logging_agent.format_templates, dict)
    assert isinstance(logging_agent.storage_policies, dict)
    assert isinstance(logging_agent.context_rules, dict)
    assert isinstance(logging_agent.enrichment_rules, dict)
    assert isinstance(logging_agent.rotation_policies, dict)

@pytest.mark.asyncio
async def test_process_with_log_tracking(logging_agent, mock_memory_system):
    """Test content processing with log state tracking."""
    # Mock memory system response
    mock_memory_system.llm.analyze.return_value = {
        "concepts": [
            {
                "type": "logging_result",
                "description": "successful"
            },
            {
                "type": "structure_state",
                "state": "optimal"
            },
            {
                "type": "context_state",
                "state": "enriched"
            },
            {
                "type": "format_state",
                "state": "consistent"
            }
        ]
    }
    
    content = {
        "log_id": "log1",
        "log_level": "info",
        "log_type": "application",
        "log_format": "json",
        "log_metadata": {"app": "test_app"},
        "log_context": {
            "request": {"priority": 0.9}
        }
    }
    
    response = await logging_agent.process(content)
    
    # Verify log state tracking
    assert "log1" in logging_agent.active_logs
    log_state = logging_agent.active_logs["log1"]
    assert log_state["level"] == "info"
    assert log_state["type"] == "application"
    assert log_state["format"] == "json"
    assert log_state["metadata"]["app"] == "test_app"
    assert len(log_state["history"]) == 1
    assert log_state["needs_attention"] is True
    
    # Verify emotional updates
    assert logging_agent.emotions["structure_state"] == "optimal"
    assert logging_agent.emotions["context_state"] == "enriched"
    assert logging_agent.emotions["format_state"] == "consistent"

@pytest.mark.asyncio
async def test_format_template_management(logging_agent):
    """Test format template management and application."""
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "pattern": ".*error.*",
            "format": {
                "timestamp_format": "ISO8601",
                "level_format": "uppercase",
                "message_format": "structured"
            },
            "needs_update": False
        }
    }
    
    logging_agent._update_format_templates(templates)
    
    # Test matching content
    content = {
        "log_id": "log1",
        "message": "error occurred"
    }
    
    await logging_agent._update_log_state("log1", content)
    
    # Verify template application
    log_state = logging_agent.active_logs["log1"]
    assert log_state["metadata"]["timestamp_format"] == "ISO8601"
    assert log_state["metadata"]["level_format"] == "uppercase"
    assert log_state["metadata"]["message_format"] == "structured"

@pytest.mark.asyncio
async def test_storage_policy_management(logging_agent):
    """Test storage policy management."""
    policies = {
        "policy1": {
            "type": "time",
            "pattern": ".*debug.*",
            "storage": "s3",
            "needs_optimization": True,
            "metadata": {"retention": "30d"}
        }
    }
    
    logging_agent._update_storage_policies(policies)
    
    # Verify policy tracking
    assert "policy1" in logging_agent.storage_policies
    policy_state = logging_agent.storage_policies["policy1"]
    assert policy_state["type"] == "time"
    assert policy_state["pattern"] == ".*debug.*"
    assert policy_state["storage"] == "s3"
    assert policy_state["needs_optimization"] is True
    assert policy_state["metadata"]["retention"] == "30d"

@pytest.mark.asyncio
async def test_context_rule_management(logging_agent):
    """Test context rule management."""
    rules = {
        "rule1": {
            "type": "static",
            "pattern": ".*request.*",
            "context": {
                "add_trace_id": True,
                "add_user_id": True
            },
            "needs_tuning": True,
            "metadata": {"priority": "high"}
        }
    }
    
    logging_agent._update_context_rules(rules)
    
    # Verify rule tracking
    assert "rule1" in logging_agent.context_rules
    rule_state = logging_agent.context_rules["rule1"]
    assert rule_state["type"] == "static"
    assert rule_state["pattern"] == ".*request.*"
    assert rule_state["context"]["add_trace_id"] is True
    assert rule_state["needs_tuning"] is True
    assert rule_state["metadata"]["priority"] == "high"

@pytest.mark.asyncio
async def test_enrichment_rule_management(logging_agent):
    """Test enrichment rule management."""
    rules = {
        "rule1": {
            "type": "static",
            "pattern": ".*user.*",
            "enrichment": {
                "add_user_details": True,
                "add_session_info": True
            },
            "needs_update": True,
            "metadata": {"source": "user_service"}
        }
    }
    
    logging_agent._update_enrichment_rules(rules)
    
    # Verify rule tracking
    assert "rule1" in logging_agent.enrichment_rules
    rule_state = logging_agent.enrichment_rules["rule1"]
    assert rule_state["type"] == "static"
    assert rule_state["pattern"] == ".*user.*"
    assert rule_state["enrichment"]["add_user_details"] is True
    assert rule_state["needs_update"] is True
    assert rule_state["metadata"]["source"] == "user_service"

@pytest.mark.asyncio
async def test_rotation_policy_management(logging_agent):
    """Test rotation policy management."""
    policies = {
        "policy1": {
            "type": "time",
            "interval": "hourly",
            "retention": 24,
            "needs_review": True,
            "metadata": {"max_size": "1GB"}
        }
    }
    
    logging_agent._update_rotation_policies(policies)
    
    # Verify policy tracking
    assert "policy1" in logging_agent.rotation_policies
    policy_state = logging_agent.rotation_policies["policy1"]
    assert policy_state["type"] == "time"
    assert policy_state["interval"] == "hourly"
    assert policy_state["retention"] == 24
    assert policy_state["needs_review"] is True
    assert policy_state["metadata"]["max_size"] == "1GB"

@pytest.mark.asyncio
async def test_process_and_store_with_enhancements(logging_agent, mock_memory_system):
    """Test enhanced log processing and storage."""
    content = {
        "log_id": "log1",
        "log_level": "info",
        "format_templates": {
            "template1": {
                "type": "static",
                "pattern": ".*info.*",
                "format": {"timestamp_format": "ISO8601"}
            }
        },
        "storage_policies": {
            "policy1": {
                "type": "time",
                "interval": "daily"
            }
        }
    }
    
    result = await logging_agent.process_and_store(content, "application")
    
    # Verify logging result
    assert isinstance(result, LoggingResult)
    assert result.is_valid is True
    
    # Verify log tracking
    assert "log1" in logging_agent.active_logs
    assert logging_agent.active_logs["log1"]["level"] == "info"
    
    # Verify rule tracking
    assert "template1" in logging_agent.format_templates
    assert "policy1" in logging_agent.storage_policies
    
    # Verify reflections were recorded
    reflection_calls = mock_memory_system.semantic.store.record_reflection.call_args_list
    assert any(
        "High confidence logging completed" in call.args[0]
        for call in reflection_calls
    )

@pytest.mark.asyncio
async def test_format_template_application(logging_agent, mock_memory_system):
    """Test format template application and reflection."""
    # Set up test template
    templates = {
        "template1": {
            "type": "static",
            "pattern": ".*error.*",
            "format": {
                "timestamp_format": "ISO8601"
            },
            "needs_update": True
        }
    }
    
    logging_agent._update_format_templates(templates)
    
    # Apply template to log
    content = {
        "log_id": "log1",
        "message": "error occurred"
    }
    
    await logging_agent._update_log_state("log1", content)
    
    # Verify template application
    log_state = logging_agent.active_logs["log1"]
    assert log_state["metadata"]["timestamp_format"] == "ISO8601"
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Format template template1 applied to log1 needs update",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(logging_agent, mock_memory_system):
    """Test error handling during logging."""
    # Make LLM raise an error
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await logging_agent.process_and_store({"type": "test"}, "application")
    
    # Verify error handling
    assert isinstance(result, LoggingResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_called_with(
        "Logging failed - issues detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(logging_agent, mock_memory_system):
    """Test domain access validation."""
    # Test allowed domain
    await logging_agent.process_and_store(
        {"type": "test"},
        "application",
        target_domain="professional"
    )
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await logging_agent.process_and_store(
            {"type": "test"},
            "application",
            target_domain="restricted"
        )

if __name__ == "__main__":
    pytest.main([__file__])
