"""Tests for Nova's emotion analysis functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.nova.core.emotion import EmotionAgent, EmotionResult

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value={
        "emotions": [
            {
                "name": "joy",
                "type": "primary",
                "description": "Strong positive feeling",
                "intensity": 0.8,
                "confidence": 0.9,
                "valence": 0.9,
                "arousal": 0.7,
                "domain_appropriateness": 0.8
            }
        ],
        "context": {
            "triggers": ["positive feedback"],
            "background": "Professional achievement",
            "domain_factors": {
                "setting": "workplace",
                "intensity_appropriateness": "high"
            },
            "relationships": [
                {
                    "type": "professional",
                    "target": "colleague",
                    "strength": 0.7
                }
            ]
        }
    })
    return llm

@pytest.fixture
def emotion_agent(mock_llm):
    """Create an EmotionAgent instance with mock dependencies."""
    return EmotionAgent(
        llm=mock_llm,
        store=MagicMock(),
        vector_store=MagicMock(),
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_emotion_with_llm(emotion_agent, mock_llm):
    """Test emotion analysis using LLM."""
    content = {
        "content": "I'm very happy with the results!",
        "type": "feedback"
    }
    
    result = await emotion_agent.analyze_emotion(content)
    
    # Verify LLM was called
    mock_llm.analyze.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, EmotionResult)
    assert len(result.emotions) == 1
    assert isinstance(result.intensity, (int, float))
    assert 0 <= result.intensity <= 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1
    assert "domain" in result.metadata
    assert result.context is not None

@pytest.mark.asyncio
async def test_analyze_emotion_without_llm():
    """Test emotion analysis without LLM (fallback mode)."""
    agent = EmotionAgent()  # No LLM provided
    content = {
        "content": "I'm happy and excited about this!",
        "context": {"setting": "meeting"}
    }
    
    result = await agent.analyze_emotion(content)
    
    # Verify basic analysis worked
    assert isinstance(result, EmotionResult)
    assert len(result.emotions) > 0
    assert any(e["type"] == "basic_emotion" for e in result.emotions)
    assert isinstance(result.intensity, (int, float))
    assert 0 <= result.intensity <= 1
    assert isinstance(result.confidence, (int, float))
    assert 0 <= result.confidence <= 1

def test_basic_analysis(emotion_agent):
    """Test basic emotion analysis without LLM."""
    content = {
        "content": "I'm happy but also a bit afraid",
        "context": {
            "setting": "presentation"
        }
    }
    
    result = emotion_agent._basic_analysis(content)
    
    assert "emotions" in result
    assert "context" in result
    assert len(result["emotions"]) == 2  # happy and afraid
    assert all(e["type"] == "basic_emotion" for e in result["emotions"])

def test_extract_emotions(emotion_agent):
    """Test emotion extraction and validation."""
    analysis = {
        "emotions": [
            {
                "name": "joy",
                "type": "primary",
                "intensity": 0.8,
                "confidence": 0.9,
                "valence": 0.9,
                "arousal": 0.7,
                "domain_appropriateness": 0.8
            },
            {
                "name": "interest",
                "intensity": 0.6  # Missing type should get default
            },
            "invalid"  # Not a dict, should be ignored
        ]
    }
    
    emotions = emotion_agent._extract_emotions(analysis)
    
    assert len(emotions) == 2  # Invalid one should be filtered out
    assert all("type" in e for e in emotions)
    assert any(e["type"] == "emotion" for e in emotions)  # Default type
    assert any("valence" in e for e in emotions)
    assert any("domain_appropriateness" in e for e in emotions)
    assert all("confidence" in e for e in emotions)
    assert all(isinstance(e["confidence"], (int, float)) for e in emotions)
    assert all(0 <= e["confidence"] <= 1 for e in emotions)

def test_calculate_intensity(emotion_agent):
    """Test intensity calculation."""
    emotions = [
        {
            "intensity": 0.8,
            "confidence": 0.9
        },
        {
            "intensity": 0.6,
            "confidence": 0.7
        }
    ]
    
    intensity = emotion_agent._calculate_intensity(emotions)
    
    assert 0 <= intensity <= 1
    # Should be weighted average:
    # (0.8 * 0.9 + 0.6 * 0.7) / (0.9 + 0.7) ≈ 0.71
    assert 0.70 <= intensity <= 0.72

def test_extract_context(emotion_agent):
    """Test context extraction and validation."""
    analysis = {
        "context": {
            "triggers": ["event1", "event2"],
            "background": "test background",
            "domain_factors": {
                "setting": "workplace",
                "intensity": "high"
            },
            "relationships": [
                {
                    "type": "professional",
                    "target": "colleague",
                    "strength": 0.7
                }
            ],
            "invalid": object()  # Should be ignored
        }
    }
    
    context = emotion_agent._extract_context(analysis)
    
    assert "triggers" in context
    assert "background" in context
    assert "domain_factors" in context
    assert "relationships" in context
    assert len(context["relationships"]) == 1
    assert "invalid" not in context

def test_calculate_confidence(emotion_agent):
    """Test confidence calculation."""
    emotions = [
        {
            "confidence": 0.8,
            "domain_appropriateness": 0.9
        },
        {
            "confidence": 0.6,
            "domain_appropriateness": 0.7
        }
    ]
    
    intensity = 0.8  # High intensity
    
    confidence = emotion_agent._calculate_confidence(emotions, intensity)
    
    # Verify confidence is a valid number
    assert isinstance(confidence, (int, float))
    assert 0 <= confidence <= 1
    
    # Verify confidence calculation is reasonable
    # Given high confidence (0.8, 0.6) and high domain appropriateness (0.9, 0.7)
    # confidence should be above threshold
    assert confidence >= 0.6, f"Confidence {confidence} should be >= 0.6 given high input values"

@pytest.mark.asyncio
async def test_error_handling(emotion_agent):
    """Test error handling during analysis."""
    # Make LLM raise an error
    emotion_agent.llm.analyze.side_effect = Exception("Test error")
    
    result = await emotion_agent.analyze_emotion({"content": "test"})
    
    # Verify we get a valid but error-indicating result
    assert isinstance(result, EmotionResult)
    assert result.confidence == 0.0
    assert result.intensity == 0.0
    assert len(result.emotions) == 0
    assert "error" in result.metadata
    assert "error" in result.context

@pytest.mark.asyncio
async def test_domain_awareness(emotion_agent):
    """Test domain awareness in analysis."""
    content = {"content": "test"}
    result = await emotion_agent.analyze_emotion(content)
    
    # Verify domain is included
    assert result.metadata["domain"] == "professional"
    
    # Test with different domain
    emotion_agent.domain = "personal"
    result = await emotion_agent.analyze_emotion(content)
    assert result.metadata["domain"] == "personal"

if __name__ == "__main__":
    pytest.main([__file__])
