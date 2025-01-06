"""Tests for Nova's analytics functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.analytics import AnalyticsAgent, AnalyticsResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "analytics": {
            "type": "behavioral",
            "analytics": {
                "main": {
                    "type": "pattern",
                    "value": 85.5,
                    "confidence": 0.8,
                    "description": "Main pattern",
                    "patterns": {
                        "frequency": "daily",
                        "strength": "high"
                    }
                },
                "sub": {
                    "type": "segment",
                    "value": 45.2,
                    "confidence": 0.7,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "insights": [
            {
                "type": "pattern",
                "description": "Pattern analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "patterns": {
                    "frequency": "daily",
                    "strength": "high"
                }
            }
        ],
        "issues": [
            {
                "type": "missing_segment",
                "severity": "medium",
                "description": "Missing segment",
                "domain_impact": 0.3,
                "suggested_fix": "Add segment",
                "patterns": {
                    "frequency": "daily",
                    "strength": "high"
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
            "content": {"content": "Similar analytics"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def analytics_agent(mock_llm, mock_vector_store):
    """Create an AnalyticsAgent instance with mock dependencies."""
    return AnalyticsAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_analytics_with_llm(analytics_agent, mock_llm):
    """Test analytics processing using LLM."""
    content = {
        "content": "Test content",
        "type": "behavioral",
        "metadata": {"key": "value"}
    }
    
    result = await analytics_agent.process_analytics(content, "behavioral")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, AnalyticsResult)
    assert result.analytics["type"] == "behavioral"
    assert len(result.analytics["analytics"]) == 2
    assert len(result.insights) == 1
    assert len(result.issues) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_process_analytics_without_llm():
    """Test analytics processing without LLM (fallback mode)."""
    agent = AnalyticsAgent()  # No LLM provided
    content = {
        "patterns": ["pattern1"],
        "segments": {"segment1": []},
        "trends": {}
    }
    
    result = await agent.process_analytics(content, "behavioral")
    
    # Verify basic analytics worked
    assert isinstance(result, AnalyticsResult)
    assert result.analytics["type"] == "behavioral"
    assert "analytics" in result.analytics
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_analytics(analytics_agent, mock_vector_store):
    """Test similar analytics retrieval."""
    content = {"content": "test content"}
    analytics_type = "behavioral"
    
    analytics = await analytics_agent._get_similar_analytics(content, analytics_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "analytics",
            "analytics_type": "behavioral"
        }
    )
    assert len(analytics) == 1
    assert "content" in analytics[0]
    assert analytics[0]["similarity"] == 0.9

def test_basic_analytics_behavioral(analytics_agent):
    """Test basic behavioral analytics."""
    content = {
        "patterns": ["pattern1"],
        "segments": {"segment1": []},
        "trends": {}
    }
    
    result = analytics_agent._basic_analytics(content, "behavioral", [])
    
    assert "analytics" in result
    assert "insights" in result
    assert "issues" in result
    assert result["analytics"]["type"] == "behavioral"
    assert len(result["insights"]) > 0
    assert all(i["type"] in ["has_patterns", "has_segments", "has_trends"] for i in result["insights"])

def test_basic_analytics_predictive(analytics_agent):
    """Test basic predictive analytics."""
    content = {
        "models": {"model1": []},
        "features": {"feature1": []},
        "predictions": {}
    }
    
    result = analytics_agent._basic_analytics(content, "predictive", [])
    
    assert "analytics" in result
    assert "insights" in result
    assert "issues" in result
    assert result["analytics"]["type"] == "predictive"
    assert len(result["insights"]) > 0
    assert all(i["type"] in ["has_models", "has_features", "has_predictions"] for i in result["insights"])

def test_check_rule(analytics_agent):
    """Test analytics rule checking."""
    content = {
        "patterns": ["pattern1"],
        "segments": {"segment1": []},
        "trends": {},
        "models": {"model1": []},
        "features": {"feature1": []},
        "predictions": {},
        "causes": {"cause1": []},
        "correlations": {"corr1": []},
        "factors": {}
    }
    
    # Test behavioral rules
    assert analytics_agent._check_rule("has_patterns", content) is True
    assert analytics_agent._check_rule("has_segments", content) is True
    assert analytics_agent._check_rule("has_trends", content) is True
    
    # Test predictive rules
    assert analytics_agent._check_rule("has_models", content) is True
    assert analytics_agent._check_rule("has_features", content) is True
    assert analytics_agent._check_rule("has_predictions", content) is True
    
    # Test diagnostic rules
    assert analytics_agent._check_rule("has_causes", content) is True
    assert analytics_agent._check_rule("has_correlations", content) is True
    assert analytics_agent._check_rule("has_factors", content) is True

def test_extract_analytics(analytics_agent):
    """Test analytics extraction and validation."""
    analytics = {
        "analytics": {
            "type": "behavioral",
            "analytics": {
                "main": {
                    "type": "pattern",
                    "value": 85.5,
                    "confidence": 0.8,
                    "description": "Main pattern"
                },
                "sub": {
                    "type": "segment",
                    "value": 45.2,
                    "confidence": 0.7
                }
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = analytics_agent._extract_analytics(analytics)
    
    assert result["type"] == "behavioral"
    assert len(result["analytics"]) == 2
    assert result["analytics"]["main"]["value"] == 85.5
    assert "description" in result["analytics"]["main"]
    assert "metadata" in result
    assert "confidence" in result["analytics"]["sub"]

def test_extract_insights(analytics_agent):
    """Test insight extraction and validation."""
    analytics = {
        "insights": [
            {
                "type": "pattern",
                "description": "Test insight",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "patterns": {
                    "frequency": "daily",
                    "strength": "high"
                }
            },
            {
                "type": "basic",
                "description": "Basic insight",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    insights = analytics_agent._extract_insights(analytics)
    
    assert len(insights) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in insights)
    assert all("description" in i for i in insights)
    assert all("confidence" in i for i in insights)
    assert all(isinstance(i["confidence"], (int, float)) for i in insights)
    assert all(0 <= i["confidence"] <= 1 for i in insights)
    assert any("domain_relevance" in i for i in insights)

def test_extract_issues(analytics_agent):
    """Test issue extraction and validation."""
    analytics = {
        "issues": [
            {
                "type": "missing_pattern",
                "severity": "high",
                "description": "Missing pattern",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add pattern",
                "patterns": {
                    "frequency": "daily",
                    "strength": "high"
                }
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = analytics_agent._extract_issues(analytics)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(analytics_agent):
    """Test confidence calculation."""
    analytics = {
        "analytics": {
            "main": {"type": "pattern"},
            "sub": {"type": "segment"}
        },
        "metadata": {
            "version": "1.0",
            "environment": "test"
        }
    }
    
    insights = [
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
    
    confidence = analytics_agent._calculate_confidence(analytics, insights, issues)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Analytics confidence (0.2 from analytics + metadata)
    # - Insight confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(analytics_agent):
    """Test validity determination."""
    analytics = {
        "analytics": {
            "main": {"type": "pattern"}
        },
        "metadata": {
            "version": "1.0"
        }
    }
    
    insights = [
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
    
    is_valid = analytics_agent._determine_validity(analytics, insights, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed insights
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = analytics_agent._determine_validity(analytics, insights, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(analytics_agent):
    """Test error handling during analytics processing."""
    # Make LLM raise an error
    analytics_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await analytics_agent.process_analytics({"content": "test"}, "behavioral")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, AnalyticsResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(analytics_agent):
    """Test domain awareness in analytics processing."""
    content = {"content": "test"}
    result = await analytics_agent.process_analytics(content, "behavioral")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    analytics_agent.domain = "personal"
    result = await analytics_agent.process_analytics(content, "behavioral")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
