"""Integration tests for Nova's FastAPI server."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS, reset_rate_limits
from nia.nova.core.endpoints import get_analytics_agent, get_memory_system, get_world
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

from httpx import AsyncClient
from fastapi.testclient import TestClient
import websockets
import json

# Test client
client = TestClient(app)

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

# Test headers
HEADERS = {"X-API-Key": TEST_API_KEY}

@pytest.fixture
async def world():
    """Create world instance for testing."""
    from nia.world.environment import NIAWorld
    return NIAWorld()

@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset test state before each test."""
    reset_rate_limits()
    yield

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == app.version

def test_root():
    """Test root endpoint."""
    response = client.get("/", headers=HEADERS)
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

@pytest.mark.asyncio
async def test_flow_analytics(mock_memory, mock_analytics_agent, world):
    """Test flow analytics endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_resource_analytics(mock_memory, mock_analytics_agent, world):
    """Test resource analytics endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_agent_analytics(mock_memory, mock_analytics_agent, world):
    """Test agent analytics endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_create_task(mock_memory, mock_analytics_agent, world):
    """Test task creation endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_get_task(mock_memory, mock_analytics_agent, world):
    """Test task retrieval endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        # First create a task
        task_id = await test_create_task(mock_memory, mock_analytics_agent, world)
        
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_update_task(mock_memory, mock_analytics_agent, world):
    """Test task update endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        # First create a task
        task_id = await test_create_task(mock_memory, mock_analytics_agent, world)
        
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_coordinate_agents(mock_memory, mock_analytics_agent, world):
    """Test agent coordination endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_assign_agent(mock_memory, mock_analytics_agent, world):
    """Test agent assignment endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_optimize_flow(mock_memory, mock_analytics_agent, world):
    """Test flow optimization endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_allocate_resources(mock_memory, mock_analytics_agent, world):
    """Test resource allocation endpoint."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

@pytest.mark.asyncio
async def test_memory_operations(mock_memory, mock_analytics_agent, world):
    """Test memory operations endpoints."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
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
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
        if "get_world" in app.dependency_overrides:
            del app.dependency_overrides["get_world"]

def test_rate_limiting():
    """Test rate limiting."""
    # Use a simpler endpoint that doesn't involve vector store
    endpoint = "/health"
    
    # Make requests up to limit
    for _ in range(100):
        response = client.get(
            endpoint,
            headers=HEADERS
        )
        assert response.status_code == 200
    
    # Next request should fail
    response = client.get(
        endpoint,
        headers=HEADERS
    )
    assert response.status_code == 429
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

@pytest.fixture
async def mock_memory():
    class MockStore:
        async def connect(self):
            return self
            
        async def close(self):
            return None
            
        async def ensure_collection(self):
            return "test_collection"
            
        async def store(self, *args, **kwargs):
            return {"id": "test-id"}
            
        async def search(self, *args, **kwargs):
            return []
            
        async def get_collection(self):
            return "test_collection"
    
    class MockMemorySystem:
        def __init__(self):
            self.semantic = MockStore()
            self.episodic = MockStore()
            self.vector_store = MockStore()
            
        async def __aenter__(self):
            await self.semantic.connect()
            await self.episodic.connect()
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.semantic.close()
            await self.episodic.close()
    
    memory_system = MockMemorySystem()
    async with memory_system as ms:
        yield ms

@pytest.fixture
async def mock_analytics_agent():
    class MockAnalyticsAgent:
        async def process_analytics(self, content, analytics_type, metadata=None):
            from nia.nova.core.analytics import AnalyticsResult
            return AnalyticsResult(
                is_valid=True,
                analytics={
                    "test_metric": {
                        "type": "metric",
                        "value": 0.8,
                        "confidence": 0.9
                    }
                },
                insights=[
                    {
                        "type": "test_insight",
                        "description": "Test insight",
                        "confidence": 0.9
                    }
                ],
                confidence=0.9,
                metadata=metadata
            )
            
        async def process_and_store(self, content, analytics_type, target_domain=None):
            from nia.nova.core.analytics import AnalyticsResult
            return AnalyticsResult(
                is_valid=True,
                analytics={},
                insights=[],
                confidence=0.9,
                metadata={"domain": target_domain}
            )
            
        async def get_domain_access(self, domain):
            return domain == "test" or domain == "professional"
            
        async def validate_domain_access(self, domain):
            if not await self.get_domain_access(domain):
                raise PermissionError(f"No access to domain: {domain}")
    
    agent = MockAnalyticsAgent()
    return agent

@pytest.fixture
async def mock_llm():
    class MockLLM:
        async def analyze(self, content, template=None, max_tokens=None):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "analytics": {"test": "data"},
                                "insights": [{"type": "test"}]
                            })
                        }
                    }
                ]
            }
    return MockLLM()

@pytest.fixture
async def mock_tiny_factory(mock_memory, mock_llm):
    class MockTinyFactory:
        def __init__(self, memory_system=None):
            self.memory_system = memory_system
            self.agents = {}
            
        def create_agent(self, agent_type, domain, capabilities, supervisor_id=None, attributes=None):
            agent_id = f"test_{agent_type}_{len(self.agents)}"
            self.agents[agent_id] = {
                "type": agent_type,
                "domain": domain,
                "capabilities": capabilities,
                "supervisor_id": supervisor_id,
                "attributes": attributes or {}
            }
            return agent_id
            
        def get_agent(self, agent_id):
            return self.agents.get(agent_id)
            
        def get_agents_by_type(self, agent_type):
            return [
                agent_id for agent_id, agent in self.agents.items()
                if agent["type"] == agent_type
            ]
            
        def get_agents_by_domain(self, domain):
            return [
                agent_id for agent_id, agent in self.agents.items()
                if agent["domain"] == domain
            ]
    
    return MockTinyFactory(memory_system=mock_memory)

@pytest.mark.asyncio
async def test_websocket_success(mock_memory, mock_analytics_agent, world):
    """Test successful WebSocket connection and analytics."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        # Use FastAPI's test client
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
            # Send analytics request
            websocket.send_json(VALID_ANALYTICS_REQUEST)
            
            # Receive response
            data = websocket.receive_json()
            assert data["type"] == "analytics_update"
            assert "analytics" in data
            assert "insights" in data
            assert "confidence" in data
            assert "timestamp" in data
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

