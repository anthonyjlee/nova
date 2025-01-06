"""Tests for Nova's metrics functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.metrics import MetricsAgent, MetricsResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "metrics": {
            "type": "performance",
            "metrics": {
                "main": {
                    "type": "processor",
                    "value": 85.5,
                    "unit": "percent",
                    "description": "Main metric",
                    "thresholds": {
                        "warning": 80.0,
                        "critical": 90.0
                    }
                },
                "sub": {
                    "type": "helper",
                    "value": 45.2,
                    "unit": "percent",
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "values": [
            {
                "type": "metric",
                "description": "Metric analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "thresholds": {
                    "warning": 80.0,
                    "critical": 90.0
                }
            }
        ],
        "issues": [
            {
                "type": "missing_threshold",
                "severity": "medium",
                "description": "Missing threshold",
                "domain_impact": 0.3,
                "suggested_fix": "Add threshold",
                "thresholds": {
                    "warning": 80.0,
                    "critical": 90.0
                }
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
            "content": {"content": "Similar metrics"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def metrics_agent(mock_llm, mock_vector_store):
    """Create a MetricsAgent instance with mock dependencies."""
    return MetricsAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_metrics_with_llm(metrics_agent, mock_llm):
    """Test metrics processing using LLM."""
    content = {
        "content": "Test content",
        "type": "performance",
        "metadata": {"key": "value"}
    }
    
    result = await metrics_agent.process_metrics(content, "performance")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, MetricsResult)
    assert result.metrics["type"] == "performance"
    assert len(result.metrics["metrics"]) == 2
    assert len(result.values) == 1
    assert len(result.issues) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_process_metrics_without_llm():
    """Test metrics processing without LLM (fallback mode)."""
    agent = MetricsAgent()  # No LLM provided
    content = {
        "values": ["value1"],
        "thresholds": {"value1": []},
        "trends": {}
    }
    
    result = await agent.process_metrics(content, "performance")
    
    # Verify basic metrics worked
    assert isinstance(result, MetricsResult)
    assert result.metrics["type"] == "performance"
    assert "metrics" in result.metrics
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_metrics(metrics_agent, mock_vector_store):
    """Test similar metrics retrieval."""
    content = {"content": "test content"}
    metrics_type = "performance"
    
    metrics = await metrics_agent._get_similar_metrics(content, metrics_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "metrics",
            "metrics_type": "performance"
        }
    )
    assert len(metrics) == 1
    assert "content" in metrics[0]
    assert metrics[0]["similarity"] == 0.9

def test_basic_metrics_performance(metrics_agent):
    """Test basic performance metrics."""
    content = {
        "values": ["value1"],
        "thresholds": {"value1": []},
        "trends": {}
    }
    
    result = metrics_agent._basic_metrics(content, "performance", [])
    
    assert "metrics" in result
    assert "values" in result
    assert "issues" in result
    assert result["metrics"]["type"] == "performance"
    assert len(result["values"]) > 0
    assert all(v["type"] in ["has_values", "has_thresholds", "has_trends"] for v in result["values"])

def test_basic_metrics_resource(metrics_agent):
    """Test basic resource metrics."""
    content = {
        "usage": {"resource1": []},
        "limits": {"resource1": []},
        "allocation": {}
    }
    
    result = metrics_agent._basic_metrics(content, "resource", [])
    
    assert "metrics" in result
    assert "values" in result
    assert "issues" in result
    assert result["metrics"]["type"] == "resource"
    assert len(result["values"]) > 0
    assert all(v["type"] in ["has_usage", "has_limits", "has_allocation"] for v in result["values"])

def test_check_rule(metrics_agent):
    """Test metrics rule checking."""
    content = {
        "values": ["value1"],
        "thresholds": {"value1": []},
        "trends": {},
        "usage": {"resource1": []},
        "limits": {"resource1": []},
        "allocation": {},
        "scores": {"metric1": []},
        "criteria": {"metric1": []},
        "benchmarks": {}
    }
    
    # Test performance rules
    assert metrics_agent._check_rule("has_values", content) is True
    assert metrics_agent._check_rule("has_thresholds", content) is True
    assert metrics_agent._check_rule("has_trends", content) is True
    
    # Test resource rules
    assert metrics_agent._check_rule("has_usage", content) is True
    assert metrics_agent._check_rule("has_limits", content) is True
    assert metrics_agent._check_rule("has_allocation", content) is True
    
    # Test quality rules
    assert metrics_agent._check_rule("has_scores", content) is True
    assert metrics_agent._check_rule("has_criteria", content) is True
    assert metrics_agent._check_rule("has_benchmarks", content) is True

def test_extract_metrics(metrics_agent):
    """Test metrics extraction and validation."""
    metrics = {
        "metrics": {
            "type": "performance",
            "metrics": {
                "main": {
                    "type": "processor",
                    "value": 85.5,
                    "unit": "percent",
                    "description": "Main metric"
                },
                "sub": {
                    "type": "helper",
                    "value": 45.2,
                    "unit": "percent"
                }
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = metrics_agent._extract_metrics(metrics)
    
    assert result["type"] == "performance"
    assert len(result["metrics"]) == 2
    assert result["metrics"]["main"]["value"] == 85.5
    assert "description" in result["metrics"]["main"]
    assert "metadata" in result
    assert "unit" in result["metrics"]["sub"]

def test_extract_values(metrics_agent):
    """Test value extraction and validation."""
    metrics = {
        "values": [
            {
                "type": "metric",
                "description": "Test value",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "thresholds": {
                    "warning": 80.0,
                    "critical": 90.0
                }
            },
            {
                "type": "basic",
                "description": "Basic value",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    values = metrics_agent._extract_values(metrics)
    
    assert len(values) == 2  # Invalid one should be filtered out
    assert all("type" in v for v in values)
    assert all("description" in v for v in values)
    assert all("confidence" in v for v in values)
    assert all(isinstance(v["confidence"], (int, float)) for v in values)
    assert all(0 <= v["confidence"] <= 1 for v in values)
    assert any("domain_relevance" in v for v in values)

def test_extract_issues(metrics_agent):
    """Test issue extraction and validation."""
    metrics = {
        "issues": [
            {
                "type": "missing_threshold",
                "severity": "high",
                "description": "Missing threshold",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add threshold",
                "thresholds": {
                    "warning": 80.0,
                    "critical": 90.0
                }
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = metrics_agent._extract_issues(metrics)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(metrics_agent):
    """Test confidence calculation."""
    metrics = {
        "metrics": {
            "main": {"type": "processor"},
            "sub": {"type": "helper"}
        },
        "metadata": {
            "version": "1.0",
            "environment": "test"
        }
    }
    
    values = [
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
    
    confidence = metrics_agent._calculate_confidence(metrics, values, issues)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Metrics confidence (0.2 from metrics + metadata)
    # - Value confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(metrics_agent):
    """Test validity determination."""
    metrics = {
        "metrics": {
            "main": {"type": "processor"}
        },
        "metadata": {
            "version": "1.0"
        }
    }
    
    values = [
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
    
    is_valid = metrics_agent._determine_validity(metrics, values, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed values
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = metrics_agent._determine_validity(metrics, values, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(metrics_agent):
    """Test error handling during metrics processing."""
    # Make LLM raise an error
    metrics_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await metrics_agent.process_metrics({"content": "test"}, "performance")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, MetricsResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.values) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(metrics_agent):
    """Test domain awareness in metrics processing."""
    content = {"content": "test"}
    result = await metrics_agent.process_metrics(content, "performance")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    metrics_agent.domain = "personal"
    result = await metrics_agent.process_metrics(content, "performance")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
