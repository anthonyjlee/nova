"""Tests for Nova's integration functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.integration import IntegrationAgent, IntegrationResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content",
                    "connections": ["conn1", "conn2"]
                },
                "sub": {
                    "type": "subsection",
                    "importance": 0.6,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "connections": {
                "primary": ["conn1"],
                "secondary": ["conn2"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "insights": [
            {
                "type": "connection",
                "description": "Connection analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "connections": ["conn1"]
            }
        ],
        "issues": [
            {
                "type": "missing_connection",
                "severity": "medium",
                "description": "Missing connection",
                "domain_impact": 0.3,
                "suggested_fix": "Add connection",
                "related_connections": ["conn3"]
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
            "content": {"content": "Similar integration"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def integration_agent(mock_llm, mock_vector_store):
    """Create an IntegrationAgent instance with mock dependencies."""
    return IntegrationAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_integrate_content_with_llm(integration_agent, mock_llm):
    """Test content integration using LLM."""
    content = {
        "content": "Test content",
        "type": "synthesis",
        "metadata": {"key": "value"}
    }
    
    result = await integration_agent.integrate_content(content, "synthesis")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, IntegrationResult)
    assert result.integration["type"] == "synthesis"
    assert len(result.integration["components"]) == 2
    assert len(result.insights) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_integrate_content_without_llm():
    """Test content integration without LLM (fallback mode)."""
    agent = IntegrationAgent()  # No LLM provided
    content = {
        "conclusions": ["conclusion1"],
        "themes": ["theme1"],
        "context": {}
    }
    
    result = await agent.integrate_content(content, "synthesis")
    
    # Verify basic integration worked
    assert isinstance(result, IntegrationResult)
    assert result.integration["type"] == "synthesis"
    assert "components" in result.integration
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_integrations(integration_agent, mock_vector_store):
    """Test similar integration retrieval."""
    content = {"content": "test content"}
    integration_type = "synthesis"
    
    integrations = await integration_agent._get_similar_integrations(content, integration_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "integration",
            "integration_type": "synthesis"
        }
    )
    assert len(integrations) == 1
    assert "content" in integrations[0]
    assert integrations[0]["similarity"] == 0.9

def test_basic_integration_synthesis(integration_agent):
    """Test basic synthesis integration."""
    content = {
        "conclusions": ["conclusion1"],
        "themes": ["theme1"],
        "context": {}
    }
    
    result = integration_agent._basic_integration(content, "synthesis", [])
    
    assert "integration" in result
    assert "insights" in result
    assert "issues" in result
    assert result["integration"]["type"] == "synthesis"
    assert len(result["insights"]) > 0
    assert all(i["type"] in ["has_conclusions", "has_themes", "has_context"] for i in result["insights"])

def test_basic_integration_analysis(integration_agent):
    """Test basic analysis integration."""
    content = {
        "insights": ["insight1"],
        "patterns": ["pattern1"],
        "evidence": ["evidence1"]
    }
    
    result = integration_agent._basic_integration(content, "analysis", [])
    
    assert "integration" in result
    assert "insights" in result
    assert "issues" in result
    assert result["integration"]["type"] == "analysis"
    assert len(result["insights"]) > 0
    assert all(i["type"] in ["has_insights", "has_patterns", "has_evidence"] for i in result["insights"])

def test_check_rule(integration_agent):
    """Test integration rule checking."""
    content = {
        "conclusions": ["conclusion1"],
        "themes": ["theme1"],
        "context": {},
        "insights": ["insight1"],
        "patterns": ["pattern1"],
        "evidence": ["evidence1"],
        "findings": ["finding1"],
        "sources": ["source1"],
        "validation": {"type": "complete"}
    }
    
    # Test synthesis rules
    assert integration_agent._check_rule("has_conclusions", content) is True
    assert integration_agent._check_rule("has_themes", content) is True
    assert integration_agent._check_rule("has_context", content) is True
    
    # Test analysis rules
    assert integration_agent._check_rule("has_insights", content) is True
    assert integration_agent._check_rule("has_patterns", content) is True
    assert integration_agent._check_rule("has_evidence", content) is True
    
    # Test research rules
    assert integration_agent._check_rule("has_findings", content) is True
    assert integration_agent._check_rule("has_sources", content) is True
    assert integration_agent._check_rule("has_validation", content) is True

def test_extract_integration(integration_agent):
    """Test integration extraction and validation."""
    integration = {
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content"
                },
                "sub": {
                    "type": "subsection",
                    "importance": 0.6
                }
            },
            "connections": {
                "primary": ["conn1"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = integration_agent._extract_integration(integration)
    
    assert result["type"] == "synthesis"
    assert len(result["components"]) == 2
    assert result["components"]["main"]["importance"] == 0.8
    assert "description" in result["components"]["main"]
    assert "connections" in result
    assert "metadata" in result

def test_extract_insights(integration_agent):
    """Test insight extraction and validation."""
    integration = {
        "insights": [
            {
                "type": "connection",
                "description": "Test insight",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "connections": ["conn1"]
            },
            {
                "type": "basic",
                "description": "Basic insight",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    insights = integration_agent._extract_insights(integration)
    
    assert len(insights) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in insights)
    assert all("description" in i for i in insights)
    assert all("confidence" in i for i in insights)
    assert any("domain_relevance" in i for i in insights)

def test_extract_issues(integration_agent):
    """Test issue extraction and validation."""
    integration = {
        "issues": [
            {
                "type": "missing_connection",
                "severity": "high",
                "description": "Missing connection",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add connection",
                "related_connections": ["conn1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = integration_agent._extract_issues(integration)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(integration_agent):
    """Test confidence calculation."""
    integration = {
        "components": {
            "main": {"type": "section"},
            "sub": {"type": "subsection"}
        },
        "connections": {
            "primary": ["conn1"],
            "secondary": ["conn2"]
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
    
    confidence = integration_agent._calculate_confidence(integration, insights, issues)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Integration confidence (0.2 from components + connections)
    # - Insight confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(integration_agent):
    """Test validity determination."""
    integration = {
        "components": {
            "main": {"type": "section"}
        },
        "connections": {
            "primary": ["conn1"]
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
    
    is_valid = integration_agent._determine_validity(integration, insights, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed insights
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = integration_agent._determine_validity(integration, insights, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(integration_agent):
    """Test error handling during integration."""
    # Make LLM raise an error
    integration_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await integration_agent.integrate_content({"content": "test"}, "synthesis")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, IntegrationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(integration_agent):
    """Test domain awareness in integration."""
    content = {"content": "test"}
    result = await integration_agent.integrate_content(content, "synthesis")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    integration_agent.domain = "personal"
    result = await integration_agent.integrate_content(content, "synthesis")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
