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
    assert isinstance(result, ResearchResult), "Result should be a ResearchResult instance"
    
    # Verify findings
    assert isinstance(result.findings, list), "Findings should be a list"
    assert len(result.findings) >= 1, "Should have at least one finding"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify metadata and sources
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "domain" in result.metadata and result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional'"
    assert result.sources is not None and isinstance(result.sources, dict), \
        "Sources should be a non-null dictionary"

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
    assert isinstance(result, ResearchResult), "Result should be a ResearchResult instance"
    
    # Verify findings
    assert isinstance(result.findings, list), "Findings should be a list"
    assert len(result.findings) >= 1, "Should have at least one finding"
    assert any(f["type"] == "inferred_finding" for f in result.findings), \
        "Should have at least one inferred finding"
    
    # Verify confidence
    assert isinstance(result.confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= result.confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify sources without vector store
    assert isinstance(result.sources, dict), "Sources should be a dictionary"
    assert "similar_memories" not in result.sources, \
        "Should not have similar_memories without vector store"

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
    # Verify we got memories back
    assert isinstance(memories, list), "Should return a list of memories"
    assert len(memories) >= 1, "Should have at least one memory"
    
    # Verify memory structure
    memory = memories[0]
    assert isinstance(memory, dict), "Each memory should be a dictionary"
    assert "content" in memory, "Each memory should have content"
    assert isinstance(memory.get("similarity", 0.0), (int, float)), \
        "Similarity should be numeric"
    assert 0 <= memory.get("similarity", 0.0) <= 1, \
        "Similarity should be between 0 and 1"

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
    
    # Verify basic structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "findings" in result, "Result should contain findings"
    assert "sources" in result, "Result should contain sources"
    
    # Verify findings
    assert isinstance(result["findings"], list), "Findings should be a list"
    assert len(result["findings"]) >= 1, "Should have at least one finding"
    assert all(f["type"] == "inferred_finding" for f in result["findings"]), \
        "Each finding should be of type inferred_finding"
    
    # Verify sources
    assert isinstance(result["sources"], dict), "Sources should be a dictionary"
    assert "similar_memories" in result["sources"], \
        "Sources should contain similar_memories from input"

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
    
    # Verify we got valid findings (filtering out invalid ones)
    assert len(findings) >= 1, "Should have at least one valid finding"
    
    # Verify each finding has required fields
    for finding in findings:
        assert isinstance(finding, dict), "Each finding should be a dictionary"
        assert "type" in finding, "Each finding should have a type"
        assert isinstance(finding.get("confidence", 0.0), (int, float)), \
            "Confidence should be numeric"
        assert 0 <= finding.get("confidence", 0.0) <= 1, \
            "Confidence should be between 0 and 1"
    
    # Verify finding types
    assert any(f["type"] == "finding" for f in findings), \
        "Should have at least one default 'finding' type"
    
    # Verify at least one finding has extended fields
    assert any("domain_relevance" in f or "impact" in f for f in findings), \
        "At least one finding should have domain_relevance or impact"

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
    
    # Verify basic structure
    assert isinstance(sources, dict), "Sources should be a dictionary"
    
    # Verify required fields are present
    required_fields = ["similar_memories", "references", "citations", "domain_factors", "quality_factors"]
    for field in required_fields:
        assert field in sources, f"Sources should contain {field}"
    
    # Verify field contents
    assert isinstance(sources["references"], list), "References should be a list"
    assert len(sources["references"]) >= 1, "Should have at least one reference"
    
    assert isinstance(sources["quality_factors"], list), "Quality factors should be a list"
    assert len(sources["quality_factors"]) >= 1, "Should have at least one quality factor"
    
    assert isinstance(sources["domain_factors"], dict), "Domain factors should be a dictionary"
    assert len(sources["domain_factors"]) >= 1, "Should have at least one domain factor"
    
    # Verify invalid fields are filtered out
    assert "invalid" not in sources, "Invalid fields should be filtered out"

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
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Verify confidence calculation is reasonable
    # Given high confidence findings (0.8, 0.6), multiple references,
    # and good quality factors, confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"

@pytest.mark.asyncio
async def test_error_handling(research_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    research_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await research_agent.analyze_research({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, ResearchResult), "Result should be a ResearchResult instance"
    assert result.confidence == 0.0, "Confidence should be 0.0 when error occurs"
    assert len(result.findings) == 0, "Should have no findings when error occurs"
    
    # Verify error state
    assert isinstance(result.metadata, dict), "Metadata should be a dictionary"
    assert "error" in result.metadata, "Metadata should contain error information"
    assert isinstance(result.metadata["error"], str), "Error should be a string message"
    
    assert isinstance(result.sources, dict), "Sources should be a dictionary"
    assert "error" in result.sources, "Sources should contain error information"

@pytest.mark.asyncio
async def test_domain_awareness(research_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await research_agent.analyze_research(content)
    
    # Verify domain is included and correct
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "professional", \
        "Domain should be set to 'professional' initially"
    
    # Test with different domain
    research_agent.domain = "personal"
    result = await research_agent.analyze_research(content)
    
    # Verify domain was updated
    assert isinstance(result.metadata, dict), "Result should have metadata dictionary"
    assert "domain" in result.metadata, "Metadata should include domain"
    assert result.metadata["domain"] == "personal", \
        "Domain should be updated to 'personal'"

if __name__ == "__main__":
    pytest.main([__file__])
