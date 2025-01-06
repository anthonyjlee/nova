"""Tests for Nova's analytics endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.nia.nova.core.app import app
from src.nia.nova.core.analytics import AnalyticsAgent, AnalyticsResult
from src.nia.agents.specialized.orchestration_agent import OrchestrationAgent
from src.nia.nova.core.endpoints import get_world
from src.nia.world.environment import NIAWorld

client = TestClient(app)

@pytest.fixture
async def world():
    """Create world instance for testing."""
    return NIAWorld()

@pytest.fixture
def mock_analytics_agent(mocker, world):
    """Create a mock analytics agent."""
    agent = mocker.Mock()
    agent.process_analytics = mocker.AsyncMock(return_value=AnalyticsResult(
        is_valid=True,
        analytics={
            "type": "behavioral",
            "analytics": {
                "performance": {
                    "efficiency": 0.85,
                    "reliability": 0.9
                }
            }
        },
        insights=[
            {
                "type": "performance",
                "description": "High efficiency detected",
                "confidence": 0.8
            }
        ],
        confidence=0.85,
        metadata={"domain": "professional"}
    ))
    return agent

@pytest.fixture
def mock_orchestration_agent(mocker, mock_analytics_agent, world):
    """Create a mock orchestration agent."""
    agent = mocker.Mock()
    agent.analytics = mock_analytics_agent
    agent.active_flows = {
        "flow1": {
            "status": "active",
            "metrics": {"progress": 0.5}
        }
    }
    return agent

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "endpoints" in response.json()

@pytest.mark.asyncio
async def test_get_flow_analytics(world):
    """Test flow analytics endpoint."""
    app.dependency_overrides[get_world] = lambda: world
    response = client.get("/api/analytics/flows?flow_id=flow1")
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "insights" in data
    assert "confidence" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_get_resource_analytics(world):
    """Test resource analytics endpoint."""
    app.dependency_overrides[get_world] = lambda: world
    response = client.get("/api/analytics/resources?resource_id=resource1")
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "insights" in data
    assert "confidence" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_get_agent_analytics(world):
    """Test agent analytics endpoint."""
    app.dependency_overrides[get_world] = lambda: world
    response = client.get("/api/analytics/agents?agent_id=agent1")
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "insights" in data
    assert "confidence" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_optimize_flow(mock_orchestration_agent, world):
    """Test flow optimization endpoint."""
    app.dependency_overrides[get_world] = lambda: world
    response = client.post("/api/orchestration/flows/flow1/optimize")
    assert response.status_code == 200
    data = response.json()
    assert "flow_id" in data
    assert "optimizations" in data
    assert "analytics" in data
    assert "confidence" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_allocate_resources(mock_orchestration_agent, world):
    """Test resource allocation endpoint."""
    allocation_request = {
        "resources": {
            "cpu": {"requested": 2},
            "memory": {"requested": "4G"}
        }
    }
    app.dependency_overrides[get_world] = lambda: world
    response = client.post(
        "/api/orchestration/resources/allocate",
        json=allocation_request
    )
    assert response.status_code == 200
    data = response.json()
    assert "allocations" in data
    assert "analytics" in data
    assert "confidence" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_analytics_websocket(world):
    """Test analytics WebSocket endpoint."""
    app.dependency_overrides[get_world] = lambda: world
    with client.websocket_connect("/api/analytics/ws") as websocket:
        # Send analytics request
        websocket.send_json({
            "type": "flow_analytics",
            "flow_id": "flow1",
            "timestamp": datetime.now().isoformat()
        })
        
        # Receive response
        data = websocket.receive_json()
        assert data["type"] == "analytics_update"
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_domain_specific_analytics(world):
    """Test domain-specific analytics."""
    app.dependency_overrides[get_world] = lambda: world
    response = client.get(
        "/api/analytics/flows",
        params={"flow_id": "flow1", "domain": "personal"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analytics"].get("domain") == "personal"

@pytest.mark.asyncio
async def test_analytics_error_handling(world):
    """Test analytics error handling."""
    app.dependency_overrides[get_world] = lambda: world
    # Test invalid flow ID
    response = client.get("/api/analytics/flows?flow_id=invalid")
    assert response.status_code == 500
    assert "error" in response.json()
    
    # Test invalid resource ID
    response = client.get("/api/analytics/resources?resource_id=invalid")
    assert response.status_code == 500
    assert "error" in response.json()
    
    # Test invalid agent ID
    response = client.get("/api/analytics/agents?agent_id=invalid")
    assert response.status_code == 500
    assert "error" in response.json()

@pytest.mark.asyncio
async def test_analytics_integration(mock_orchestration_agent, world):
    """Test analytics integration with orchestration."""
    app.dependency_overrides[get_world] = lambda: world
    # Test flow optimization with analytics
    response = client.post(
        "/api/orchestration/flows/flow1/optimize",
        params={"domain": "professional"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert data["analytics"].get("type") == "behavioral"
    assert "performance" in data["analytics"].get("analytics", {})
    
    # Test resource allocation with analytics
    allocation_request = {
        "resources": {
            "cpu": {"requested": 2},
            "memory": {"requested": "4G"}
        }
    }
    response = client.post(
        "/api/orchestration/resources/allocate",
        json=allocation_request,
        params={"domain": "professional"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert len(data["allocations"]) > 0
    for allocation in data["allocations"]:
        assert "confidence" in allocation
