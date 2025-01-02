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
    assert len(result.desires) == 1
    assert result.confidence > 0
    assert "domain" in result.metadata
    assert result.motivations is not None

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
    assert result.confidence >= 0
    assert "explicit_reason" not in result.motivations  # No "because" in text

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
    assert len(result["desires"]) == 2  # "want to" and "need to"
    assert all(d["type"] == "inferred_desire" for d in result["desires"])
    assert "explicit_reason" in result["motivations"]

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
    
    assert len(desires) == 2  # Invalid one should be filtered out
    assert all("type" in d for d in desires)
    assert any(d["type"] == "desire" for d in desires)  # Default type
    assert any("domain_relevance" in d for d in desires)
    assert any("priority" in d for d in desires)

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
    
    assert "reasons" in motivations
    assert "drivers" in motivations
    assert "constraints" in motivations
    assert "domain_factors" in motivations
    assert "priority_factors" in motivations
    assert len(motivations["reasons"]) == 2
    assert len(motivations["priority_factors"]) == 1
    assert "invalid" not in motivations

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
    
    assert 0 <= confidence <= 1
    # Should include:
    # - Desire confidence (0.7 average)
    # - Reasons (0.4 from 2 reasons)
    # - Drivers (0.15 from 1 driver)
    # - Constraints (0.1 from 1 constraint)
    # - Domain factors (0.2 from 2 factors)
    # - Priority factors (0.15 from 1 factor)
    assert 0.65 <= confidence <= 0.75

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
