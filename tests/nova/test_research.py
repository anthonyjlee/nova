"""Tests for Nova's research analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.research import ResearchAgent, ResearchResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "findings": [
            {
                "statement": "Key research finding",
                "type": "core_finding",
                "description": "Important discovery",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "impact": 0.8,
                "novelty": 0.7,
                "status": "verified"
            }
        ],
        "sources": {
            "similar_memories": [
                {
                    "content": "Related memory",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "references": ["ref1", "ref2"],
            "citations": ["cite1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "quality_factors": [
                {
                    "factor": "reliability",
                    "weight": 0.8
                }
            ]
        }
    })
    return llm

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar content"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    return store

@pytest.fixture
def research_agent(mock_llm, mock_vector_store):
    """Create a ResearchAgent instance with mock dependencies."""
    return ResearchAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=mock_vector_store,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_research_with_llm(research_agent, mock_llm):
    """Test research analysis using LLM."""
    content = {
        "content": "Research content to analyze",
        "type": "research"
    }
    
    result = await research_agent.analyze_research(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, ResearchResult)
    assert len(result.findings) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.sources is not None

@pytest.mark.asyncio
async def test_analyze_research_without_llm():
    """Test research analysis without LLM (fallback mode)."""
    agent = ResearchAgent()  # No LLM provided
    content = {
        "content": "Research shows that this and demonstrates that",
        "context": {"setting": "research"}
    }
    
    result = await agent.analyze_research(content)
    
    # Verify basic analysis worked
    assert isinstance(result, ResearchResult)
    assert len(result.findings) > 0
    assert any(f["type"] == "inferred_finding" for f in result.findings)
    assert result.confidence >= 0
    assert "similar_memories" not in result.sources  # No vector store

@pytest.mark.asyncio
async def test_get_similar_memories(research_agent, mock_vector_store):
    """Test similar memory retrieval."""
    content = {"content": "test content"}
    
    memories = await research_agent._get_similar_memories(content)
    
    # Verify vector store search
    mock_vector_store.search.assert_called_once_with(
        "test content",
        limit=5,
        metadata_filter={"domain": "professional"}
    )
    assert len(memories) == 1
    assert "content" in memories[0]
    assert memories[0]["similarity"] == 0.9

def test_basic_analysis(research_agent):
    """Test basic research analysis without LLM."""
    content = {
        "content": "Research found that X and demonstrates Y",
        "context": {
            "setting": "research"
        }
    }
    
    similar_memories = [
        {
            "content": {"content": "Similar finding"},
            "similarity": 0.8,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    result = research_agent._basic_analysis(content, similar_memories)
    
    assert "findings" in result
    assert "sources" in result
    assert len(result["findings"]) == 2  # "found that" and "demonstrates"
    assert all(f["type"] == "inferred_finding" for f in result["findings"])
    assert "similar_memories" in result["sources"]

def test_extract_findings(research_agent):
    """Test finding extraction and validation."""
    analysis = {
        "findings": [
            {
                "statement": "Valid",
                "type": "core_finding",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "impact": 0.7,
                "novelty": 0.8,
                "status": "verified"
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    findings = research_agent._extract_findings(analysis)
    
    assert len(findings) == 2  # Invalid one should be filtered out
    assert all("type" in f for f in findings)
    assert any(f["type"] == "finding" for f in findings)  # Default type
    assert any("domain_relevance" in f for f in findings)
    assert any("impact" in f for f in findings)

def test_extract_sources(research_agent):
    """Test source extraction and validation."""
    analysis = {
        "sources": {
            "similar_memories": [
                {
                    "content": "memory1",
                    "similarity": 0.8,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "references": ["ref1", "ref2"],
            "citations": ["cite1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "quality_factors": [
                {
                    "factor": "reliability",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    sources = research_agent._extract_sources(analysis)
    
    assert "similar_memories" in sources
    assert "references" in sources
    assert "citations" in sources
    assert "domain_factors" in sources
    assert "quality_factors" in sources
    assert len(sources["references"]) == 2
    assert len(sources["quality_factors"]) == 1
    assert "invalid" not in sources

def test_calculate_confidence(research_agent):
    """Test confidence calculation."""
    findings = [
        {
            "confidence": 0.8,
            "impact": 0.7
        },
        {
            "confidence": 0.6,
            "impact": 0.8
        }
    ]
    
    sources = {
        "similar_memories": [
            {
                "content": "memory1",
                "similarity": 0.8,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ],
        "references": ["ref1", "ref2"],
        "citations": ["cite1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "quality_factors": [
            {
                "factor": "reliability",
                "weight": 0.8
            }
        ]
    }
    
    confidence = research_agent._calculate_confidence(findings, sources)
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Finding confidence (0.7 average)
    # - Similar memories (0.2 from 1 memory)
    # - References (0.3 from 2 references)
    # - Citations (0.1 from 1 citation)
    # - Domain factors (0.2 from 2 factors)
    # - Quality factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

@pytest.mark.asyncio
async def test_error_handling(research_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    research_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await research_agent.analyze_research({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ResearchResult)
    assert result.confidence == 0.0
    assert len(result.findings) == 0
    assert "error" in result.metadata
    assert "error" in result.sources

@pytest.mark.asyncio
async def test_domain_awareness(research_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await research_agent.analyze_research(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    research_agent.domain = "personal"
    result = await research_agent.analyze_research(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
