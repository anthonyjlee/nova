"""Tests for Nova's analytics endpoints."""

import pytest
import asyncio
import logging
from fastapi.testclient import TestClient
from datetime import datetime
import websockets
from unittest.mock import AsyncMock

from src.nia.nova.core.app import app
from src.nia.nova.core.analytics import AnalyticsAgent, AnalyticsResult
from src.nia.agents.specialized.orchestration_agent import OrchestrationAgent
from src.nia.nova.core.endpoints import get_world, get_analytics_agent, get_orchestration_agent
from src.nia.nova.core.auth import get_api_key
from src.nia.nova.core.error_handling import ResourceNotFoundError, ValidationError
from src.nia.world.environment import NIAWorld

logger = logging.getLogger(__name__)

client = TestClient(app)

@pytest.fixture(autouse=True)
async def cleanup_world():
    """Reset NIAWorld singleton between tests."""
    NIAWorld._instance = None
    yield
    NIAWorld._instance = None

@pytest.fixture
async def world():
    """Create world instance for testing."""
    # Generate unique name for each test
    world = NIAWorld(name=f"NIAWorld_{datetime.now().timestamp()}")
    world.state["tasks_paused"] = False
    return world

@pytest.fixture(autouse=True)
def mock_api_key():
    """Mock API key authentication."""
    from src.nia.nova.core.auth import API_KEYS, get_ws_api_key
    API_KEYS["test-key"] = {
        "permissions": ["read", "write"],
        "rate_limit": {
            "requests": 100,
            "window": 60
        }
    }
    app.dependency_overrides[get_api_key] = lambda: "test-key"
    app.dependency_overrides[get_ws_api_key] = lambda websocket: "test-key"
    yield
    if "test-key" in API_KEYS:
        del API_KEYS["test-key"]
    if get_api_key in app.dependency_overrides:
        del app.dependency_overrides[get_api_key]
    if get_ws_api_key in app.dependency_overrides:
        del app.dependency_overrides[get_ws_api_key]

@pytest.fixture
async def mock_analytics_agent():
    """Create a mock analytics agent with timeout handling."""
    from unittest.mock import AsyncMock
    agent = AsyncMock()
    
    async def process_analytics(*args, **kwargs):
        content = kwargs.get("content", {})
        
        # Handle validation errors for WebSocket test
        if content.get("type") == "invalid_type":
            raise ValidationError("Invalid analytics type")
        elif content.get("type") == "flow_analytics" and content.get("flow_id") == "invalid_flow":
            raise ResourceNotFoundError("Flow not found")
        
        # Return normal result for valid requests
        return AnalyticsResult(
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
        )
    
    agent.process_analytics = AsyncMock(side_effect=process_analytics)
    return agent

