"""Tests for Nova's monitoring functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.monitoring import MonitoringAgent, MonitoringResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "monitoring": {
            "type": "performance",
            "agents": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main agent",
                    "metrics": ["metric1", "metric2"]
                },
                "sub": {
                    "type": "helper",
                    "priority": 0.6,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "metrics": {
                "primary": ["metric1"],
                "secondary": ["metric2"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "metrics": [
            {
                "type": "metric",
                "description": "Metric analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "agents": ["agent1"]
            }
        ],
        "issues": [
            {
                "type": "missing_metric",
                "severity": "medium",
                "description": "Missing metric",
                "domain_impact": 0.3,
                "suggested_fix": "Add metric",
                "related_agents": ["agent3"]
            }
        ]
    })
    return llm

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar monitoring"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def monitoring_agent(mock_llm, mock_vector_store):
    """Create a MonitoringAgent instance with mock dependencies."""
    return MonitoringAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_monitor_agents_with_llm(monitoring_agent, mock_llm):
    """Test agent monitoring using LLM."""
    content = {
        "content": "Test content",
        "type": "performance",
        "metadata": {"key": "value"}
    }
    
    result = await monitoring_agent.monitor_agents(content, "performance")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, MonitoringResult)
    assert result.monitoring["type"] == "performance"
    assert len(result.monitoring["agents"]) == 2
    assert len(result.metrics) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_monitor_agents_without_llm():
    """Test agent monitoring without LLM (fallback mode)."""
    agent = MonitoringAgent()  # No LLM provided
    content = {
        "metrics": ["metric1"],
        "thresholds": {"metric1": []},
        "trends": {}
    }
    
    result = await agent.monitor_agents(content, "performance")
    
    # Verify basic monitoring worked
    assert isinstance(result, MonitoringResult)
    assert result.monitoring["type"] == "performance"
    assert "agents" in result.monitoring
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_monitoring(monitoring_agent, mock_vector_store):
    """Test similar monitoring retrieval."""
    content = {"content": "test content"}
    monitoring_type = "performance"
    
    monitoring = await monitoring_agent._get_similar_monitoring(content, monitoring_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "monitoring",
            "monitoring_type": "performance"
        }
    )
    assert len(monitoring) == 1
    assert "content" in monitoring[0]
    assert monitoring[0]["similarity"] == 0.9

def test_basic_monitoring_performance(monitoring_agent):
    """Test basic performance monitoring."""
    content = {
        "metrics": ["metric1"],
        "thresholds": {"metric1": []},
        "trends": {}
    }
    
    result = monitoring_agent._basic_monitoring(content, "performance", [])
    
    assert "monitoring" in result
    assert "metrics" in result
    assert "issues" in result
    assert result["monitoring"]["type"] == "performance"
    assert len(result["metrics"]) > 0
    assert all(m["type"] in ["has_metrics", "has_thresholds", "has_trends"] for m in result["metrics"])

def test_basic_monitoring_health(monitoring_agent):
    """Test basic health monitoring."""
    content = {
        "status": ["status1"],
        "diagnostics": {"status1": []},
        "recovery": {}
    }
    
    result = monitoring_agent._basic_monitoring(content, "health", [])
    
    assert "monitoring" in result
    assert "metrics" in result
    assert "issues" in result
    assert result["monitoring"]["type"] == "health"
    assert len(result["metrics"]) > 0
    assert all(m["type"] in ["has_status", "has_diagnostics", "has_recovery"] for m in result["metrics"])

def test_check_rule(monitoring_agent):
    """Test monitoring rule checking."""
    content = {
        "metrics": ["metric1"],
        "thresholds": {"metric1": []},
        "trends": {},
        "status": ["status1"],
        "diagnostics": {"status1": []},
        "recovery": {},
        "usage": {"agent1": []},
        "limits": {"agent1": []},
        "allocation": {}
    }
    
    # Test performance rules
    assert monitoring_agent._check_rule("has_metrics", content) is True
    assert monitoring_agent._check_rule("has_thresholds", content) is True
    assert monitoring_agent._check_rule("has_trends", content) is True
    
    # Test health rules
    assert monitoring_agent._check_rule("has_status", content) is True
    assert monitoring_agent._check_rule("has_diagnostics", content) is True
    assert monitoring_agent._check_rule("has_recovery", content) is True
    
    # Test resource rules
    assert monitoring_agent._check_rule("has_usage", content) is True
    assert monitoring_agent._check_rule("has_limits", content) is True
    assert monitoring_agent._check_rule("has_allocation", content) is True

def test_extract_monitoring(monitoring_agent):
    """Test monitoring extraction and validation."""
    monitoring = {
        "monitoring": {
            "type": "performance",
            "agents": {
                "main": {
                    "type": "processor",
                    "priority": 0.8,
                    "description": "Main agent"
                },
                "sub": {
                    "type": "helper",
                    "priority": 0.6
                }
            },
            "metrics": {
                "primary": ["metric1"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = monitoring_agent._extract_monitoring(monitoring)
    
    assert result["type"] == "performance"
    assert len(result["agents"]) == 2
    assert result["agents"]["main"]["priority"] == 0.8
    assert "description" in result["agents"]["main"]
    assert "metrics" in result
    assert "metadata" in result

def test_extract_metrics(monitoring_agent):
    """Test metric extraction and validation."""
    monitoring = {
        "metrics": [
            {
                "type": "metric",
                "description": "Test metric",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "agents": ["agent1"]
            },
            {
                "type": "basic",
                "description": "Basic metric",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    metrics = monitoring_agent._extract_metrics(monitoring)
    
    assert len(metrics) == 2  # Invalid one should be filtered out
    assert all("type" in m for m in metrics)
    assert all("description" in m for m in metrics)
    assert all("confidence" in m for m in metrics)
    assert any("domain_relevance" in m for m in metrics)

def test_extract_issues(monitoring_agent):
    """Test issue extraction and validation."""
    monitoring = {
        "issues": [
            {
                "type": "missing_metric",
                "severity": "high",
                "description": "Missing metric",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add metric",
                "related_agents": ["agent1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = monitoring_agent._extract_issues(monitoring)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(monitoring_agent):
    """Test confidence calculation."""
    monitoring = {
        "agents": {
            "main": {"type": "processor"},
            "sub": {"type": "helper"}
        },
        "metrics": {
            "primary": ["metric1"],
            "secondary": ["metric2"]
        }
    }
    
    metrics = [
        {
            "confidence": 0.8,
            "importance": 0.7
        },
        {
            "confidence": 0.6,
            "importance": 0.5
        }
    ]
    
    issues = [
        {
            "severity": "low",
            "type": "minor"
        },
        {
            "severity": "medium",
            "type": "warning"
        }
    ]
    
    confidence = monitoring_agent._calculate_confidence(monitoring, metrics, issues)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Monitoring confidence (0.2 from agents + metrics)
    # - Metric confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(monitoring_agent):
    """Test validity determination."""
    monitoring = {
        "agents": {
            "main": {"type": "processor"}
        },
        "metrics": {
            "primary": ["metric1"]
        }
    }
    
    metrics = [
        {
            "confidence": 0.8,
            "importance": 0.7
        },
        {
            "confidence": 0.7,
            "importance": 0.6
        },
        {
            "confidence": 0.6,
            "importance": 0.5
        }
    ]
    
    # Test with no critical issues
    issues = [
        {
            "severity": "low",
            "type": "minor"
        }
    ]
    
    is_valid = monitoring_agent._determine_validity(monitoring, metrics, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed metrics
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = monitoring_agent._determine_validity(monitoring, metrics, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(monitoring_agent):
    """Test error handling during monitoring."""
    # Make LLM raise an error
    monitoring_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await monitoring_agent.monitor_agents({"content": "test"}, "performance")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, MonitoringResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.metrics) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(monitoring_agent):
    """Test domain awareness in monitoring."""
    content = {"content": "test"}
    result = await monitoring_agent.monitor_agents(content, "performance")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    monitoring_agent.domain = "personal"
    result = await monitoring_agent.monitor_agents(content, "performance")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
