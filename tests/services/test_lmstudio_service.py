"""Integration tests for LM Studio service."""

import pytest
from typing import Dict, Any, List
from nia.config.llm_config import LLMConfig, ModelType
from nia.services.llm_service import LMStudioService

@pytest.fixture
def llm_config() -> LLMConfig:
    """Create LLM configuration for testing."""
    return LLMConfig()

@pytest.fixture
async def lmstudio_service(llm_config: LLMConfig) -> LMStudioService:
    """Create LM Studio service for testing."""
    service = LMStudioService(llm_config)
    # Verify LM Studio is running and models are loaded
    if not await service.validate_connection():
        pytest.fail(
            "LM Studio not available. Please ensure:\n"
            "1. LM Studio is running on localhost:1234\n"
            "2. Required models are loaded:\n"
            f"   - Chat model: {llm_config.lmstudio.chat_model}\n"
            f"   - Embedding model: {llm_config.lmstudio.embedding_model}"
        )
    return service

@pytest.mark.asyncio
async def test_validate_connection(lmstudio_service: LMStudioService):
    """Test connection validation."""
    assert await lmstudio_service.validate_connection()

@pytest.mark.asyncio
async def test_chat_completion(lmstudio_service: LMStudioService):
    """Test chat completion."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"}
    ]
    
    response = await lmstudio_service.get_chat_completion(messages)
    
    assert "choices" in response
    assert len(response["choices"]) > 0
    assert "message" in response["choices"][0]
    assert "content" in response["choices"][0]["message"]
    # The response should contain "4" somewhere in the content
    assert "4" in response["choices"][0]["message"]["content"].lower()

@pytest.mark.asyncio
async def test_embeddings(lmstudio_service: LMStudioService):
    """Test text embeddings."""
    texts = [
        "This is a test sentence.",
        "Another test sentence for embedding."
    ]
    
    embeddings = await lmstudio_service.get_embeddings(texts)
    
    assert len(embeddings) == len(texts)
    assert all(isinstance(embedding, list) for embedding in embeddings)
    assert all(isinstance(value, float) for embedding in embeddings for value in embedding)
    # Embedding dimensions should be consistent
    assert all(len(embedding) == len(embeddings[0]) for embedding in embeddings)

@pytest.mark.asyncio
async def test_stream_chat_completion(lmstudio_service: LMStudioService):
    """Test streaming chat completion."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Count from 1 to 5."}
    ]
    
    response = await lmstudio_service.stream_chat_completion(messages)
    
    assert isinstance(response, str)
    assert len(response) > 0
    # Response should contain numbers 1 through 5
    assert all(str(i) in response for i in range(1, 6))

@pytest.mark.asyncio
async def test_chat_completion_with_temperature(lmstudio_service: LMStudioService):
    """Test chat completion with different temperatures."""
    messages = [
        {"role": "system", "content": "You are a creative assistant."},
        {"role": "user", "content": "Generate a random animal name."}
    ]
    
    # Test with low temperature (more focused)
    response_low = await lmstudio_service.get_chat_completion(messages, temperature=0.1)
    assert "choices" in response_low
    assert len(response_low["choices"]) > 0
    
    # Test with high temperature (more creative)
    response_high = await lmstudio_service.get_chat_completion(messages, temperature=0.9)
    assert "choices" in response_high
    assert len(response_high["choices"]) > 0
    
    # Responses should be different due to temperature difference
    low_content = response_low["choices"][0]["message"]["content"]
    high_content = response_high["choices"][0]["message"]["content"]
    assert low_content != high_content

@pytest.mark.asyncio
async def test_chat_completion_with_max_tokens(lmstudio_service: LMStudioService):
    """Test chat completion with max tokens limit."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a long story about a dragon."}
    ]
    
    # Test with limited tokens
    response = await lmstudio_service.get_chat_completion(messages, max_tokens=50)
    assert "choices" in response
    assert len(response["choices"]) > 0
    content = response["choices"][0]["message"]["content"]
    # Rough estimate: average token is 4 characters
    assert len(content) < 50 * 4

@pytest.mark.asyncio
async def test_error_handling(lmstudio_service: LMStudioService):
    """Test error handling for invalid requests."""
    # Test with empty messages
    with pytest.raises(ValueError) as exc_info:
        await lmstudio_service.get_chat_completion([])
    assert "error" in str(exc_info.value).lower()
    
    # Test with invalid message format
    with pytest.raises(ValueError) as exc_info:
        await lmstudio_service.get_chat_completion([{"invalid": "message"}])
    assert "error" in str(exc_info.value).lower()
    
    # Test with empty text for embeddings
    with pytest.raises(ValueError) as exc_info:
        await lmstudio_service.get_embeddings([])
    assert "error" in str(exc_info.value).lower()
