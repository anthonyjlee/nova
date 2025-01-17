"""Integration tests for Nova's LM Studio integration."""

import pytest
import aiohttp
import asyncio
from datetime import datetime

from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld

# LM Studio configuration
CHAT_MODEL = "llama-3.2-3b-instruct"
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

@pytest.fixture
def world():
    """Create world instance for testing."""
    return NIAWorld()

@pytest.fixture
async def memory_system():
    """Create memory system for testing."""
    from nia.memory.vector.vector_store import VectorStore
    from nia.memory.vector.embeddings import EmbeddingService
    
    # Create vector store with connection details
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        embedding_service=embedding_service,
        host="localhost",
        port=6333
    )
    
    system = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store=vector_store
    )
    await system.initialize()
    return system

@pytest.fixture
async def parsing_agent(world, memory_system):
    """Create parsing agent for testing."""
    agent = ParsingAgent(
        name="test_parser",
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    await agent.initialize()
    return agent

@pytest.fixture(autouse=True)
async def setup_lmstudio():
    """Setup LM Studio connection before tests."""
    try:
        # Check models endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:1234/v1/models") as response:
                    if response.status == 404:
                        pytest.skip("LM Studio API endpoint not found. Please ensure LM Studio is running and API is enabled.")
                    elif response.status != 200:
                        pytest.skip(f"LM Studio returned status {response.status}. Please check LM Studio configuration.")
                    
                    data = await response.json()
                    models = data.get("data", [])
                    available_models = [model["id"] for model in models]
                    
                    if CHAT_MODEL not in available_models:
                        pytest.skip(f"Required chat model '{CHAT_MODEL}' not found in LM Studio. Please load the model and try again.")
                        
                    if EMBEDDING_MODEL not in available_models:
                        pytest.skip(f"Required embedding model '{EMBEDDING_MODEL}' not found in LM Studio. Please load the model and try again.")
                    
        except aiohttp.ClientError:
            pytest.skip("Could not connect to LM Studio. Please ensure LM Studio is running on port 1234.")
            
    except Exception as e:
        pytest.skip(f"LM Studio setup failed: {str(e)}. Please check LM Studio configuration.")

@pytest.mark.asyncio
async def test_lmstudio_parsing(parsing_agent):
    """Test LM Studio can handle basic parsing."""
    try:
        # Test text for parsing
        test_text = """
        System load peaked at 95% at 14:00 UTC.
        Memory usage remained stable at 75%.
        Network latency increased by 20ms during peak hours.
        """
        
        # Parse text
        result = await parsing_agent.parse_and_store(test_text)
        
        # Verify response format
        assert result is not None
        assert result.concepts  # Should have concepts array
        assert result.key_points  # Should have key_points array
        assert result.confidence > 0  # Should have confidence score
        
        # Verify content was understood
        assert any("load" in concept["statement"].lower() for concept in result.concepts)
        assert any("memory" in concept["statement"].lower() for concept in result.concepts)
        assert any("latency" in concept["statement"].lower() for concept in result.concepts)
        
    except Exception as e:
        pytest.fail(f"LM Studio parsing test failed: {str(e)}")

@pytest.mark.asyncio
async def test_lmstudio_error_handling(parsing_agent):
    """Test LM Studio handles errors properly."""
    try:
        # Test with invalid input
        result = await parsing_agent.parse_and_store("")
        
        # Should still return valid format
        assert result is not None
        assert result.concepts  # Should have concepts array
        assert result.key_points  # Should have key_points array
        assert result.confidence < 0.5  # Should have low confidence
        
        # Should indicate error
        assert any("error" in concept["type"].lower() for concept in result.concepts)
        
    except Exception as e:
        pytest.fail(f"LM Studio error handling test failed: {str(e)}")
