"""Tests for Nova's analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.analysis import AnalysisAgent, AnalysisResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "analysis": {
            "type": "text",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content",
                    "patterns": ["pattern1", "pattern2"]
                },
                "sub": {
                    "type": "subsection",
                    "importance": 0.6,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "patterns": {
                "structure": ["pattern1"],
                "content": ["pattern2"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "insights": [
            {
                "type": "structure",
                "description": "Content structure analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "patterns": ["pattern1"]
            }
        ],
        "issues": [
            {
                "type": "missing_pattern",
                "severity": "medium",
                "description": "Missing pattern",
                "domain_impact": 0.3,
                "suggested_fix": "Add pattern",
                "related_patterns": ["pattern3"]
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
            "content": {"content": "Similar analysis"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def analysis_agent(mock_llm, mock_vector_store):
    """Create an AnalysisAgent instance with mock dependencies."""
    return AnalysisAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_content_with_llm(analysis_agent, mock_llm):
    """Test content analysis using LLM."""
    content = {
        "content": "Test content",
        "type": "text",
        "metadata": {"key": "value"}
    }
    
    result = await analysis_agent.analyze_content(content, "text")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, AnalysisResult)
    assert result.analysis["type"] == "text"
    assert len(result.analysis["components"]) == 2
    assert len(result.insights) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_analyze_content_without_llm():
    """Test content analysis without LLM (fallback mode)."""
    agent = AnalysisAgent()  # No LLM provided
    content = {
        "content": "test",
        "type": "text",
        "metadata": {}
    }
    
    result = await agent.analyze_content(content, "text")
    
    # Verify basic analysis worked
    assert isinstance(result, AnalysisResult)
    assert result.analysis["type"] == "text"
    assert "components" in result.analysis
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_analyses(analysis_agent, mock_vector_store):
    """Test similar analysis retrieval."""
    content = {"content": "test content"}
    analysis_type = "text"
    
    analyses = await analysis_agent._get_similar_analyses(content, analysis_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "analysis",
            "analysis_type": "text"
        }
    )
    assert len(analyses) == 1
    assert "content" in analyses[0]
    assert analyses[0]["similarity"] == 0.9

def test_basic_analysis_text(analysis_agent):
    """Test basic text analysis."""
    content = {
        "content": "test",
        "structure": {},
        "metadata": {}
    }
    
    result = analysis_agent._basic_analysis(content, "text", [])
    
    assert "analysis" in result
    assert "insights" in result
    assert "issues" in result
    assert result["analysis"]["type"] == "text"
    assert len(result["insights"]) > 0
    assert all(i["type"] in ["has_content", "has_structure", "has_metadata"] for i in result["insights"])

def test_basic_analysis_data(analysis_agent):
    """Test basic data analysis."""
    content = {
        "fields": {
            "name": {"type": "string", "value": "test"},
            "age": {"type": "integer", "value": 30}
        }
    }
    
    result = analysis_agent._basic_analysis(content, "data", [])
    
    assert "analysis" in result
    assert "insights" in result
    assert "issues" in result
    assert result["analysis"]["type"] == "data"
    assert len(result["insights"]) > 0
    assert all(i["type"] in ["has_fields", "has_values", "has_types"] for i in result["insights"])

def test_check_rule(analysis_agent):
    """Test analysis rule checking."""
    content = {
        "content": "test",
        "structure": {"type": "section"},
        "metadata": {"key": "value"},
        "fields": {
            "name": {"type": "string", "value": "test"}
        },
        "syntax": {"type": "code"},
        "patterns": ["pattern1"]
    }
    
    # Test text rules
    assert analysis_agent._check_rule("has_content", content) is True
    assert analysis_agent._check_rule("has_structure", content) is True
    assert analysis_agent._check_rule("has_metadata", content) is True
    
    # Test data rules
    assert analysis_agent._check_rule("has_fields", content) is True
    assert analysis_agent._check_rule("has_values", content) is True
    assert analysis_agent._check_rule("has_types", content) is True
    
    # Test code rules
    assert analysis_agent._check_rule("has_syntax", content) is True
    assert analysis_agent._check_rule("has_patterns", content) is True

def test_extract_analysis(analysis_agent):
    """Test analysis extraction and validation."""
    analysis = {
        "analysis": {
            "type": "text",
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
            "patterns": {
                "structure": ["pattern1"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = analysis_agent._extract_analysis(analysis)
    
    assert result["type"] == "text"
    assert len(result["components"]) == 2
    assert result["components"]["main"]["importance"] == 0.8
    assert "description" in result["components"]["main"]
    assert "patterns" in result
    assert "metadata" in result

def test_extract_insights(analysis_agent):
    """Test insight extraction and validation."""
    analysis = {
        "insights": [
            {
                "type": "structure",
                "description": "Test insight",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "patterns": ["pattern1"]
            },
            {
                "type": "basic",
                "description": "Basic insight",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    insights = analysis_agent._extract_insights(analysis)
    
    assert len(insights) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in insights)
    assert all("description" in i for i in insights)
    assert all("confidence" in i for i in insights)
    assert any("domain_relevance" in i for i in insights)

def test_extract_issues(analysis_agent):
    """Test issue extraction and validation."""
    analysis = {
        "issues": [
            {
                "type": "missing_pattern",
                "severity": "high",
                "description": "Missing pattern",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add pattern",
                "related_patterns": ["pattern1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = analysis_agent._extract_issues(analysis)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(analysis_agent):
    """Test confidence calculation."""
    analysis = {
        "components": {
            "main": {"type": "section"},
            "sub": {"type": "subsection"}
        },
        "patterns": {
            "structure": ["pattern1"],
            "content": ["pattern2"]
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
    
    confidence = analysis_agent._calculate_confidence(analysis, insights, issues)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Analysis confidence (0.2 from components + patterns)
    # - Insight confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(analysis_agent):
    """Test validity determination."""
    analysis = {
        "components": {
            "main": {"type": "section"}
        },
        "patterns": {
            "structure": ["pattern1"]
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
    
    is_valid = analysis_agent._determine_validity(analysis, insights, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed insights
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = analysis_agent._determine_validity(analysis, insights, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(analysis_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    analysis_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await analysis_agent.analyze_content({"content": "test"}, "text")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, AnalysisResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(analysis_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await analysis_agent.analyze_content(content, "text")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    analysis_agent.domain = "personal"
    result = await analysis_agent.analyze_content(content, "text")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