@pytest.fixture
async def mock_orchestration_agent(mock_analytics_agent):
    """Create a mock orchestration agent with timeout handling."""
    from unittest.mock import AsyncMock
    agent = AsyncMock()
    agent.analytics = mock_analytics_agent
    agent.active_flows = {
        "flow1": {
            "status": "active",
            "metrics": {"progress": 0.5}
        }
    }
    
    # Add timeout handling to process_flow
    async def process_flow_with_timeout(*args, **kwargs):
        try:
            return await asyncio.wait_for(
                asyncio.create_task(async_flow_result()),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Flow processing timed out")
            return {
                "status": "error",
                "error": "Processing timed out",
                "timestamp": datetime.now().isoformat()
            }
    
    async def async_flow_result():
        return {
            "status": "success",
            "flow_id": "flow1",
            "metrics": {"progress": 1.0},
            "timestamp": datetime.now().isoformat()
        }
    
    # Add timeout handling to allocate_resources
    async def allocate_resources_with_timeout(*args, **kwargs):
        try:
            return await asyncio.wait_for(
                asyncio.create_task(async_allocation_result()),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Resource allocation timed out")
            return {
                "status": "error",
                "error": "Allocation timed out",
                "timestamp": datetime.now().isoformat()
            }
    
    async def async_allocation_result():
        return {
            "status": "success",
            "allocations": [
                {
                    "resource_id": "cpu",
                    "allocated": 2.0,
                    "confidence": 0.9
                },
                {
                    "resource_id": "memory",
                    "allocated": 4.0,
                    "confidence": 0.85
                }
            ],
            "analytics": {
                "type": "resource_allocation",
                "metrics": {
                    "utilization": 0.75,
                    "efficiency": 0.85
                }
            },
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
    
    agent.process_flow.side_effect = process_flow_with_timeout
    agent.allocate_resources.side_effect = allocate_resources_with_timeout
    return agent

@pytest.fixture(autouse=True)
def setup_dependencies(mock_analytics_agent, mock_orchestration_agent):
    """Set up dependencies for all tests."""
    from src.nia.nova.core.endpoints import get_analytics_agent, get_orchestration_agent
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    app.dependency_overrides[get_orchestration_agent] = lambda: mock_orchestration_agent
    yield
    app.dependency_overrides.clear()

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
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_get_flow_analytics(world, mock_analytics_agent, mock_orchestration_agent):
    """Test flow analytics endpoint."""
    try:
        response = client.get("/api/analytics/flows?flow_id=flow1", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data
        
        # Verify analytics agent was called correctly
        mock_analytics_agent.process_analytics.assert_called_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_get_resource_analytics(world, mock_analytics_agent, mock_orchestration_agent):
    """Test resource analytics endpoint."""
    try:
        response = client.get("/api/analytics/resources?resource_id=resource1", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data
        
        # Verify analytics agent was called correctly
        mock_analytics_agent.process_analytics.assert_called_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_get_agent_analytics(world, mock_analytics_agent, mock_orchestration_agent):
    """Test agent analytics endpoint."""
    try:
        response = client.get("/api/analytics/agents?agent_id=agent1", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data
        
        # Verify analytics agent was called correctly
        mock_analytics_agent.process_analytics.assert_called_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_optimize_flow(world, mock_analytics_agent, mock_orchestration_agent):
    """Test flow optimization endpoint."""
    try:
        # Create a proper optimization request
        request = {
            "parameters": {
                "target": "performance",
                "max_iterations": 100
            },
            "constraints": {
                "max_latency": 1000,
                "min_throughput": 100
            }
        }
        
        response = client.post(
            "/api/orchestration/flows/flow1/optimize",
            json=request,
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "flow_id" in data
        assert "optimizations" in data
        assert "analytics" in data
        assert "confidence" in data
        assert "timestamp" in data
        
        # Verify orchestration agent was called correctly
        mock_orchestration_agent.process_flow.assert_called_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_allocate_resources(world, mock_analytics_agent, mock_orchestration_agent):
    """Test resource allocation endpoint."""
    try:
        # Create a proper resource allocation request matching ResourceAllocationRequest model
        allocation_request = {
            "resources": {
                "cpu": {
                    "requested": 2.0,
                    "min": 1.0,
                    "max": 4.0
                },
                "memory": {
                    "requested": 4.0,
                    "min": 2.0,
                    "max": 8.0
                }
            },
            "constraints": {
                "max_cost": 100.0,
                "priority": "high"
            },
            "priority": 3
        }
        
        response = client.post(
            "/api/orchestration/resources/allocate",
            json=allocation_request,
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "allocations" in data
        assert "analytics" in data
        assert "confidence" in data
        assert "timestamp" in data
        
        # Verify orchestration agent was called correctly
        mock_orchestration_agent.allocate_resources.assert_called_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_analytics_websocket(world, mock_analytics_agent):
    """Test analytics WebSocket endpoint."""
    app.dependency_overrides[get_world] = lambda: world
    app.dependency_overrides[get_analytics_agent] = lambda: mock_analytics_agent
    
    # Create a test client that supports WebSocket
    websocket = client.websocket_connect(
        "/api/analytics/ws",
        headers={"X-API-Key": "test-key"}
    ).__enter__()  # Use context manager to ensure proper connection
    
    try:
        # Test valid request
        valid_request = {
            "type": "flow_analytics",
            "flow_id": "flow1",
            "domain": "professional",
            "timestamp": datetime.now().isoformat()
        }
        websocket.send_json(valid_request)
        
        # Verify valid response
        data = websocket.receive_json()
        assert data["type"] == "analytics_update"
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data
        
        # Test invalid request format
        invalid_request = {
            "type": "invalid_type",
            "flow_id": "flow1"
        }
        websocket.send_json(invalid_request)
        
        # Verify error response
        error_data = websocket.receive_json()
        assert error_data["type"] == "error"
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        
        # Test invalid flow ID
        invalid_flow_request = {
            "type": "flow_analytics",
            "flow_id": "invalid_flow",
            "timestamp": datetime.now().isoformat()
        }
        websocket.send_json(invalid_flow_request)
        
        # Verify not found response
        not_found_data = websocket.receive_json()
        assert not_found_data["type"] == "error"
        assert not_found_data["error"]["code"] == "NOT_FOUND"
            
    finally:
        # Ensure WebSocket is closed
        websocket.close()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_domain_specific_analytics(world, mock_analytics_agent, mock_orchestration_agent):
    """Test domain-specific analytics."""
    try:
        response = client.get(
            "/api/analytics/flows",
            params={"flow_id": "flow1", "domain": "personal"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check domain in metadata
        mock_analytics_agent.process_analytics.assert_called_once()
        call_args = mock_analytics_agent.process_analytics.call_args[1]
        assert call_args.get("metadata", {}).get("domain") == "personal"
        
        # Verify analytics data
        assert "analytics" in data
        assert "insights" in data
        assert "confidence" in data
        assert "timestamp" in data
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_analytics_error_handling(world, mock_analytics_agent, mock_orchestration_agent):
    """Test analytics error handling."""
    try:
        # Configure mock to raise ResourceNotFoundError for invalid IDs
        async def mock_process_analytics(*args, **kwargs):
            content = kwargs.get("content", {})
            if content.get("flow_id") == "invalid":
                raise ResourceNotFoundError("Flow not found")
            if content.get("resource_id") == "invalid":
                raise ResourceNotFoundError("Resource not found")
            if content.get("agent_id") == "invalid":
                raise ResourceNotFoundError("Agent not found")
            return AnalyticsResult(
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
                insights=[],
                confidence=0.85
            )
            
        # Replace the entire mock object to ensure clean state
        mock_analytics_agent.process_analytics = AsyncMock(side_effect=mock_process_analytics)
        
        # Test invalid flow ID
        response = client.get("/api/analytics/flows?flow_id=invalid", headers={"X-API-Key": "test-key"})
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        
        # Test invalid resource ID
        response = client.get("/api/analytics/resources?resource_id=invalid", headers={"X-API-Key": "test-key"})
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        
        # Test invalid agent ID
        response = client.get("/api/analytics/agents?agent_id=invalid", headers={"X-API-Key": "test-key"})
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.timeout(30)  # Add timeout of 30 seconds
async def test_analytics_integration(world, mock_analytics_agent, mock_orchestration_agent):
    """Test analytics integration with orchestration."""
    try:
        # Test flow optimization with analytics
        request = {
            "parameters": {
                "target": "performance",
                "max_iterations": 100
            },
            "constraints": {
                "max_latency": 1000,
                "min_throughput": 100
            }
        }
        response = client.post(
            "/api/orchestration/flows/flow1/optimize",
            json=request,
            params={"domain": "professional"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert data["analytics"].get("type") == "behavioral"
        assert "performance" in data["analytics"].get("analytics", {})
        
        # Verify flow optimization called correct methods
        mock_orchestration_agent.process_flow.assert_called_once()
        mock_analytics_agent.process_analytics.assert_called()
        
        # Test resource allocation with analytics
        allocation_request = {
            "resources": {
                "cpu": {
                    "requested": 2.0,
                    "min": 1.0,
                    "max": 4.0
                },
                "memory": {
                    "requested": 4.0,
                    "min": 2.0,
                    "max": 8.0
                }
            },
            "constraints": {
                "max_cost": 100.0,
                "priority": "high"
            },
            "priority": 3
        }
        response = client.post(
            "/api/orchestration/resources/allocate",
            json=allocation_request,
            params={"domain": "professional"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert len(data["allocations"]) > 0
        for allocation in data["allocations"]:
            assert "confidence" in allocation
            
        # Verify resource allocation called correct methods
        mock_orchestration_agent.allocate_resources.assert_called_once()
        assert mock_analytics_agent.process_analytics.call_count >= 2
    finally:
        app.dependency_overrides.clear()