def test_websocket_invalid_api_key():
    """Test WebSocket connection with invalid API key."""
    with pytest.raises(Exception) as exc_info:  # FastAPI's TestClient raises its own exception
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": "invalid-key"}):
            pass

def test_websocket_missing_api_key():
    """Test WebSocket connection without API key."""
    with pytest.raises(Exception) as exc_info:  # FastAPI's TestClient raises its own exception
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws"):
            pass

@pytest.mark.asyncio
async def test_websocket_invalid_request(mock_memory, mock_analytics_agent, world):
    """Test WebSocket connection with invalid analytics request."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
            # Send invalid request
            websocket.send_json({"invalid": "request"})
            
            # Receive error response
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

@pytest.mark.asyncio
async def test_websocket_processing_error(mock_memory, mock_analytics_agent, world):
    """Test WebSocket connection with processing error."""
    # Override dependencies with error-raising mock
    class ErrorAnalyticsAgent:
        async def process_analytics(self, content, analytics_type, metadata=None):
            raise Exception("Processing error")
    
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: ErrorAnalyticsAgent()
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
            # Send valid request that will trigger processing error
            websocket.send_json(VALID_ANALYTICS_REQUEST)
            
            # Receive error response
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "error" in data
            assert data["error"]["code"] == "PROCESSING_ERROR"
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

@pytest.mark.asyncio
async def test_websocket_rate_limiting(mock_memory, mock_analytics_agent, world):
    """Test WebSocket connection rate limiting."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        # Make requests up to limit
        for _ in range(100):
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                websocket.send_json(VALID_ANALYTICS_REQUEST)
                data = websocket.receive_json()
                assert data["type"] == "analytics_update"
        
        # Next request should fail
        with pytest.raises(Exception) as exc_info:  # FastAPI's TestClient raises its own exception
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}):
                pass
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

@pytest.mark.asyncio
async def test_websocket_cleanup_on_disconnect(mock_memory, mock_analytics_agent, world):
    """Test WebSocket cleanup when connection is closed unexpectedly."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        # Connect and immediately close
        websocket = client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY})
        websocket.close()
        
        # Should be able to connect again
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
            websocket.send_json(VALID_ANALYTICS_REQUEST)
            data = websocket.receive_json()
            assert data["type"] == "analytics_update"
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

@pytest.mark.asyncio
async def test_websocket_concurrent_connections(mock_memory, mock_analytics_agent, world):
    """Test multiple concurrent WebSocket connections."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        # Create multiple connections
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as ws1, \
             client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as ws2:
            
            # Send requests on both connections
            ws1.send_json(VALID_ANALYTICS_REQUEST)
            ws2.send_json(VALID_ANALYTICS_REQUEST)
            
            # Verify both connections receive responses
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()
            
            assert data1["type"] == "analytics_update"
            assert data2["type"] == "analytics_update"
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

@pytest.mark.asyncio
async def test_websocket_timeout(mock_memory, mock_analytics_agent, world):
    """Test WebSocket connection timeout handling."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
            # Send initial request to verify connection
            websocket.send_json(VALID_ANALYTICS_REQUEST)
            data = websocket.receive_json()
            assert data["type"] == "analytics_update"
            
            # Wait for timeout (FastAPI's default is 10 seconds)
            import time
            time.sleep(11)
            
            # Next request should fail due to timeout
            with pytest.raises(Exception) as exc_info:  # FastAPI's TestClient raises its own exception
                websocket.send_json(VALID_ANALYTICS_REQUEST)
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]

@pytest.mark.asyncio
async def test_websocket_heartbeat(mock_memory, mock_analytics_agent, world):
    """Test WebSocket connection stays alive with ping/pong."""
    # Override dependencies
    app.dependency_overrides[get_memory_system] = lambda: mock_memory
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_world] = lambda: world
    
    try:
        client = TestClient(app)
        with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
            # Send initial request
            websocket.send_json(VALID_ANALYTICS_REQUEST)
            data = websocket.receive_json()
            assert data["type"] == "analytics_update"
            
            # Wait longer than ping interval but less than timeout
            import time
            time.sleep(5)  # Default ping interval is 3 seconds
            
            # Connection should still be alive
            websocket.send_json(VALID_ANALYTICS_REQUEST)
            data = websocket.receive_json()
            assert data["type"] == "analytics_update"
    finally:
        if "get_analytics_agent" in app.dependency_overrides:
            del app.dependency_overrides["get_analytics_agent"]
        if "get_memory_system" in app.dependency_overrides:
            del app.dependency_overrides["get_memory_system"]
