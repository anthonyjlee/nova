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
    assert isinstance(result, SynthesisResult), "Result should be a SynthesisResult instance"
    
    # Verify synthesis
    assert isinstance(result.synthesis, dict), "Synthesis should be a dictionary"
    assert result.synthesis["type"] == "analysis", "Type should be 'analysis'"
    assert len(result.synthesis["components"]) >= 1, "Should have at least one component"
    
    # Verify conclusions and issues
    assert len(result.conclusions) >= 1, "Should have at least one conclusion"
    assert len(result.issues) >= 0, "Should have zero or more issues"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata and result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"

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
    assert isinstance(result, SynthesisResult), "Result should be a SynthesisResult instance"
    
    # Verify synthesis structure
    assert isinstance(result.synthesis, dict), "Synthesis should be a dictionary"
    assert result.synthesis["type"] == "analysis", "Type should be 'analysis'"
    assert "components" in result.synthesis, "Synthesis should have components"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify validity
    assert result.is_valid is True, "Result should be valid with basic content"
    assert isinstance(result.conclusions, list), "Should have conclusions list"
    assert isinstance(result.issues, list), "Should have issues list"

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
    # Verify we got syntheses back
    assert isinstance(syntheses, list), "Should return a list of syntheses"
    assert len(syntheses) >= 1, "Should have at least one synthesis"
    
    # Verify synthesis structure
    synthesis = syntheses[0]
    assert isinstance(synthesis, dict), "Each synthesis should be a dictionary"
    assert "content" in synthesis, "Each synthesis should have content"
    assert isinstance(synthesis.get("similarity", 0.0), (int, float)), \
        "Similarity should be numeric"
    assert 0 <= synthesis.get("similarity", 0.0) <= 1, \
        "Similarity should be between 0 and 1"

def test_basic_synthesis_analysis(synthesis_agent):
    """Test basic analysis synthesis."""
    content = {
        "insights": ["insight1"],
        "patterns": ["pattern1"],
        "context": {}
    }
    
    result = synthesis_agent._basic_synthesis(content, "analysis", [])
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "synthesis" in result, "Result should contain synthesis"
    assert "conclusions" in result, "Result should contain conclusions"
    assert "issues" in result, "Result should contain issues"
    
    # Verify synthesis
    assert isinstance(result["synthesis"], dict), "Synthesis should be a dictionary"
    assert result["synthesis"]["type"] == "analysis", "Type should be 'analysis'"
    
    # Verify conclusions
    assert len(result["conclusions"]) >= 1, "Should have at least one conclusion"
    assert all(c["type"] in ["has_insights", "has_patterns", "has_context"] for c in result["conclusions"]), \
        "Each conclusion should have a valid analysis type"

