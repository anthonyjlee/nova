"""Integration tests for Nova's FastAPI server with LM Studio."""

import pytest
import aiohttp
import asyncio
import websockets
from fastapi.testclient import TestClient
import json
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import get_world
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld

# Test client
client = TestClient(app)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

# Test headers
HEADERS = {"X-API-Key": TEST_API_KEY}

# LM Studio configuration
CHAT_MODEL = "llama-3.2-3b-instruct"
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

@pytest.fixture
async def world():
    """Create world instance for testing."""
    return NIAWorld()

@pytest.fixture
async def memory_system():
    """Create memory system for testing."""
    system = TwoLayerMemorySystem()
    try:
        await system.initialize()
        yield system
    finally:
        await system.cleanup()

@pytest.fixture
async def parsing_agent(world, memory_system):
    """Create a parsing agent for testing."""
    agent = ParsingAgent(
        name="test_parser",
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    try:
        await agent.initialize()
        yield agent
    finally:
        await agent.cleanup()

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
async def test_parsing_with_lmstudio(parsing_agent, world, memory_system):
    """Test parsing capabilities with LM Studio."""
    try:
        # Test text for parsing
        test_text = """
        System load peaked at 95% at 14:00 UTC.
        Memory usage remained stable at 75%.
        Network latency increased by 20ms during peak hours.
        """
        
        # Create parse request
        parse_request = {
            "text": test_text,
            "llm_config": {
                "chat_model": CHAT_MODEL,
                "embedding_model": EMBEDDING_MODEL
            },
            "domain": "professional"
        }
        
        # Get parsing results
        response = client.post(
            "/api/analytics/parse",
            headers=HEADERS,
            json=parse_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "concepts" in data
        assert "key_points" in data
        assert data["confidence"] > 0
        
        # Verify parsing agent was used
        assert await parsing_agent.get_last_parse() is not None
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_analytics_with_lmstudio(world, memory_system):
    """Test analytics generation with LM Studio."""
    try:
        # Test analytics request
        response = client.get(
            "/api/analytics/flows",
            headers=HEADERS,
            params={
                "flow_id": "test-flow",
                "llm_config": json.dumps({
                    "chat_model": CHAT_MODEL,
                    "embedding_model": EMBEDDING_MODEL
                })
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "insights" in data
        assert data["insights"]
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_memory_operations_with_lmstudio(world, memory_system):
    """Test memory operations with LM Studio."""
    try:
        # Store memory with semantic analysis
        store_response = client.post(
            "/api/orchestration/memory/store",
            headers=HEADERS,
            json={
                "type": "observation",
                "content": {
                    "text": "High system load detected during peak hours",
                    "type": "observation"
                },
                "importance": 0.8,
                "context": {
                    "source": "system_monitor",
                    "timestamp": datetime.now().isoformat()
                },
                "llm_config": {
                    "chat_model": CHAT_MODEL,
                    "embedding_model": EMBEDDING_MODEL
                }
            }
        )
        
        assert store_response.status_code == 200
        memory_id = store_response.json()["memory_id"]
        
        # Search memory using semantic search
        search_response = client.post(
            "/api/orchestration/memory/search",
            headers=HEADERS,
            json={
                "type": "semantic_search",
                "content": {
                    "query": "system performance issues"
                },
                "importance": 0.5,
                "context": {
                    "search_type": "semantic",
                    "timestamp": datetime.now().isoformat()
                },
                "llm_config": {
                    "chat_model": CHAT_MODEL,
                    "embedding_model": EMBEDDING_MODEL
                }
            }
        )
        
        assert search_response.status_code == 200
        results = search_response.json()["matches"]
        assert len(results) > 0
        
        # Verify memory was stored and retrieved
        stored_memory = await memory_system.get_memory(memory_id)
        assert stored_memory is not None
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_websocket_with_lmstudio(world, memory_system):
    """Test WebSocket connection with LM Studio integration."""
    try:
        async with client.websocket_connect(
            "/api/analytics/ws",
            headers={
                "x-api-key": TEST_API_KEY
            }
        ) as websocket:
            # Send analytics request
            await websocket.send_json({
                "type": "parse_request",
                "content": "System load increased to 90%",
                "llm_config": {
                    "chat_model": CHAT_MODEL,
                    "embedding_model": EMBEDDING_MODEL
                }
            })
            
            # Receive response with timeout
            data = await asyncio.wait_for(websocket.receive_json(), timeout=10)
            assert data["type"] == "analytics_update"
            assert "insights" in data
            assert data["insights"]
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_error_handling(world, memory_system):
    """Test error handling with invalid requests."""
    try:
        # Test invalid model
        response = client.post(
            "/api/analytics/parse",
            headers=HEADERS,
            json={
                "text": "Test text",
                "llm_config": {
                    "chat_model": "invalid-model",
                    "embedding_model": EMBEDDING_MODEL
                }
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Chat model" in str(data["detail"])
        
        # Test missing API key
        response = client.post(
            "/api/analytics/parse",
            json={
                "text": "Test text",
                "llm_config": {
                    "chat_model": CHAT_MODEL,
                    "embedding_model": EMBEDDING_MODEL
                }
            }
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
