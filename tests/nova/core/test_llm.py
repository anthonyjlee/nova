"""Unit tests for LM Studio LLM implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, AsyncIterator, Union
import json
import aiohttp
from datetime import datetime
from pydantic import BaseModel

from nia.nova.core.llm import LMStudioLLM
from nia.nova.core.llm_types import (
    LLMConcept,
    LLMAnalysisResult,
    LLMAnalyticsResult,
    LLMError
)

@pytest.fixture
def llm():
    """Create LLM instance for testing."""
    return LMStudioLLM(
        chat_model="test_model",
        embedding_model="test_embeddings",
        api_base="http://localhost:1234/v1"
    )

@pytest.fixture
def mock_response():
    """Create mock response data."""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "response": "Test analysis",
                    "concepts": ["concept1", "concept2"],
                    "key_points": ["point1", "point2"],
                    "implications": ["implication1"],
                    "uncertainties": ["uncertainty1"],
                    "reasoning": ["reason1"],
                    "metadata": {
                        "confidence": 0.8
                    }
                })
            }
        }]
    }

@pytest.fixture
def mock_stream_response():
    """Create mock streaming response."""
    async def generate_chunks():
        chunks = [
            {
                "choices": [{
                    "delta": {
                        "content": "chunk1"
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "content": "chunk2"
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "content": "chunk3"
                    },
                    "finish_reason": "stop"
                }]
            }
        ]
        for chunk in chunks:
            yield json.dumps(chunk).encode() + b"\n"
    
    mock = AsyncMock()
    mock.content.iter_any = generate_chunks
    mock.status = 200
    return mock

@pytest.mark.asyncio
async def test_analyze(llm, mock_response):
    """Test content analysis."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.return_value = mock_response
        
        result = await llm.analyze(
            content={"text": "test content"},
            template="parsing_analysis"
        )
        
        assert result["response"] == "Test analysis"
        assert len(result["concepts"]) == 2
        assert len(result["key_points"]) == 2
        assert result["confidence"] == 0.8

@pytest.mark.asyncio
async def test_streaming_analysis(llm, mock_stream_response):
    """Test streaming analysis."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.return_value = mock_stream_response
        
        stream = await llm.analyze(
            content={"text": "test content"},
            template="parsing_analysis",
            stream=True
        )
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0]["data"]["content"] == "chunk1"
        assert not chunks[0]["data"]["is_final"]
        assert chunks[2]["data"]["is_final"]

@pytest.mark.asyncio
async def test_generate(llm, mock_response):
    """Test text generation."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.return_value = mock_response
        
        result = await llm.generate("Test prompt")
        assert isinstance(result, str)
        assert "Test analysis" in result

@pytest.mark.asyncio
async def test_streaming_generation(llm, mock_stream_response):
    """Test streaming text generation."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.return_value = mock_stream_response
        
        stream = await llm.generate("Test prompt", stream=True)
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert all(isinstance(c["data"]["content"], str) for c in chunks)
        assert chunks[-1]["data"]["is_final"]

@pytest.mark.asyncio
async def test_embeddings(llm):
    """Test text embeddings."""
    mock_embedding_response = {
        "data": [{
            "embedding": [0.1, 0.2, 0.3]
        }]
    }
    
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.return_value = mock_embedding_response
        
        result = await llm.embed("Test text")
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(x, float) for x in result)

@pytest.mark.asyncio
async def test_error_handling(llm):
    """Test error handling."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.side_effect = LLMError(
            code="TEST_ERROR",
            message="Test error message"
        )
        
        result = await llm.analyze(
            content={"text": "test"},
            template="parsing_analysis"
        )
        
        assert "Error analyzing content" in result["response"]
        assert result["concepts"][0]["type"] == "error"
        assert "Test error message" in result["concepts"][0]["description"]
        assert result["confidence"] == 0.0

@pytest.mark.asyncio
async def test_streaming_error_handling(llm):
    """Test streaming error handling."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.side_effect = LLMError(
            code="TEST_ERROR",
            message="Test error message"
        )
        
        stream = await llm.analyze(
            content={"text": "test"},
            template="parsing_analysis",
            stream=True
        )
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0]["type"] == "error"
        assert "Test error message" in chunks[0]["data"]["message"]

@pytest.mark.asyncio
async def test_session_management(llm):
    """Test client session management."""
    assert llm._session is None
    
    # First request creates session
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "test"}}]}
        )
        
        await llm.generate("test")
        assert llm._session is not None
        
        # Second request reuses session
        old_session = llm._session
        await llm.generate("test again")
        assert llm._session is old_session
        
        # Close session
        await llm.close()
        assert llm._session.closed

@pytest.mark.asyncio
async def test_structured_completion(llm, mock_response):
    """Test structured completion."""
    with patch.object(llm, "_make_request") as mock_request:
        mock_request.return_value = mock_response
        
        class TestResponse(BaseModel):
            response: str
            concepts: List[str]
            metadata: Dict[str, Any]
        
        result = await llm.get_structured_completion(
            prompt="Test prompt",
            response_model=TestResponse,
            metadata={"test": "metadata"}
        )
        
        assert isinstance(result, TestResponse)
        assert result.response == "Test analysis"
        assert len(result.concepts) == 2
        assert result.metadata["test"] == "metadata"
