"""Test WebSocket endpoints and Celery tasks."""

import pytest
import asyncio
import json
import logging
import traceback
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Callable, TypeVar, Optional, Union
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from unittest.mock import Mock, patch
from logging.handlers import RotatingFileHandler

from nia.nova.core.websocket_server import WebSocketServer, ConnectionManager
from nia.nova.core.celery_app import (
    store_chat_message,
    store_task_update,
    store_agent_status,
    store_graph_update
)
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.agent_store import get_agent_store

# Configure JSON logging
LOGS_DIR = Path("test_results/websocket_celery_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_log = LOGS_DIR / f"session_{session_id}.json"

T = TypeVar('T')

class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    @staticmethod
    def safe_convert(value: Any, converter: Callable[[Any], T], default: T) -> T:
        """Safely convert value or return default if conversion fails."""
        if value is None:
            return default
        try:
            return converter(value)
        except (ValueError, TypeError, AttributeError):
            return default

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_entry = {
            "timestamp": self.safe_convert(
                getattr(record, 'created', None),
                lambda x: datetime.fromtimestamp(x).isoformat(),
                datetime.now().isoformat()
            ),
            "level": self.safe_convert(record.levelname, str, "NOTSET"),
            "message": self.safe_convert(record.getMessage(), str, ""),
            "function": self.safe_convert(record.funcName, str, ""),
            "line": self.safe_convert(record.lineno, int, 0),
            "thread_id": self.safe_convert(record.thread, int, 0),
            "process_id": self.safe_convert(record.process, int, 0),
            "test_phase": self.safe_convert(
                getattr(record, 'test_phase', None), 
                str, 
                ""
            ),
            "test_result": self.safe_convert(
                getattr(record, 'test_result', None),
                bool,
                False
            )
        }
        
        if record.exc_info:
            log_entry["exception"] = {
                "type": self.safe_convert(
                    record.exc_info[0] if record.exc_info else None,
                    lambda x: x.__name__,
                    "Exception"
                ),
                "message": self.safe_convert(
                    record.exc_info[1] if record.exc_info else None,
                    str,
                    ""
                ),
                "traceback": self.safe_convert(
                    record.exc_info,
                    lambda x: traceback.format_exception(*x),
                    []
                )
            }
            
        return json.dumps(log_entry)

# Configure logging with RotatingFileHandler
logger = logging.getLogger("test_websocket_celery")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    session_log,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

def create_test_result(test_name: str, success: bool, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a test result entry."""
    return {
        "test_name": test_name,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }

class TestResults:
    """Manage test results and output."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        
    def add_result(self, test_name: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """Add a test result."""
        self.results.append(create_test_result(test_name, success, details))
        
    def save_results(self) -> Path:
        """Save results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = LOGS_DIR / f"test_results_{timestamp}.json"
        
        # Save test results
        with open(filename, 'w') as f:
            json.dump({
                "session_id": session_id,
                "summary": {
                    "total_tests": len(self.results),
                    "passed": sum(1 for r in self.results if r["success"]),
                    "failed": sum(1 for r in self.results if not r["success"])
                },
                "results": self.results
            }, f, indent=2)
            
        # Also log results to JSON handler
        for result in self.results:
            logger.info(
                f"Test {result['test_name']}: {'PASSED' if result['success'] else 'FAILED'}",
                extra={
                    "test_phase": result["test_name"],
                    "test_result": result["success"]
                }
            )
            if not result["success"] and "error" in result.get("details", {}):
                logger.error(
                    f"Test {result['test_name']} error: {result['details']['error']}",
                    extra={
                        "test_phase": result["test_name"],
                        "test_result": False
                    }
                )
        
        return filename

@pytest.fixture
async def memory_system():
    """Create memory system fixture."""
    system = TwoLayerMemorySystem()
    await system.initialize()
    return system

@pytest.fixture
def websocket_server(memory_system):
    """Create WebSocket server fixture."""
    return WebSocketServer(lambda: memory_system)

@pytest.fixture
def connection_manager():
    """Create connection manager fixture."""
    return ConnectionManager()

async def test_websocket_connection(websocket_server, connection_manager):
    """Test WebSocket connection handling."""
    logger.info("Starting WebSocket connection test", extra={"test_phase": "websocket_connection"})
    
    try:
        # Mock WebSocket and test connection
        websocket = Mock(spec=WebSocket)
        websocket.send_json = Mock()
        client_id = "test-client"
        
        await websocket_server.handle_chat_connection(websocket, client_id)
        
        # Verify connection and message
        websocket.send_json.assert_called_once()
        message = websocket.send_json.call_args[0][0]
        assert message["type"] == "connection_success", "Wrong message type"
        assert message["client_id"] == client_id, "Wrong client ID"
        assert "timestamp" in message, "Missing timestamp"
        assert "data" in message, "Missing data field"
        
        logger.info("WebSocket connection test passed", 
                   extra={"test_phase": "websocket_connection", "test_result": True})
        
    except Exception as e:
        logger.error(f"WebSocket connection test failed: {str(e)}", 
                    extra={"test_phase": "websocket_connection", "test_result": False})
        logger.error(traceback.format_exc())
        raise

async def test_chat_message_handling(websocket_server):
    """Test chat message handling and storage."""
    logger.info("Starting chat message handling test", extra={"test_phase": "chat_message"})
    
    try:
        # Test message handling
        websocket = Mock(spec=WebSocket)
        websocket.send_json = Mock()
        test_message = {
            "type": "message",
            "timestamp": datetime.now().isoformat(),
            "client_id": "test-client",
            "channel": None,
            "data": {
                "thread_id": "test-thread", 
                "content": "Test message",
                "sender": "test-user"
            }
        }
        websocket.receive_json = Mock(return_value=test_message)
        
        with patch('nia.nova.core.websocket_server.store_chat_message') as mock_task:
            await websocket_server.handle_chat_connection(websocket, "test-client")
            
            mock_task.delay.assert_called_once()
            task_args = mock_task.delay.call_args[0][0]
            assert task_args["thread_id"] == "test-thread", "Wrong thread ID"
            assert task_args["content"] == "Test message", "Wrong message content"
            
            logger.info("Chat message handling test passed", 
                       extra={"test_phase": "chat_message", "test_result": True})
            
    except Exception as e:
        logger.error(f"Chat message handling test failed: {str(e)}", 
                    extra={"test_phase": "chat_message", "test_result": False})
        logger.error(traceback.format_exc())
        raise

async def test_task_update_handling(websocket_server):
    """Test task update handling and storage."""
    logger.info("Starting task update handling test", extra={"test_phase": "task_update"})
    
    try:
        # Test task update handling
        websocket = Mock(spec=WebSocket)
        websocket.send_json = Mock()
        test_update = {
            "type": "task_update",
            "timestamp": datetime.now().isoformat(),
            "client_id": "test-client",
            "channel": None,
            "data": {
                "thread_id": "test-thread",
                "task_id": "test-task",
                "status": "in_progress"
            }
        }
        websocket.receive_json = Mock(return_value=test_update)
        
        with patch('nia.nova.core.websocket_server.store_task_update') as mock_task:
            await websocket_server.handle_task_connection(websocket, "test-client")
            
            mock_task.delay.assert_called_once()
            task_args = mock_task.delay.call_args[0][0]
            assert task_args["thread_id"] == "test-thread", "Wrong thread ID"
            assert task_args["task_id"] == "test-task", "Wrong task ID"
            assert task_args["status"] == "in_progress", "Wrong status"
            
            logger.info("Task update handling test passed", 
                       extra={"test_phase": "task_update", "test_result": True})
            
    except Exception as e:
        logger.error(f"Task update handling test failed: {str(e)}", 
                    extra={"test_phase": "task_update", "test_result": False})
        logger.error(traceback.format_exc())
        raise

async def test_agent_status_handling(websocket_server):
    """Test agent status handling and storage."""
    logger.info("Starting agent status handling test", extra={"test_phase": "agent_status"})
    
    try:
        # Test agent status handling
        websocket = Mock(spec=WebSocket)
        websocket.send_json = Mock()
        test_status = {
            "type": "agent_status",
            "timestamp": datetime.now().isoformat(),
            "client_id": "test-client",
            "channel": None,
            "data": {
                "agent_id": "test-agent",
                "status": "active",
                "metadata": {"task": "test-task"}
            }
        }
        websocket.receive_json = Mock(return_value=test_status)
        
        with patch('nia.nova.core.websocket_server.store_agent_status') as mock_task:
            await websocket_server.handle_agent_connection(websocket, "test-client")
            
            mock_task.delay.assert_called_once()
            task_args = mock_task.delay.call_args[0][0]
            assert task_args["agent_id"] == "test-agent", "Wrong agent ID"
            assert task_args["status"] == "active", "Wrong status"
            
            logger.info("Agent status handling test passed", 
                       extra={"test_phase": "agent_status", "test_result": True})
            
    except Exception as e:
        logger.error(f"Agent status handling test failed: {str(e)}", 
                    extra={"test_phase": "agent_status", "test_result": False})
        logger.error(traceback.format_exc())
        raise

async def test_graph_update_handling(websocket_server):
    """Test graph update handling and storage."""
    logger.info("Starting graph update handling test", extra={"test_phase": "graph_update"})
    
    try:
        # Test graph update handling
        websocket = Mock(spec=WebSocket)
        websocket.send_json = Mock()
        test_update = {
            "type": "graph_update",
            "timestamp": datetime.now().isoformat(),
            "client_id": "test-client",
            "channel": None,
            "data": {
                "nodes": [{"id": "node1", "type": "concept"}],
                "edges": [{"from": "node1", "to": "node2", "type": "related"}]
            }
        }
        websocket.receive_json = Mock(return_value=test_update)
        
        with patch('nia.nova.core.websocket_server.store_graph_update') as mock_task:
            await websocket_server.handle_graph_connection(websocket, "test-client")
            
            mock_task.delay.assert_called_once()
            task_args = mock_task.delay.call_args[0][0]
            assert len(task_args["nodes"]) == 1, "Wrong number of nodes"
            assert len(task_args["edges"]) == 1, "Wrong number of edges"
            
            logger.info("Graph update handling test passed", 
                       extra={"test_phase": "graph_update", "test_result": True})
            
    except Exception as e:
        logger.error(f"Graph update handling test failed: {str(e)}", 
                    extra={"test_phase": "graph_update", "test_result": False})
        logger.error(traceback.format_exc())
        raise

async def test_broadcast_message(connection_manager):
    """Test message broadcasting to connected clients."""
    logger.info("Starting broadcast message test", extra={"test_phase": "broadcast"})
    
    try:
        # Test broadcast functionality
        websocket1 = Mock(spec=WebSocket)
        websocket1.send_json = Mock()
        websocket2 = Mock(spec=WebSocket)
        websocket2.send_json = Mock()
        
        await connection_manager.connect(websocket1, "client1", "chat")
        await connection_manager.connect(websocket2, "client2", "chat")
        
        message = {
            "type": "message",
            "timestamp": datetime.now().isoformat(),
            "client_id": "server",
            "channel": "chat",
            "data": {
                "content": "Test broadcast"
            }
        }
        await connection_manager.broadcast(message, "chat")
        
        websocket1.send_json.assert_called_once()
        websocket2.send_json.assert_called_once()
        
        broadcast1 = websocket1.send_json.call_args[0][0]
        broadcast2 = websocket2.send_json.call_args[0][0]
        assert broadcast1["data"]["content"] == "Test broadcast", "Wrong message content for client 1"
        assert broadcast2["data"]["content"] == "Test broadcast", "Wrong message content for client 2"
        
        logger.info("Broadcast message test passed", 
                   extra={"test_phase": "broadcast", "test_result": True})
        
    except Exception as e:
        logger.error(f"Broadcast message test failed: {str(e)}", 
                    extra={"test_phase": "broadcast", "test_result": False})
        logger.error(traceback.format_exc())
        raise

@pytest.mark.celery
async def test_store_chat_message():
    """Test chat message storage Celery task."""
    logger.info("Starting chat message storage test", extra={"test_phase": "celery_chat"})
    
    try:
        # Test chat message storage
        message_data = {
            "thread_id": "test-thread",
            "content": "Test message",
            "sender": "test-user",
            "timestamp": datetime.now().isoformat()
        }
        
        result = store_chat_message.delay(message_data)
        assert result.successful(), "Task failed to execute"
        
        memory = TwoLayerMemorySystem()
        await memory.initialize()
        stored_thread = await memory.get_experience("test-thread")
        assert stored_thread is not None, "Thread not found"
        assert isinstance(stored_thread.content, dict), "Thread content not found"
        messages = stored_thread.content.get("messages", [])
        assert messages, "No messages in thread"
        
        latest_message = messages[-1]
        assert isinstance(latest_message, dict), "Message should be a dictionary"
        assert latest_message.get("content") == "Test message", "Wrong message content"
        
        logger.info("Chat message storage test passed", 
                   extra={"test_phase": "celery_chat", "test_result": True})
        
    except Exception as e:
        logger.error(f"Chat message storage test failed: {str(e)}", 
                    extra={"test_phase": "celery_chat", "test_result": False})
        logger.error(traceback.format_exc())
        raise

@pytest.mark.celery
async def test_store_task_update():
    """Test task update storage Celery task."""
    logger.info("Starting task update storage test", extra={"test_phase": "celery_task"})
    
    try:
        # Test task update storage
        task_data = {
            "thread_id": "test-thread",
            "task_id": "test-task",
            "status": "completed",
            "metadata": {
                "completion_time": datetime.now().isoformat()
            }
        }
        
        result = store_task_update.delay(task_data)
        assert result.successful(), "Task failed to execute"
        
        memory = TwoLayerMemorySystem()
        await memory.initialize()
        stored_thread = await memory.get_experience("test-thread")
        assert stored_thread is not None, "Thread not found"
        assert isinstance(stored_thread.metadata, dict), "Thread metadata not found"
        tasks = stored_thread.metadata.get("tasks", [])
        assert tasks, "No tasks in thread metadata"
        
        matching_tasks = [t for t in tasks if isinstance(t, dict) and t.get("id") == "test-task"]
        assert matching_tasks, "Task not found"
        task = matching_tasks[0]
        assert task.get("status") == "completed", "Wrong task status"
        
        logger.info("Task update storage test passed", 
                   extra={"test_phase": "celery_task", "test_result": True})
        
    except Exception as e:
        logger.error(f"Task update storage test failed: {str(e)}", 
                    extra={"test_phase": "celery_task", "test_result": False})
        logger.error(traceback.format_exc())
        raise

@pytest.mark.celery
async def test_store_agent_status():
    """Test agent status storage Celery task."""
    logger.info("Starting agent status storage test", extra={"test_phase": "celery_agent"})
    
    try:
        # Test agent status storage
        status_data = {
            "agent_id": "test-agent",
            "status": "active",
            "metadata": {
                "current_task": "test-task",
                "updated_at": datetime.now().isoformat()
            }
        }
        
        result = store_agent_status.delay(status_data)
        assert result.successful(), "Task failed to execute"
        
        agent_store = await get_agent_store()
        agent = await agent_store.get_agent("test-agent")
        assert agent is not None, "Agent not found"
        assert agent["status"] == "active", "Wrong agent status"
        assert agent["metadata"]["current_task"] == "test-task", "Wrong task in metadata"
        
        logger.info("Agent status storage test passed", 
                   extra={"test_phase": "celery_agent", "test_result": True})
        
    except Exception as e:
        logger.error(f"Agent status storage test failed: {str(e)}", 
                    extra={"test_phase": "celery_agent", "test_result": False})
        logger.error(traceback.format_exc())
        raise

@pytest.mark.celery
async def test_store_graph_update():
    """Test graph update storage Celery task."""
    logger.info("Starting graph update storage test", extra={"test_phase": "celery_graph"})
    
    try:
        # Test graph update storage
        graph_data = {
            "nodes": [
                {
                    "id": "concept1",
                    "type": "concept",
                    "metadata": {"domain": "test"}
                }
            ],
            "edges": [
                {
                    "from": "concept1",
                    "to": "concept2",
                    "type": "related",
                    "metadata": {"weight": 0.8}
                }
            ]
        }
        
        result = store_graph_update.delay(graph_data)
        assert result.successful(), "Task failed to execute"
        
        memory_system = TwoLayerMemorySystem()
        await memory_system.initialize()
        for node in graph_data["nodes"]:
            stored_node = await memory_system.get_experience(node["id"])
            assert stored_node is not None, f"Node {node['id']} not found"
            assert stored_node.type == node["type"], "Wrong node type"
            
        logger.info("Graph update storage test passed", 
                   extra={"test_phase": "celery_graph", "test_result": True})
        
    except Exception as e:
        logger.error(f"Graph update storage test failed: {str(e)}", 
                    extra={"test_phase": "celery_graph", "test_result": False})
        logger.error(traceback.format_exc())
        raise
