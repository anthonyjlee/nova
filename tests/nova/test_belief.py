"""Tests for Nova's belief analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.belief import BeliefAgent, BeliefResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "beliefs": [
            {
                "statement": "This is important",
                "type": "core_belief",
                "description": "A fundamental belief",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "certainty": 0.7,
                "impact": 0.8
            }
        ],
        "evidence": {
            "sources": ["document1", "document2"],
            "context": "Professional setting",
            "supporting_facts": [
                "Fact 1 supports this",
                "Fact 2 confirms this"
            ],
            "contradictions": [],
            "domain_factors": {
                "relevance": "high",
                "applicability": "direct"
            }
        }
    })
    return llm

@pytest.fixture
def belief_agent(mock_llm):
    """Create a BeliefAgent instance with mock dependencies."""
    return BeliefAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock(),
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_beliefs_with_llm(belief_agent, mock_llm):
    """Test belief analysis using LLM."""
    content = {
        "content": "I believe this is important",
        "type": "statement"
    }
    
    result = await belief_agent.analyze_beliefs(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, BeliefResult)
    assert len(result.beliefs) == 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata
    assert result.evidence is not None

@pytest.mark.asyncio
async def test_analyze_beliefs_without_llm():
    """Test belief analysis without LLM (fallback mode)."""
    agent = BeliefAgent()  # No LLM provided
    content = {
        "content": "I think this is important and I believe it will work",
        "context": {"setting": "meeting"}
    }
    
    result = await agent.analyze_beliefs(content)
    
    # Verify basic analysis worked
    assert isinstance(result, BeliefResult)
    assert len(result.beliefs) > 0
    assert any(b["type"] == "inferred_belief" for b in result.beliefs)
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "context" in result.evidence

def test_basic_analysis(belief_agent):
    """Test basic belief analysis without LLM."""
    content = {
        "content": "I think this is good and I believe it will help",
        "context": {
            "setting": "discussion"
        }
    }
    
    result = belief_agent._basic_analysis(content)
    
    assert "beliefs" in result
    assert "evidence" in result
    assert len(result["beliefs"]) == 2  # "I think" and "I believe"
    assert all(b["type"] == "inferred_belief" for b in result["beliefs"])

def test_extract_beliefs(belief_agent):
    """Test belief extraction and validation."""
    analysis = {
        "beliefs": [
            {
                "statement": "Valid",
                "type": "core_belief",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "certainty": 0.7,
                "impact": 0.8
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    beliefs = belief_agent._extract_beliefs(analysis)
    
    assert len(beliefs) == 2  # Invalid one should be filtered out
    assert all("type" in b for b in beliefs)
    assert any(b["type"] == "belief" for b in beliefs)  # Default type
    assert any("domain_relevance" in b for b in beliefs)
    assert any("certainty" in b for b in beliefs)
    assert all("confidence" in b for b in beliefs)
    assert all(isinstance(b["confidence"], (int, float)) for b in beliefs)
    assert all(0 <= b["confidence"] <= 1 for b in beliefs)

def test_extract_evidence(belief_agent):
    """Test evidence extraction and validation."""
    analysis = {
        "evidence": {
            "sources": ["source1", "source2"],
            "context": "test context",
            "supporting_facts": ["fact1", "fact2"],
            "contradictions": ["contra1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "invalid": object()  # Should be ignored
        }
    }
    
    evidence = belief_agent._extract_evidence(analysis)
    
    assert "sources" in evidence
    assert "context" in evidence
    assert "supporting_facts" in evidence
    assert "contradictions" in evidence
    assert "domain_factors" in evidence
    assert len(evidence["sources"]) == 2
    assert len(evidence["supporting_facts"]) == 2
    assert "invalid" not in evidence

def test_calculate_confidence(belief_agent):
    """Test confidence calculation."""
    beliefs = [
        {
            "confidence": 0.8,
            "certainty": 0.7
        },
        {
            "confidence": 0.6,
            "certainty": 0.8
        }
    ]
    
    evidence = {
        "supporting_facts": ["fact1", "fact2"],
        "contradictions": ["contra1"],
        "sources": ["source1", "source2", "source3"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        }
    }
    
    confidence = belief_agent._calculate_confidence(beliefs, evidence)
    
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    # Should include:
    # - Belief confidence (0.7 average)
    # - Supporting facts (0.2 from 2 facts)
    # - Contradictions (0.8 from 1 contradiction)
    # - Sources (0.45 from 3 sources)
    # - Domain factors (0.2 from 2 factors)
    assert 0.65 <= confidence <= 0.75

@pytest.mark.asyncio
async def test_error_handling(belief_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    belief_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await belief_agent.analyze_beliefs({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, BeliefResult)
    assert result.confidence == 0.0
    assert len(result.beliefs) == 0
    assert "error" in result.metadata
    assert "error" in result.evidence

@pytest.mark.asyncio
async def test_domain_awareness(belief_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await belief_agent.analyze_beliefs(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    belief_agent.domain = "personal"
    result = await belief_agent.analyze_beliefs(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
