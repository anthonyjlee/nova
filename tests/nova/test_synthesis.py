"""Tests for Nova's synthesis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.synthesis import SynthesisAgent, SynthesisResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "synthesis": {
            "type": "analysis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content",
                    "themes": ["theme1", "theme2"]
                },
                "sub": {
                    "type": "subsection",
                    "importance": 0.6,
                    "metadata": {
                        "key": "value"
                    }
                }
            },
            "themes": {
                "primary": ["theme1"],
                "secondary": ["theme2"]
            },
            "metadata": {
                "version": "1.0"
            }
        },
        "conclusions": [
            {
                "type": "theme",
                "description": "Theme analysis",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "themes": ["theme1"]
            }
        ],
        "issues": [
            {
                "type": "missing_theme",
                "severity": "medium",
                "description": "Missing theme",
                "domain_impact": 0.3,
                "suggested_fix": "Add theme",
                "related_themes": ["theme3"]
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
            "content": {"content": "Similar synthesis"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def synthesis_agent(mock_llm, mock_vector_store):
    """Create a SynthesisAgent instance with mock dependencies."""
    return SynthesisAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_synthesize_content_with_llm(synthesis_agent, mock_llm):
    """Test content synthesis using LLM."""
    content = {
        "content": "Test content",
        "type": "analysis",
        "metadata": {"key": "value"}
    }
    
    result = await synthesis_agent.synthesize_content(content, "analysis")
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, SynthesisResult)
    assert result.synthesis["type"] == "analysis"
    assert len(result.synthesis["components"]) == 2
    assert len(result.conclusions) == 1
    assert len(result.issues) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata

@pytest.mark.asyncio
async def test_synthesize_content_without_llm():
    """Test content synthesis without LLM (fallback mode)."""
    agent = SynthesisAgent()  # No LLM provided
    content = {
        "insights": ["insight1"],
        "patterns": ["pattern1"],
        "context": {}
    }
    
    result = await agent.synthesize_content(content, "analysis")
    
    # Verify basic synthesis worked
    assert isinstance(result, SynthesisResult)
    assert result.synthesis["type"] == "analysis"
    assert "components" in result.synthesis
    assert result.confidence >= 0
    assert result.is_valid is True  # All basic checks should pass

@pytest.mark.asyncio
async def test_get_similar_syntheses(synthesis_agent, mock_vector_store):
    """Test similar synthesis retrieval."""
    content = {"content": "test content"}
    synthesis_type = "analysis"
    
    syntheses = await synthesis_agent._get_similar_syntheses(content, synthesis_type)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={
            "domain": "professional",
            "type": "synthesis",
            "synthesis_type": "analysis"
        }
    )
    assert len(syntheses) == 1
    assert "content" in syntheses[0]
    assert syntheses[0]["similarity"] == 0.9

def test_basic_synthesis_analysis(synthesis_agent):
    """Test basic analysis synthesis."""
    content = {
        "insights": ["insight1"],
        "patterns": ["pattern1"],
        "context": {}
    }
    
    result = synthesis_agent._basic_synthesis(content, "analysis", [])
    
    assert "synthesis" in result
    assert "conclusions" in result
    assert "issues" in result
    assert result["synthesis"]["type"] == "analysis"
    assert len(result["conclusions"]) > 0
    assert all(c["type"] in ["has_insights", "has_patterns", "has_context"] for c in result["conclusions"])

def test_basic_synthesis_research(synthesis_agent):
    """Test basic research synthesis."""
    content = {
        "findings": ["finding1"],
        "evidence": ["evidence1"],
        "sources": ["source1"]
    }
    
    result = synthesis_agent._basic_synthesis(content, "research", [])
    
    assert "synthesis" in result
    assert "conclusions" in result
    assert "issues" in result
    assert result["synthesis"]["type"] == "research"
    assert len(result["conclusions"]) > 0
    assert all(c["type"] in ["has_findings", "has_evidence", "has_sources"] for c in result["conclusions"])

def test_check_rule(synthesis_agent):
    """Test synthesis rule checking."""
    content = {
        "insights": ["insight1"],
        "patterns": ["pattern1"],
        "context": {},
        "findings": ["finding1"],
        "evidence": ["evidence1"],
        "sources": ["source1"],
        "themes": ["theme1"],
        "flow": {"type": "linear"}
    }
    
    # Test analysis rules
    assert synthesis_agent._check_rule("has_insights", content) is True
    assert synthesis_agent._check_rule("has_patterns", content) is True
    assert synthesis_agent._check_rule("has_context", content) is True
    
    # Test research rules
    assert synthesis_agent._check_rule("has_findings", content) is True
    assert synthesis_agent._check_rule("has_evidence", content) is True
    assert synthesis_agent._check_rule("has_sources", content) is True
    
    # Test dialogue rules
    assert synthesis_agent._check_rule("has_themes", content) is True
    assert synthesis_agent._check_rule("has_flow", content) is True

def test_extract_synthesis(synthesis_agent):
    """Test synthesis extraction and validation."""
    synthesis = {
        "synthesis": {
            "type": "analysis",
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
            "themes": {
                "primary": ["theme1"]
            },
            "metadata": {
                "version": "1.0"
            }
        }
    }
    
    result = synthesis_agent._extract_synthesis(synthesis)
    
    assert result["type"] == "analysis"
    assert len(result["components"]) == 2
    assert result["components"]["main"]["importance"] == 0.8
    assert "description" in result["components"]["main"]
    assert "themes" in result
    assert "metadata" in result

def test_extract_conclusions(synthesis_agent):
    """Test conclusion extraction and validation."""
    synthesis = {
        "conclusions": [
            {
                "type": "theme",
                "description": "Test conclusion",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7,
                "themes": ["theme1"]
            },
            {
                "type": "basic",
                "description": "Basic conclusion",
                "confidence": 0.6
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    conclusions = synthesis_agent._extract_conclusions(synthesis)
    
    assert len(conclusions) == 2  # Invalid one should be filtered out
    assert all("type" in c for c in conclusions)
    assert all("description" in c for c in conclusions)
    assert all("confidence" in c for c in conclusions)
    assert any("domain_relevance" in c for c in conclusions)

def test_extract_issues(synthesis_agent):
    """Test issue extraction and validation."""
    synthesis = {
        "issues": [
            {
                "type": "missing_theme",
                "severity": "high",
                "description": "Missing theme",
                "details": "Details",
                "domain_impact": 0.8,
                "suggested_fix": "Add theme",
                "related_themes": ["theme1"]
            },
            {
                "type": "basic_issue",
                "description": "Basic"
            },
            "Invalid"  # Should be ignored
        ]
    }
    
    issues = synthesis_agent._extract_issues(synthesis)
    
    assert len(issues) == 2  # Invalid one should be filtered out
    assert all("type" in i for i in issues)
    assert all("severity" in i for i in issues)
    assert all("description" in i for i in issues)
    assert any("domain_impact" in i for i in issues)

def test_calculate_confidence(synthesis_agent):
    """Test confidence calculation."""
    synthesis = {
        "components": {
            "main": {"type": "section"},
            "sub": {"type": "subsection"}
        },
        "themes": {
            "primary": ["theme1"],
            "secondary": ["theme2"]
        }
    }
    
    conclusions = [
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
    
    confidence = synthesis_agent._calculate_confidence(synthesis, conclusions, issues)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Synthesis confidence (0.2 from components + themes)
    # - Conclusion confidence (0.7 average)
    # - Issue impact (0.2 from low + medium severity)
    assert 0.45 <= confidence <= 0.55

def test_determine_validity(synthesis_agent):
    """Test validity determination."""
    synthesis = {
        "components": {
            "main": {"type": "section"}
        },
        "themes": {
            "primary": ["theme1"]
        }
    }
    
    conclusions = [
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
    
    is_valid = synthesis_agent._determine_validity(synthesis, conclusions, issues, 0.7)
    assert is_valid is True  # High confidence, mostly passed conclusions
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = synthesis_agent._determine_validity(synthesis, conclusions, issues, 0.7)
    assert is_valid is False  # Critical issue should fail validation

@pytest.mark.asyncio
async def test_error_handling(synthesis_agent):
    """Test error handling during synthesis."""
    # Make LLM raise an error
    synthesis_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await synthesis_agent.synthesize_content({"content": "test"}, "analysis")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, SynthesisResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.conclusions) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata

@pytest.mark.asyncio
async def test_domain_awareness(synthesis_agent):
    """Test domain awareness in synthesis."""
    content = {"content": "test"}
    result = await synthesis_agent.synthesize_content(content, "analysis")
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    synthesis_agent.domain = "personal"
    result = await synthesis_agent.synthesize_content(content, "analysis")
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
