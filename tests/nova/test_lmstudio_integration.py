"""Integration tests for Nova's FastAPI server with LM Studio."""

import pytest
import requests
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
def parsing_agent(world):
    """Create a parsing agent for testing."""
    memory_system = TwoLayerMemorySystem()
    return ParsingAgent(
        name="test_parser",
        memory_system=memory_system,
        world=world,
        domain="professional"
    )

@pytest.fixture(autouse=True)
def setup_lmstudio():
    """Setup LM Studio connection before tests."""
    try:
        # Check models endpoint
        try:
            response = requests.get("http://localhost:1234/v1/models")
            if response.status_code == 404:
                pytest.skip("LM Studio API endpoint not found. Please ensure LM Studio is running and API is enabled.")
            elif response.status_code != 200:
                pytest.skip(f"LM Studio returned status {response.status_code}. Please check LM Studio configuration.")
            
            models = response.json().get("data", [])
            available_models = [model["id"] for model in models]
            
            if CHAT_MODEL not in available_models:
                pytest.skip(f"Required chat model '{CHAT_MODEL}' not found in LM Studio. Please load the model and try again.")
                
            if EMBEDDING_MODEL not in available_models:
                pytest.skip(f"Required embedding model '{EMBEDDING_MODEL}' not found in LM Studio. Please load the model and try again.")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Could not connect to LM Studio. Please ensure LM Studio is running on port 1234.")
            
    except Exception as e:
        pytest.skip(f"LM Studio setup failed: {str(e)}. Please check LM Studio configuration.")

def test_parsing_with_lmstudio(parsing_agent, world):
    """Test parsing capabilities with LM Studio."""
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
    
    # Override dependencies
    app.dependency_overrides[get_world] = lambda: world
    
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

def test_analytics_with_lmstudio(world):
    """Test analytics generation with LM Studio."""
    app.dependency_overrides[get_world] = lambda: world
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

def test_memory_operations_with_lmstudio(world):
    """Test memory operations with LM Studio."""
    app.dependency_overrides[get_world] = lambda: world
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

def test_websocket_with_lmstudio(world):
    """Test WebSocket connection with LM Studio integration."""
    app.dependency_overrides[get_world] = lambda: world
    with client.websocket_connect(
        "/api/analytics/ws",
        headers={
            "x-api-key": TEST_API_KEY
        }
    ) as websocket:
        # Send analytics request
        websocket.send_json({
            "type": "parse_request",
            "content": "System load increased to 90%",
            "llm_config": {
                "chat_model": CHAT_MODEL,
                "embedding_model": EMBEDDING_MODEL
            }
        })
        
        # Receive response
        data = websocket.receive_json()
        assert data["type"] == "analytics_update"
        assert "insights" in data
        assert data["insights"]

def test_error_handling(world):
    """Test error handling with invalid requests."""
    app.dependency_overrides[get_world] = lambda: world
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
    assert "error" in data
    data = response.json()
    data = response.json()
    assert "Chat model" in data["detail"]["error"]
    
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
