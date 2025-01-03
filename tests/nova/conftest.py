"""Test configuration for Nova's FastAPI server."""

import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_llm():
    """Mock LM Studio responses."""
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": """
{
    "analytics": {
        "key_metrics": [
            {
                "name": "Test Metric",
                "value": 0.8,
                "confidence": 0.9
            }
        ],
        "trends": [
            {
                "name": "Test Trend",
                "description": "Test trend description",
                "confidence": 0.85
            }
        ]
    },
    "insights": [
        {
            "type": "test_insight",
            "description": "Test insight description",
            "confidence": 0.8,
            "recommendations": ["Test recommendation"]
        }
    ]
}
"""
                }
            }
        ]
    }

    async def mock_analyze(*args, **kwargs):
        return mock_response

    async def mock_get_structured_completion(*args, **kwargs):
        return mock_response

    with patch("nia.nova.core.llm.LMStudioLLM.analyze", new=AsyncMock(side_effect=mock_analyze)), \
         patch("nia.nova.core.llm.LMStudioLLM.get_structured_completion", new=AsyncMock(side_effect=mock_get_structured_completion)):
        yield
