"""Integration tests for Nova's FastAPI server."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS, reset_rate_limits
from nia.nova.core.test_data import (
    VALID_TASK,
    VALID_COORDINATION_REQUEST,
    VALID_AGENT_ASSIGNMENT,
    VALID_MEMORY_STORE,
    VALID_MEMORY_SEARCH,
    VALID_RESOURCE_ALLOCATION,
    VALID_FLOW_OPTIMIZATION,
    VALID_ANALYTICS_REQUEST
)

# Test client
client = TestClient(app)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

# Test headers
HEADERS = {"X-API-Key": TEST_API_KEY}

@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset test state before each test."""
    reset_rate_limits()
    yield

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == app.version

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nova API"
    assert data["version"] == app.version
    assert data["docs_url"] == "/docs"
    assert data["redoc_url"] == "/redoc"

def test_missing_api_key():
    """Test endpoints require API key."""
    endpoints = [
        "/api/analytics/flows",
        "/api/analytics/resources",
        "/api/analytics/agents",
        "/api/orchestration/tasks",
        "/api/orchestration/agents/coordinate",
        "/api/orchestration/memory/store"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

def test_invalid_api_key():
    """Test invalid API key handling."""
    headers = {"X-API-Key": "invalid-key"}
    response = client.get("/api/analytics/flows", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"

def test_flow_analytics():
    """Test flow analytics endpoint."""
    response = client.get(
        "/api/analytics/flows",
        headers=HEADERS,
        params={"flow_id": "test-flow"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "insights" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_resource_analytics():
    """Test resource analytics endpoint."""
    response = client.get(
        "/api/analytics/resources",
        headers=HEADERS,
        params={"resource_id": "test-resource"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "insights" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_agent_analytics():
    """Test agent analytics endpoint."""
    response = client.get(
        "/api/analytics/agents",
        headers=HEADERS,
        params={"agent_id": "test-agent"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "insights" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_create_task():
    """Test task creation endpoint."""
    response = client.post(
        "/api/orchestration/tasks",
        headers=HEADERS,
        json=VALID_TASK
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "created"
    assert "orchestration" in data
    assert "confidence" in data
    assert "timestamp" in data
    
    # Store task_id for subsequent tests
    return data["task_id"]

def test_get_task():
    """Test task retrieval endpoint."""
    # First create a task
    task_id = test_create_task()
    
    # Then retrieve it
    response = client.get(
        f"/api/orchestration/tasks/{task_id}",
        headers=HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert "status" in data
    assert "orchestration" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_update_task():
    """Test task update endpoint."""
    # First create a task
    task_id = test_create_task()
    
    # Then update it
    updates = VALID_TASK.copy()
    updates["parameters"]["key"] = "updated"
    updates["priority"] = 2
    
    response = client.put(
        f"/api/orchestration/tasks/{task_id}",
        headers=HEADERS,
        json=updates
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "updated"
    assert "orchestration" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_coordinate_agents():
    """Test agent coordination endpoint."""
    response = client.post(
        "/api/orchestration/agents/coordinate",
        headers=HEADERS,
        json=VALID_COORDINATION_REQUEST
    )
    assert response.status_code == 200
    data = response.json()
    assert "coordination_id" in data
    assert data["status"] == "coordinated"
    assert "orchestration" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_assign_agent():
    """Test agent assignment endpoint."""
    response = client.post(
        "/api/orchestration/agents/test-agent/assign",
        headers=HEADERS,
        json=VALID_AGENT_ASSIGNMENT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "test-agent"
    assert data["status"] == "assigned"
    assert "orchestration" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_optimize_flow():
    """Test flow optimization endpoint."""
    response = client.post(
        "/api/orchestration/flows/test-flow/optimize",
        headers=HEADERS,
        json=VALID_FLOW_OPTIMIZATION
    )
    assert response.status_code == 200
    data = response.json()
    assert data["flow_id"] == "test-flow"
    assert "optimizations" in data
    assert "analytics" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_allocate_resources():
    """Test resource allocation endpoint."""
    response = client.post(
        "/api/orchestration/resources/allocate",
        headers=HEADERS,
        json=VALID_RESOURCE_ALLOCATION
    )
    assert response.status_code == 200
    data = response.json()
    assert "allocations" in data
    assert "analytics" in data
    assert "confidence" in data
    assert "timestamp" in data

def test_memory_operations():
    """Test memory operations endpoints."""
    # Test store
    store_response = client.post(
        "/api/orchestration/memory/store",
        headers=HEADERS,
        json=VALID_MEMORY_STORE
    )
    assert store_response.status_code == 200
    store_data = store_response.json()
    memory_id = store_data["memory_id"]
    
    # Test retrieve
    retrieve_response = client.get(
        f"/api/orchestration/memory/{memory_id}",
        headers=HEADERS
    )
    assert retrieve_response.status_code == 200
    retrieve_data = retrieve_response.json()
    assert retrieve_data["memory_id"] == memory_id
    assert "content" in retrieve_data
    
    # Test search
    search_response = client.post(
        "/api/orchestration/memory/search",
        headers=HEADERS,
        json=VALID_MEMORY_SEARCH
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert "matches" in search_data

def test_rate_limiting():
    """Test rate limiting."""
    # Make requests up to limit
    for _ in range(100):
        response = client.get(
            "/api/analytics/flows",
            headers=HEADERS
        )
        assert response.status_code == 200
    
    # Next request should fail
    response = client.get(
        "/api/analytics/flows",
        headers=HEADERS
    )
    assert response.status_code == 429
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

def test_websocket():
    """Test WebSocket connection."""
    # Set up WebSocket headers
    headers = {
        "x-api-key": TEST_API_KEY,
        "connection": "upgrade",
        "upgrade": "websocket",
        "sec-websocket-version": "13",
        "sec-websocket-key": "dGhlIHNhbXBsZSBub25jZQ=="  # Required by WebSocket protocol
    }
    
    with client.websocket_connect(
        "/api/analytics/ws",
        headers=headers
    ) as websocket:
        # Send analytics request
        websocket.send_json(VALID_ANALYTICS_REQUEST)
        
        # Receive response
        data = websocket.receive_json()
        assert data["type"] == "analytics_update"
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data
