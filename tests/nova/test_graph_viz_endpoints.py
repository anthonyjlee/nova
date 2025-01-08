"""Tests for graph visualization endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from nia.nova.endpoints.graph_endpoints import router, get_graph_store
from nia.memory.types.memory_types import TaskOutput, OutputType, TaskStatus
from nia.core.types.graph_types import GraphNode, GraphEdge, GraphLayout

@pytest.fixture
def mock_graph_store():
    """Mock graph store for testing."""
    store = Mock()
    store.get_tasks = AsyncMock(return_value=[])
    store.get_task_outputs = AsyncMock(return_value=[])
    store.get_task_statistics = AsyncMock(return_value={"total_tasks": 0, "completed": 0, "in_progress": 0, "pending": 0, "output_types": {}})
    store.get_graph_layout = AsyncMock(return_value={"layout": "hierarchical", "positions": {}, "dimensions": {"width": 800, "height": 600}})
    store.search_graph = AsyncMock(return_value={"nodes": [], "edges": []})
    store.filter_graph = AsyncMock(return_value={"nodes": [], "edges": []})
    return store

@pytest.fixture
def app():
    """Create FastAPI app."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.fixture
def client(app, mock_graph_store):
    """Test client with mocked dependencies."""
    async def get_mock_store():
        return mock_graph_store
    app.dependency_overrides = {
        get_graph_store: get_mock_store
    }
    return TestClient(app)

@pytest.mark.asyncio
async def test_get_task_graph(client, mock_graph_store):
    """Test getting task dependency graph."""
    # Mock task data
    tasks = [
        {
            "id": "task1",
            "name": "Root Task",
            "status": TaskStatus.COMPLETED,
            "dependencies": []
        },
        {
            "id": "task2", 
            "name": "Subtask 1",
            "status": TaskStatus.IN_PROGRESS,
            "dependencies": ["task1"]
        },
        {
            "id": "task3",
            "name": "Subtask 2", 
            "status": TaskStatus.PENDING,
            "dependencies": ["task1"]
        }
    ]
    
    # Expected graph structure
    expected = {
        "nodes": [
            {
                "id": "task1",
                "label": "Root Task",
                "type": "task",
                "metadata": {"status": "completed"}
            },
            {
                "id": "task2",
                "label": "Subtask 1",
                "type": "task",
                "metadata": {"status": "in_progress"}
            },
            {
                "id": "task3",
                "label": "Subtask 2",
                "type": "task",
                "metadata": {"status": "pending"}
            }
        ],
        "edges": [
            {
                "from_": "task1",
                "to": "task2",
                "type": "depends_on",
                "metadata": None
            },
            {
                "from_": "task1",
                "to": "task3",
                "type": "depends_on",
                "metadata": None
            }
        ]
    }
    
    mock_graph_store.get_tasks.return_value = tasks
    response = client.get("/graph/tasks")
    assert response.status_code == 200
    assert response.json() == expected

@pytest.mark.asyncio
async def test_get_task_outputs(client, mock_graph_store):
    """Test getting task output visualization."""
    # Mock output data
    outputs = [
        TaskOutput(
            task_id="task1",
            type=OutputType.CODE,
            content="def hello(): print('Hello')",
            metadata={"language": "python"}
        ),
        TaskOutput(
            task_id="task1", 
            type=OutputType.DOCUMENT,
            content="API Documentation",
            metadata={"format": "markdown"}
        )
    ]
    
    # Expected graph structure
    expected = {
        "nodes": [
            {
                "id": "task1",
                "label": "Task task1",
                "type": "task",
                "metadata": None
            },
            {
                "id": "output1",
                "label": "Code Output",
                "type": "output",
                "metadata": {
                    "output_type": "code",
                    "language": "python"
                }
            },
            {
                "id": "output2",
                "label": "Document Output",
                "type": "output",
                "metadata": {
                    "output_type": "document",
                    "format": "markdown"
                }
            }
        ],
        "edges": [
            {
                "from_": "task1",
                "to": "output1",
                "type": "produces",
                "metadata": None
            },
            {
                "from_": "task1",
                "to": "output2",
                "type": "produces",
                "metadata": None
            }
        ]
    }
    
    mock_graph_store.get_task_outputs.return_value = outputs
    response = client.get("/graph/tasks/task1/outputs")
    assert response.status_code == 200
    assert response.json() == expected

