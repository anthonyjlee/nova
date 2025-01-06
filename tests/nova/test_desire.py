"""Tests for Nova's desire analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.desire import DesireAgent, DesireResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "statement": "Achieve this goal",
                "type": "core_desire",
                "description": "Primary objective",
                "confidence": 0.8,
                "source": "analysis",
                "domain_relevance": 0.9,
                "priority": 0.8,
                "achievability": 0.7
            }
        ],
        "motivations": {
            "reasons": ["reason1", "reason2"],
            "drivers": ["driver1"],
            "constraints": ["constraint1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ]
        }
    })
    return llm

@pytest.fixture
def desire_agent(mock_llm):
    """Create a DesireAgent instance with mock dependencies."""
    return DesireAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock(),
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_desires_with_llm(desire_agent, mock_llm):
    """Test desire analysis using LLM."""
    content = {
        "content": "I want to achieve this goal",
        "type": "statement"
    }
    
    result = await desire_agent.analyze_desires(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, DesireResult)
    assert len(result.desires) >= 1  # At least one desire should be found
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    # Verify domain and motivations are present
    assert "domain" in result.metadata and result.metadata["domain"] == "professional"
    assert result.motivations is not None and isinstance(result.motivations, dict)

@pytest.mark.asyncio
async def test_analyze_desires_without_llm():
    """Test desire analysis without LLM (fallback mode)."""
    agent = DesireAgent()  # No LLM provided
    content = {
        "content": "I want to achieve this and I need to complete that",
        "context": {"setting": "meeting"}
    }
    
    result = await agent.analyze_desires(content)
    
    # Verify basic analysis worked
    assert isinstance(result, DesireResult)
    assert len(result.desires) > 0
    assert any(d["type"] == "inferred_desire" for d in result.desires)
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    # Verify no explicit reason since there's no "because" in text
    assert "explicit_reason" not in result.motivations or result.motivations["explicit_reason"] is None

def test_basic_analysis(desire_agent):
    """Test basic desire analysis without LLM."""
    content = {
        "content": "I want to do this and I need to do that because it's important",
        "context": {
            "setting": "discussion"
        }
    }
    
    result = desire_agent._basic_analysis(content)
    
    assert "desires" in result
    assert "motivations" in result
    assert len(result["desires"]) >= 1  # At least one desire should be found
    assert all(d["type"] == "inferred_desire" for d in result["desires"])
    # Verify explicit reason is present since text contains "because"
    assert "explicit_reason" in result["motivations"] and result["motivations"]["explicit_reason"] is not None

def test_extract_desires(desire_agent):
    """Test desire extraction and validation."""
    analysis = {
        "desires": [
            {
                "statement": "Valid",
                "type": "core_desire",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "priority": 0.7,
                "achievability": 0.8
            },
            {
                "statement": "Basic",
                "confidence": 0.6  # Missing type should get default
            },
            "Invalid"  # Not a dict, should be ignored
        ]
    }
    
    desires = desire_agent._extract_desires(analysis)
    
    # Verify we got valid desires (filtering out invalid ones)
    assert len(desires) >= 1, "Should have at least one valid desire"
    
    # Verify each desire has required fields
    for desire in desires:
        assert isinstance(desire, dict), "Each desire should be a dictionary"
        assert "type" in desire, "Each desire should have a type"
        assert isinstance(desire.get("confidence", 0.0), (int, float)), "Confidence should be numeric"
        assert 0 <= desire.get("confidence", 0.0) <= 1, "Confidence should be between 0 and 1"
    
    # Verify at least one desire has extended fields
    assert any("domain_relevance" in d or "priority" in d for d in desires), \
        "At least one desire should have domain_relevance or priority"

def test_extract_motivations(desire_agent):
    """Test motivation extraction and validation."""
    analysis = {
        "motivations": {
            "reasons": ["reason1", "reason2"],
            "drivers": ["driver1"],
            "constraints": ["constraint1"],
            "domain_factors": {
                "relevance": "high",
                "impact": "medium"
            },
            "priority_factors": [
                {
                    "factor": "urgency",
                    "weight": 0.8
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    motivations = desire_agent._extract_motivations(analysis)
    
    # Verify required motivation fields are present
    assert isinstance(motivations, dict), "Motivations should be a dictionary"
    assert all(field in motivations for field in ["reasons", "drivers", "constraints", "domain_factors", "priority_factors"]), \
        "All required motivation fields should be present"
    
    # Verify field types and non-empty content
    assert isinstance(motivations["reasons"], list), "Reasons should be a list"
    assert isinstance(motivations["drivers"], list), "Drivers should be a list"
    assert isinstance(motivations["constraints"], list), "Constraints should be a list"
    assert isinstance(motivations["domain_factors"], dict), "Domain factors should be a dictionary"
    assert isinstance(motivations["priority_factors"], list), "Priority factors should be a list"
    
    # Verify at least some content is present
    assert any([
        len(motivations["reasons"]) > 0,
        len(motivations["drivers"]) > 0,
        len(motivations["constraints"]) > 0,
        len(motivations["domain_factors"]) > 0,
        len(motivations["priority_factors"]) > 0
    ]), "At least one motivation field should have content"
    
    # Verify invalid fields are filtered out
    assert "invalid" not in motivations, "Invalid fields should be filtered out"

def test_calculate_confidence(desire_agent):
    """Test confidence calculation."""
    desires = [
        {
            "confidence": 0.8,
            "priority": 0.7
        },
        {
            "confidence": 0.6,
            "priority": 0.8
        }
    ]
    
    motivations = {
        "reasons": ["reason1", "reason2"],
        "drivers": ["driver1"],
        "constraints": ["constraint1"],
        "domain_factors": {
            "factor1": "value1",
            "factor2": "value2"
        },
        "priority_factors": [
            {
                "factor": "urgency",
                "weight": 0.8
            }
        ]
    }
    
    confidence = desire_agent._calculate_confidence(desires, motivations)
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    
    # Verify confidence calculation is reasonable
    # Given high confidence desires (0.8, 0.6) and rich motivations structure
    # confidence should be above threshold
    assert confidence >= 0.5, f"Confidence {confidence} should be >= 0.5 given strong input values"

@pytest.mark.asyncio
async def test_error_handling(desire_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    desire_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await desire_agent.analyze_desires({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, DesireResult)
    assert result.confidence == 0.0
    assert len(result.desires) == 0
    assert "error" in result.metadata
    assert "error" in result.motivations

@pytest.mark.asyncio
async def test_domain_awareness(desire_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await desire_agent.analyze_desires(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    desire_agent.domain = "personal"
    result = await desire_agent.analyze_desires(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
