"""Tests for chat system endpoints."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from nia.nova.endpoints.chat_endpoints import chat_router
from nia.nova.core.dependencies import get_coordination_agent

app = FastAPI()
app.include_router(chat_router)

@pytest.fixture
def mock_coordination_agent():
    """Create mock coordination agent."""
    return AsyncMock()

@pytest.fixture
def client(mock_coordination_agent):
    """Create test client."""
    app.dependency_overrides[get_coordination_agent] = lambda: mock_coordination_agent
    return TestClient(app)

class TestChatEndpoints:
    """Test chat system endpoints."""

    def test_create_thread_with_emergent_tasks(self, client):
        """Test thread creation with emergent task support."""
        # Test main thread creation
        response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })

        assert response.status_code == 200
        assert "thread_id" in response.json()
        assert response.json()["type"] == "main"
        assert response.json()["status"] == "active"
        assert response.json()["aggregation_enabled"] is False
        assert "emergent_tasks" in response.json()
        assert "output_types" in response.json()
        assert all(output_type in response.json()["output_types"] 
                  for output_type in ["code", "media", "new_skill", "document", "api_call"])

    def test_create_emergent_task(self, client):
        """Test emergent task creation."""
        # Create thread first
        thread_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = thread_response.json()["thread_id"]

        # Create task
        response = client.post(f"/api/chat/threads/{thread_id}/tasks", json={
            "description": "Create a new function",
            "output_type": "code",
            "domain": "professional"
        })

        assert response.status_code == 200
        assert "task_id" in response.json()
        assert response.json()["output_type"] == "code"
        assert response.json()["status"] == "pending"

    def test_update_task_status(self, client):
        """Test task status update."""
        # Create thread and task
        thread_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = thread_response.json()["thread_id"]

        task_response = client.post(f"/api/chat/threads/{thread_id}/tasks", json={
            "description": "Create a new function",
            "output_type": "code",
            "domain": "professional"
        })
        task_id = task_response.json()["task_id"]

        # Update task status
        response = client.post(
            f"/api/chat/threads/{thread_id}/tasks/{task_id}/status",
            json={
                "status": "completed",
                "output_data": {
                    "code": "def test(): pass",
                    "language": "python"
                }
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert "output_data" in response.json()

    def test_get_thread_tasks(self, client):
        """Test task listing endpoint."""
        # Create thread
        thread_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = thread_response.json()["thread_id"]

        # Get tasks
        response = client.get(
            f"/api/chat/threads/{thread_id}/tasks",
            params={
                "status": "pending",
                "output_type": "code"
            }
        )

        assert response.status_code == 200
        assert "tasks" in response.json()
        assert "total_count" in response.json()

        # Test sub-thread creation
        main_thread_id = response.json()["thread_id"]
        response = client.post("/api/chat/threads", json={
            "title": "Sub Thread",
            "type": "sub-thread",
            "parent_id": main_thread_id,
            "domain": "test"
        })

        assert response.status_code == 200
        assert response.json()["type"] == "sub-thread"
        assert response.json()["parent_id"] == main_thread_id
        assert response.json()["aggregation_enabled"] is True

    def test_thread_status_update(self, client):
        """Test thread status update endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Update status
        response = client.post(
            f"/api/chat/threads/{thread_id}/status",
            json={"status": "archived"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "archived"

    def test_get_thread_summary(self, client):
        """Test thread summary endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "sub-thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Get summary
        response = client.get(f"/api/chat/threads/{thread_id}/summary")

        assert response.status_code == 200
        assert "summary" in response.json()
        assert "key_points" in response.json()

    def test_get_thread_children(self, client):
        """Test thread children endpoint."""
        # Create main thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Main Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Get children
        response = client.get(f"/api/chat/threads/{thread_id}/children")

        assert response.status_code == 200
        assert "children" in response.json()
        assert "total_count" in response.json()

    def test_get_thread_with_logs(self, client):
        """Test thread retrieval with different log visibility."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Test with partial logs
        response = client.get(
            f"/api/chat/threads/{thread_id}",
            params={"show_partial_logs": True}
        )

        assert response.status_code == 200
        assert response.json()["thread_id"] == thread_id
        assert "chain_of_thought" in response.json()
        assert "domain_references" in response.json()
        assert "graph_nodes" in response.json()
        assert "metadata" in response.json()

        # Test without partial logs
        response = client.get(
            f"/api/chat/threads/{thread_id}",
            params={"show_partial_logs": False}
        )

        assert response.status_code == 200
        assert response.json()["chain_of_thought"] is None

    def test_update_log_visibility(self, client):
        """Test log visibility update endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Update log visibility
        response = client.post(
            f"/api/chat/threads/{thread_id}/logs",
            json={
                "show_partial_logs": False,
                "show_agent_thoughts": True
            }
        )

        assert response.status_code == 200
        assert response.json()["show_partial_logs"] is False
        assert response.json()["show_agent_thoughts"] is True

    def test_link_thread_to_graph(self, client):
        """Test thread-graph linking endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "type": "main",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Link to graph nodes
        response = client.post(
            f"/api/chat/threads/{thread_id}/link",
            json={
                "node_ids": ["node1", "node2"],
                "link_type": "depends_on"
            }
        )

        assert response.status_code == 200
        assert "node_ids" in response.json()
        assert "link_type" in response.json()

    def test_add_message(self, client):
        """Test message addition endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Add message
        response = client.post(
            f"/api/chat/threads/{thread_id}/messages",
            json={
                "content": "Test message",
                "type": "user"
            }
        )

        assert response.status_code == 200
        assert "message_id" in response.json()
        assert response.json()["thread_id"] == thread_id

    def test_get_thread_agents(self, client):
        """Test thread agents retrieval endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Get agents
        response = client.get(f"/api/chat/threads/{thread_id}/agents")

        assert response.status_code == 200
        assert "agents" in response.json()
        assert response.json()["thread_id"] == thread_id

    def test_search_thread(self, client):
        """Test thread search endpoint."""
        # Create thread and add messages
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        client.post(
            f"/api/chat/threads/{thread_id}/messages",
            json={
                "content": "Test message",
                "type": "user"
            }
        )

        # Search thread
        response = client.post(
            f"/api/chat/threads/{thread_id}/search",
            json={
                "query": "test",
                "limit": 10
            }
        )

        assert response.status_code == 200
        assert "matches" in response.json()
        assert response.json()["thread_id"] == thread_id

    @pytest.mark.asyncio
    async def test_thread_websocket(self, client):
        """Test thread WebSocket endpoint."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Test WebSocket connection
        with client.websocket_connect(f"/api/chat/threads/{thread_id}/ws") as websocket:
            # Send message
            websocket.send_json({
                "type": "message",
                "content": "Test message"
            })

            # Receive response
            data = websocket.receive_json()
            assert data["type"] == "message"
            assert "content" in data
            assert "timestamp" in data

    def test_thread_not_found(self, client):
        """Test handling of non-existent thread."""
        response = client.get("/api/chat/threads/nonexistent")
        assert response.status_code == 404

    def test_invalid_message(self, client):
        """Test handling of invalid message data."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Try to add invalid message
        response = client.post(
            f"/api/chat/threads/{thread_id}/messages",
            json={}  # Invalid: missing required fields
        )
        assert response.status_code == 422

    def test_search_validation(self, client):
        """Test search request validation."""
        # Create thread
        create_response = client.post("/api/chat/threads", json={
            "title": "Test Thread",
            "domain": "test"
        })
        thread_id = create_response.json()["thread_id"]

        # Try invalid search
        response = client.post(
            f"/api/chat/threads/{thread_id}/search",
            json={
                "limit": "invalid"  # Invalid: should be integer
            }
        )
        assert response.status_code == 422