@pytest.mark.asyncio
async def test_get_task_statistics(client, mock_graph_store):
    """Test getting task statistics visualization."""
    # Mock statistics data
    stats = {
        "total_tasks": 10,
        "completed": 5,
        "in_progress": 3,
        "pending": 2,
        "output_types": {
            "code": 3,
            "document": 4,
            "media": 2,
            "api": 1
        }
    }
    
    # Expected graph structure
    expected = {
        "nodes": [
            {
                "id": "stats",
                "label": "Task Statistics",
                "type": "stats",
                "metadata": {"total": 10}
            },
            {
                "id": "completed",
                "label": "Completed",
                "type": "status",
                "metadata": {"count": 5}
            },
            {
                "id": "in_progress",
                "label": "In Progress",
                "type": "status",
                "metadata": {"count": 3}
            },
            {
                "id": "pending",
                "label": "Pending",
                "type": "status",
                "metadata": {"count": 2}
            },
            {
                "id": "outputs",
                "label": "Output Types",
                "type": "outputs",
                "metadata": None
            },
            {
                "id": "code",
                "label": "Code",
                "type": "output_type",
                "metadata": {"count": 3}
            },
            {
                "id": "document",
                "label": "Document",
                "type": "output_type",
                "metadata": {"count": 4}
            },
            {
                "id": "media",
                "label": "Media",
                "type": "output_type",
                "metadata": {"count": 2}
            },
            {
                "id": "api",
                "label": "Api",
                "type": "output_type",
                "metadata": {"count": 1}
            }
        ],
        "edges": [
            {
                "from_": "stats",
                "to": "completed",
                "type": "has_status",
                "metadata": None
            },
            {
                "from_": "stats",
                "to": "in_progress",
                "type": "has_status",
                "metadata": None
            },
            {
                "from_": "stats",
                "to": "pending",
                "type": "has_status",
                "metadata": None
            },
            {
                "from_": "stats",
                "to": "outputs",
                "type": "has_outputs",
                "metadata": None
            },
            {
                "from_": "outputs",
                "to": "code",
                "type": "output_type",
                "metadata": None
            },
            {
                "from_": "outputs",
                "to": "document",
                "type": "output_type",
                "metadata": None
            },
            {
                "from_": "outputs",
                "to": "media",
                "type": "output_type",
                "metadata": None
            },
            {
                "from_": "outputs",
                "to": "api",
                "type": "output_type",
                "metadata": None
            }
        ]
    }
    
    mock_graph_store.get_task_statistics.return_value = stats
    response = client.get("/graph/tasks/statistics")
    assert response.status_code == 200
    assert response.json() == expected

@pytest.mark.asyncio
async def test_get_task_layout(client, mock_graph_store):
    """Test getting task graph layout."""
    # Mock graph data
    graph = {
        "nodes": [
            GraphNode(id="task1", label="Task 1", type="task"),
            GraphNode(id="task2", label="Task 2", type="task"),
            GraphNode(id="task3", label="Task 3", type="task")
        ],
        "edges": [
            GraphEdge(from_="task1", to="task2", type="depends_on"),
            GraphEdge(from_="task1", to="task3", type="depends_on")
        ]
    }
    
    # Expected layout
    expected = {
        "layout": GraphLayout.HIERARCHICAL,
        "positions": {
            "task1": {"x": 0, "y": 0},
            "task2": {"x": -100, "y": 100},
            "task3": {"x": 100, "y": 100}
        },
        "dimensions": {
            "width": 800,
            "height": 600
        }
    }
    
    mock_graph_store.get_graph_layout.return_value = expected
    response = client.get("/graph/tasks/layout", 
                         params={"layout": "hierarchical"})
    assert response.status_code == 200
    assert response.json() == expected

@pytest.mark.asyncio
async def test_search_task_graph(client, mock_graph_store):
    """Test searching task graph."""
    # Mock search results
    results = {
        "nodes": [
            GraphNode(id="task1", label="API Task", type="task",
                     metadata={"status": "completed"}),
            GraphNode(id="output1", label="API Documentation", type="output",
                     metadata={"type": "document"})
        ],
        "edges": [
            GraphEdge(from_="task1", to="output1", type="produces")
        ]
    }
    
    mock_graph_store.search_graph.return_value = results
    response = client.get("/graph/search", 
                         params={"query": "API", "types": ["task", "output"]})
    assert response.status_code == 200
    assert response.json() == results

@pytest.mark.asyncio
async def test_filter_task_graph(client, mock_graph_store):
    """Test filtering task graph."""
    # Mock filtered results
    results = {
        "nodes": [
            GraphNode(id="task1", label="Task 1", type="task",
                     metadata={"status": "completed"}),
            GraphNode(id="task2", label="Task 2", type="task", 
                     metadata={"status": "completed"})
        ],
        "edges": [
            GraphEdge(from_="task1", to="task2", type="depends_on")
        ]
    }
    
    mock_graph_store.filter_graph.return_value = results
    response = client.get("/graph/filter",
                         params={"status": "completed"})
    assert response.status_code == 200
    assert response.json() == results