def test_basic_synthesis_research(synthesis_agent):
    """Test basic research synthesis."""
    content = {
        "findings": ["finding1"],
        "evidence": ["evidence1"],
        "sources": ["source1"]
    }
    
    result = synthesis_agent._basic_synthesis(content, "research", [])
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "synthesis" in result, "Result should contain synthesis"
    assert "conclusions" in result, "Result should contain conclusions"
    assert "issues" in result, "Result should contain issues"
    
    # Verify synthesis
    assert isinstance(result["synthesis"], dict), "Synthesis should be a dictionary"
    assert result["synthesis"]["type"] == "research", "Type should be 'research'"
    
    # Verify conclusions
    assert len(result["conclusions"]) >= 1, "Should have at least one conclusion"
    assert all(c["type"] in ["has_findings", "has_evidence", "has_sources"] for c in result["conclusions"]), \
        "Each conclusion should have a valid research type"

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
    for rule in ["has_insights", "has_patterns", "has_context"]:
        assert synthesis_agent._check_rule(rule, content) is True, \
            f"Analysis rule '{rule}' should pass with valid content"
    
    # Test research rules
    for rule in ["has_findings", "has_evidence", "has_sources"]:
        assert synthesis_agent._check_rule(rule, content) is True, \
            f"Research rule '{rule}' should pass with valid content"
    
    # Test dialogue rules
    for rule in ["has_themes", "has_flow"]:
        assert synthesis_agent._check_rule(rule, content) is True, \
            f"Dialogue rule '{rule}' should pass with valid content"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "type" in result, "Result should have a type"
    assert result["type"] == "analysis", "Type should be 'analysis'"
    
    # Verify components
    assert "components" in result, "Result should have components"
    assert len(result["components"]) >= 1, "Should have at least one component"
    
    # Verify component structure
    main_component = result["components"].get("main")
    assert isinstance(main_component, dict), "Main component should be a dictionary"
    assert "type" in main_component, "Component should have a type"
    assert isinstance(main_component.get("importance", 0.0), (int, float)), \
        "Importance should be numeric"
    assert "description" in main_component, "Component should have a description"
    
    # Verify additional fields
    assert "themes" in result, "Result should have themes"
    assert "metadata" in result, "Result should have metadata"

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
    
    # Verify we got valid conclusions (filtering out invalid ones)
    assert len(conclusions) >= 1, "Should have at least one valid conclusion"
    
    # Verify each conclusion has required fields
    for conclusion in conclusions:
        assert isinstance(conclusion, dict), "Each conclusion should be a dictionary"
        assert "type" in conclusion, "Each conclusion should have a type"
        assert "description" in conclusion, "Each conclusion should have a description"
        assert isinstance(conclusion.get("confidence", 0.0), (int, float)), \
            "Confidence should be numeric"
        assert 0 <= conclusion.get("confidence", 0.0) <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify at least one conclusion has extended fields
    assert any("domain_relevance" in c for c in conclusions), \
        "At least one conclusion should have domain_relevance"

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
    
    # Verify we got valid issues (filtering out invalid ones)
    assert len(issues) >= 1, "Should have at least one valid issue"
    
    # Verify each issue has required fields
    for issue in issues:
        assert isinstance(issue, dict), "Each issue should be a dictionary"
        assert "type" in issue, "Each issue should have a type"
        assert "severity" in issue, "Each issue should have a severity"
        assert "description" in issue, "Each issue should have a description"
    
    # Verify at least one issue has extended fields
    assert any("domain_impact" in i or "suggested_fix" in i for i in issues), \
        "At least one issue should have domain_impact or suggested_fix"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given rich synthesis structure, high confidence conclusions, and minor issues
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"

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
    
    # Test with no critical issues
    is_valid = synthesis_agent._determine_validity(synthesis, conclusions, issues, 0.7)
    assert is_valid is True, \
        "Should be valid with high confidence conclusions and no critical issues"
    
    # Test with critical issue
    issues.append({
        "severity": "high",
        "type": "critical"
    })
    
    is_valid = synthesis_agent._determine_validity(synthesis, conclusions, issues, 0.7)
    assert is_valid is False, \
        "Should be invalid with critical issue regardless of confidence"

@pytest.mark.asyncio
async def test_error_handling(synthesis_agent):
    """Test error handling during synthesis."""
    # Make LLM raise an error
    synthesis_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await synthesis_agent.synthesize_content({"content": "test"}, "analysis")
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, SynthesisResult), "Result should be a SynthesisResult instance"
    assert result.is_valid is False, "Result should be invalid when error occurs"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    
    # Verify error state
    assert len(result.conclusions) == 0, "Should have no conclusions when error occurs"
    assert len(result.issues) >= 1, "Should have at least one issue indicating the error"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"

@pytest.mark.asyncio
async def test_domain_awareness(synthesis_agent):
    """Test domain awareness in synthesis."""
    content = {"content": "test"}
    result = await synthesis_agent.synthesize_content(content, "analysis")
    
    # Verify domain is included and correct
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test with different domain
    synthesis_agent.domain = "personal"
    result = await synthesis_agent.synthesize_content(content, "analysis")
    
    # Verify domain was updated
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"

if __name__ == "__main__":
    pytest.main([__file__])
