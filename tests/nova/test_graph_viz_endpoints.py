"""Tests for graph visualization endpoints."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from nia.nova.endpoints.graph_endpoints import graph_viz_router
from nia.nova.core.dependencies import get_graph_store

app = FastAPI()
app.include_router(graph_viz_router)

@pytest.fixture
def mock_graph_store():
    """Create mock graph store."""
    return AsyncMock()

@pytest.fixture
def client(mock_graph_store):
    """Create test client."""
    app.dependency_overrides[get_graph_store] = lambda: mock_graph_store
    return TestClient(app, headers={"X-API-Key": "test-key"})

class TestGraphVizEndpoints:
    """Test graph visualization endpoints."""

    def test_get_nodes(self, client):
        """Test node retrieval endpoint."""
        # Test without metrics
        response = client.get("/api/graph/viz/nodes", params={
            "domain": "test",
            "node_type": "task",
            "include_metrics": False,
            "limit": 10
        })

        assert response.status_code == 200
        assert "nodes" in response.json()
        assert "total_count" in response.json()
        assert "domain_colors" in response.json()
        assert response.json()["metrics"] is None

        # Test with metrics
        response = client.get("/api/graph/viz/nodes", params={
            "domain": "test",
            "node_type": "task",
            "include_metrics": True,
            "limit": 10
        })

        assert response.status_code == 200
        assert "metrics" in response.json()
        assert "node_performance" in response.json()["metrics"]
        assert "node_load" in response.json()["metrics"]
        assert "node_health" in response.json()["metrics"]

    def test_get_pattern_templates(self, client):
        """Test pattern templates endpoint."""
        response = client.get("/api/graph/viz/patterns", params={
            "pattern_type": "hierarchical"
        })

        assert response.status_code == 200
        assert "patterns" in response.json()
        assert "total_count" in response.json()
        assert "timestamp" in response.json()

    def test_get_execution_flow(self, client):
        """Test execution flow endpoint."""
        # Test without metrics
        response = client.get("/api/graph/viz/execution-flow", params={
            "task_id": "task1",
            "include_metrics": False
        })

        assert response.status_code == 200
        assert "nodes" in response.json()
        assert "edges" in response.json()
        assert response.json()["metrics"] is None

        # Test with metrics
        response = client.get("/api/graph/viz/execution-flow", params={
            "task_id": "task1",
            "include_metrics": True
        })

        assert response.status_code == 200
        assert "metrics" in response.json()
        assert "execution_time" in response.json()["metrics"]
        assert "resource_usage" in response.json()["metrics"]
        assert "error_rates" in response.json()["metrics"]

    def test_get_performance_metrics(self, client):
        """Test performance metrics endpoint."""
        response = client.get("/api/graph/viz/performance", params={
            "node_ids": ["node1", "node2"],
            "metric_types": ["performance", "health"],
            "time_range": "1h"
        })

        assert response.status_code == 200
        assert "metrics" in response.json()
        assert "node_metrics" in response.json()["metrics"]
        assert "edge_metrics" in response.json()["metrics"]
        assert "system_metrics" in response.json()["metrics"]
        assert "thresholds" in response.json()

    def test_get_edges(self, client):
        """Test edge retrieval endpoint."""
        response = client.get("/api/graph/viz/edges", params={
            "source_id": "node1",
            "target_id": "node2",
            "edge_type": "depends_on",
            "limit": 10
        })

        assert response.status_code == 200
        assert "edges" in response.json()
        assert "total_count" in response.json()
        assert "timestamp" in response.json()

    def test_get_brand_node_details(self, client):
        """Test brand node details endpoint."""
        response = client.get("/api/graph/viz/nodes/brand1")

        assert response.status_code == 200
        assert response.json()["type"] == "brand"
        assert "inventory_levels" in response.json()["properties"]
        assert "discount_rules" in response.json()["properties"]
        assert "linked_threads" in response.json()
        assert "domain" in response.json()

    def test_get_policy_node_details(self, client):
        """Test policy node details endpoint."""
        response = client.get("/api/graph/viz/nodes/policy1")

        assert response.status_code == 200
        assert response.json()["type"] == "policy"
        assert "rules" in response.json()["properties"]
        assert "affected_brands" in response.json()["properties"]
        assert "linked_threads" in response.json()
        assert "rules" in response.json()["properties"]
        assert "affected_brands" in response.json()["properties"]
        assert "linked_threads" in response.json()

    @pytest.mark.asyncio
    async def test_node_updates_websocket(self, client):
        """Test node updates WebSocket endpoint."""
        with client.websocket_connect("/api/graph/viz/nodes/node1/updates") as websocket:
            data = websocket.receive_json()
            assert "node_id" in data
            assert data["type"] == "property_update"
            assert "changes" in data
            assert "timestamp" in data

    def test_update_node_style(self, client):
        """Test node style update endpoint."""
        response = client.post("/api/graph/viz/nodes/node1/style", json={
            "style": {
                "color": "#ff0000",
                "size": 20,
                "shape": "circle"
            },
            "domain_specific": True
        })

        assert response.status_code == 200
        assert "style" in response.json()
        assert response.json()["domain_specific"] is True

    def test_get_node_neighbors(self, client):
        """Test node neighbors endpoint."""
        response = client.get("/api/graph/viz/nodes/test_node/neighbors", params={
            "edge_type": "depends_on",
            "direction": "out",
            "limit": 10
        })

        assert response.status_code == 200
        assert "node_id" in response.json()
        assert "neighbors" in response.json()
        assert "total_count" in response.json()
        assert "timestamp" in response.json()

    def test_search_graph(self, client):
        """Test graph search endpoint."""
        response = client.post("/api/graph/viz/search", json={
            "query": "test",
            "node_types": ["task", "agent"],
            "edge_types": ["depends_on"],
            "limit": 10
        })

        assert response.status_code == 200
        assert "nodes" in response.json()
        assert "edges" in response.json()
        assert "total_count" in response.json()
        assert "timestamp" in response.json()

    def test_get_task_graph_with_outputs(self, client):
        """Test task graph retrieval with output types."""
        response = client.get("/api/graph/viz/tasks", params={
            "task_id": "task1",
            "status": "active",
            "output_type": "code",
            "limit": 10
        })

        assert response.status_code == 200
        assert "tasks" in response.json()
        assert "dependencies" in response.json()
        assert "output_stats" in response.json()
        assert all(output_type in response.json()["output_stats"] 
                  for output_type in ["code", "media", "new_skill", "document", "api_call"])
        assert "total_count" in response.json()
        assert "timestamp" in response.json()

    def test_get_task_output(self, client):
        """Test task output details endpoint."""
        response = client.get("/api/graph/viz/tasks/task1/output")

        assert response.status_code == 200
        assert "task_id" in response.json()
        assert "output_type" in response.json()
        assert "output_data" in response.json()
        assert "status" in response.json()
        assert "references" in response.json()
        assert all(ref_type in response.json()["references"] 
                  for ref_type in ["neo4j_node", "qdrant_id", "external_url"])

    def test_get_output_stats(self, client):
        """Test output statistics endpoint."""
        response = client.get("/api/graph/viz/tasks/outputs/stats", params={
            "start_date": "2025-01-01",
            "end_date": "2025-01-08",
            "domain": "professional"
        })

        assert response.status_code == 200
        assert "output_types" in response.json()
        assert all(output_type in response.json()["output_types"] 
                  for output_type in ["code", "media", "new_skill", "document", "api_call"])
        assert "domains" in response.json()
        assert all(domain in response.json()["domains"] 
                  for domain in ["professional", "personal"])

    def test_get_graph_layout(self, client):
        """Test graph layout endpoint."""
        response = client.get("/api/graph/viz/layout", params={
            "algorithm": "force"
        })

        assert response.status_code == 200
        assert "layout" in response.json()
        assert "timestamp" in response.json()

    def test_get_visualization_stats(self, client):
        """Test visualization statistics endpoint."""
        response = client.get("/api/graph/viz/stats")

        assert response.status_code == 200
        assert "node_count" in response.json()
        assert "edge_count" in response.json()
        assert "node_types" in response.json()
        assert "edge_types" in response.json()
        assert "domains" in response.json()
        assert "timestamp" in response.json()

    def test_filter_graph(self, client):
        """Test graph filtering endpoint."""
        response = client.post("/api/graph/viz/filter", json={
            "node_types": ["task"],
            "edge_types": ["depends_on"],
            "domains": ["test"],
            "date_range": {
                "start": "2025-01-01",
                "end": "2025-01-08"
            }
        })

        assert response.status_code == 200
        assert "nodes" in response.json()
        assert "edges" in response.json()
        assert "total_count" in response.json()
        assert "timestamp" in response.json()

    def test_invalid_layout_algorithm(self, client):
        """Test invalid layout algorithm handling."""
        response = client.get("/api/graph/viz/layout", params={
            "algorithm": "invalid"
        })
        assert response.status_code == 422

    def test_invalid_node_id(self, client):
        """Test handling of non-existent node."""
        response = client.get("/api/graph/viz/nodes/nonexistent")
        assert response.status_code == 404

    def test_invalid_direction(self, client):
        """Test invalid neighbor direction handling."""
        response = client.get("/api/graph/viz/nodes/test_node/neighbors", params={
            "direction": "invalid"
        })
        assert response.status_code == 422

    def test_invalid_filter_criteria(self, client):
        """Test invalid filter criteria handling."""
        response = client.post("/api/graph/viz/filter", json={
            "date_range": {
                "start": "invalid"
            }
        })
        assert response.status_code == 422

    def test_large_limit(self, client):
        """Test handling of large limit parameter."""
        response = client.get("/api/graph/viz/nodes", params={
            "limit": 2000  # Above maximum
        })
        assert response.status_code == 422
