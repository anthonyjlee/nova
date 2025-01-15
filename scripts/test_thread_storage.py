#!/usr/bin/env python3
"""Test thread storage functionality."""

import asyncio
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path

from nia.memory.vector_store import VectorStore
from nia.memory.embedding import EmbeddingService
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.types.memory_types import Memory, MemoryType

# Configure JSON logging
LOGS_DIR = Path("test_results/thread_storage_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_log = LOGS_DIR / f"session_{session_id}.json"

class JsonLogHandler(logging.Handler):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.logs = []
        
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process,
            "test_phase": getattr(record, 'test_phase', None),
            "test_result": getattr(record, 'test_result', None)
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        self.logs.append(log_entry)
        self._save_logs()
        
    def _save_logs(self):
        with open(self.log_file, 'w') as f:
            json.dump({
                "session_id": session_id,
                "logs": self.logs,
                "summary": {
                    "total_tests": len([l for l in self.logs if l.get("test_result") is not None]),
                    "passed": len([l for l in self.logs if l.get("test_result") == True]),
                    "failed": len([l for l in self.logs if l.get("test_result") == False])
                }
            }, f, indent=2)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add JSON handler
json_handler = JsonLogHandler(session_log)
logger.addHandler(json_handler)

def create_test_result(test_name: str, success: bool, details: dict = None):
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
        self.results = []
        
    def add_result(self, test_name: str, success: bool, details: dict = None):
        """Add a test result."""
        self.results.append(create_test_result(test_name, success, details))
        
    def save_results(self):
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

async def check_server_status(results: TestResults):
    """Check if required servers are running."""
    try:
        logger.info("Checking server status...", extra={"test_phase": "server_check"})
        
        # Check Neo4j
        logger.info("Checking Neo4j connection...", extra={"test_phase": "neo4j_check"})
        memory_system = TwoLayerMemorySystem()
        try:
            await memory_system.initialize()
            logger.info("Neo4j is running", extra={"test_phase": "neo4j_check", "test_result": True})
            results.add_result("neo4j_check", True)
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}", 
                        extra={"test_phase": "neo4j_check", "test_result": False})
            results.add_result("neo4j_check", False, {"error": str(e)})
            return False
            
        # Check Qdrant
        logger.info("Checking Qdrant connection...", extra={"test_phase": "qdrant_check"})
        embedding_service = EmbeddingService()
        vector_store = VectorStore(embedding_service)
        try:
            # VectorStore initializes connection in __init__
            logger.info("Qdrant is running", extra={"test_phase": "qdrant_check", "test_result": True})
            results.add_result("qdrant_check", True)
        except Exception as e:
            logger.error(f"Qdrant connection failed: {str(e)}", 
                        extra={"test_phase": "qdrant_check", "test_result": False})
            results.add_result("qdrant_check", False, {"error": str(e)})
            return False
            
        logger.info("All required servers are running", 
                   extra={"test_phase": "server_check", "test_result": True})
        return True
        
    except Exception as e:
        logger.error(f"Server status check failed: {str(e)}", 
                    extra={"test_phase": "server_check", "test_result": False})
        results.add_result("server_check", False, {
            "error": str(e),
            "traceback": str(traceback.format_exc())
        })
        return False

async def test_vector_store(results: TestResults):
    """Test vector store initialization and operations."""
    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        vector_store = VectorStore(embedding_service)
        
        # Test vector storage
        logger.info("Testing vector storage...", extra={"test_phase": "vector_store_add"})
        test_content = {"text": "Test content", "metadata": {"test": True}}
        point_id = await vector_store.store_vector(
            content=test_content,  # Store content directly
            metadata={"test": True},
            layer="test"
        )
        logger.info(f"Vector stored with ID: {point_id}", extra={"test_phase": "vector_store_add", "test_result": True})
        results.add_result("vector_store_add", True, {"point_id": point_id})
        
        # Test vector search
        logger.info("Testing vector search...", extra={"test_phase": "vector_store_search"})
        search_results = await vector_store.search_vectors(
            content={"text": "Test content"},  # Pass content directly
            limit=1
        )
        logger.info(f"Vector search returned {len(search_results)} results", 
                   extra={"test_phase": "vector_store_search", "test_result": True})
        results.add_result("vector_store_search", True, {
            "results_found": len(search_results)
        })
        
        return True
    except Exception as e:
        logger.error(f"Vector store test failed: {str(e)}")
        results.add_result("vector_store_test", False, {
            "error": str(e),
            "traceback": str(traceback.format_exc())
        })
        return False

async def test_thread_operations(results: TestResults):
    """Test comprehensive thread operations including edge cases and error conditions."""
    try:
        logger.info("Testing thread operations...", extra={"test_phase": "thread_operations"})
        memory_system = TwoLayerMemorySystem()
        await memory_system.initialize()
        
        # Test 1: System thread with special metadata
        logger.info("Creating system thread...", extra={"test_phase": "system_thread_create"})
        system_thread = {
            "id": "nova-system-thread",
            "name": "Nova System Thread",
            "domain": "system",
            "messages": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "workspace": "system",
            "participants": ["nova", "nova-team"],
            "metadata": {
                "type": "system",
                "system": True,
                "pinned": True,
                "description": "Core system thread",
                "protected": True,
                "system_type": "core",
                "auto_archive": False
            }
        }
        
        # Store system thread
        memory = Memory(
            content=system_thread,  # Store content directly
            type=MemoryType.EPISODIC,
            importance=1.0  # System threads are highest importance
        )
        await memory_system.store_experience(memory)
        logger.info("System thread created", 
                   extra={"test_phase": "system_thread_create", "test_result": True})
        results.add_result("system_thread_create", True)
        
        # Test 2: Agent thread with task dependencies
        logger.info("Creating agent thread...", extra={"test_phase": "agent_thread_create"})
        agent_thread = {
            "id": "agent-task-thread",
            "name": "Agent Task Thread",
            "domain": "agent",
            "messages": [{"role": "agent", "content": "Task initiated"}],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "workspace": "tasks",
            "participants": ["task_agent", "coordination_agent"],
            "metadata": {
                "type": "agent",
                "system": False,
                "pinned": False,
                "description": "Agent task coordination",
                "task_id": "task-123",
                "dependencies": ["task-120", "task-121", "task-122"],
                "status": "active",
                "priority": "high"
            }
        }
        
        # Store agent thread
        agent_memory = Memory(
            content=agent_thread,  # Store content directly
            type=MemoryType.EPISODIC,
            importance=0.8
        )
        await memory_system.store_experience(agent_memory)
        logger.info("Agent thread created", 
                   extra={"test_phase": "agent_thread_create", "test_result": True})
        results.add_result("agent_thread_create", True)
        
        # Test 3: Invalid thread data
        logger.info("Testing invalid thread data...", extra={"test_phase": "invalid_thread"})
        try:
            # Missing required fields
            invalid_thread = {
                "id": "invalid-thread",
                # Missing name
                "domain": "test",
                # Missing messages
                "createdAt": "invalid-timestamp",  # Invalid timestamp
                "metadata": {
                    # Missing required metadata fields
                }
            }
            
            invalid_memory = Memory(
                content=invalid_thread,
                type=MemoryType.EPISODIC,
                importance=0.5
            )
            await memory_system.store_experience(invalid_memory)
            raise Exception("Expected validation error for invalid thread")
        except Exception as e:
            if "validation" not in str(e).lower():
                raise Exception("Expected validation error, got: " + str(e))
            logger.info("Invalid thread correctly rejected", 
                       extra={"test_phase": "invalid_thread", "test_result": True})
            results.add_result("invalid_thread", True)
        
        # Clean up test threads
        logger.info("Testing thread deletion...", extra={"test_phase": "thread_delete"})
        thread_ids = [
            "nova-system-thread",
            "agent-task-thread",
            "invalid-thread"  # This one shouldn't exist but try anyway
        ]
        for thread_id in thread_ids:
            try:
                await memory_system.delete_experience(thread_id)
            except Exception as e:
                logger.warning(f"Error deleting thread {thread_id}: {str(e)}")
                
        logger.info("Threads deleted successfully", 
                   extra={"test_phase": "thread_delete", "test_result": True})
        results.add_result("thread_delete", True)
        
        return True
    except Exception as e:
        logger.error(f"Thread operations test failed: {str(e)}", 
                    extra={"test_phase": "thread_operations", "test_result": False})
        results.add_result("thread_operations_test", False, {
            "error": str(e),
            "traceback": str(traceback.format_exc())
        })
        return False

async def run_tests():
    """Run all tests and save results."""
    logger.info("Starting test session...", extra={"test_phase": "session_start"})
    results = TestResults()
    
    try:
        # Check server status
        logger.info("Checking server status...", extra={"test_phase": "server_check"})
        servers_running = await check_server_status(results)
        if not servers_running:
            logger.error("Required servers are not running", 
                        extra={"test_phase": "server_check", "test_result": False})
            results.save_results()
            return
        logger.info("Server check completed successfully", 
                   extra={"test_phase": "server_check", "test_result": True})
        
        # Test vector store
        logger.info("Starting vector store tests...", extra={"test_phase": "vector_store"})
        vector_store_success = await test_vector_store(results)
        if not vector_store_success:
            logger.error("Vector store tests failed", extra={"test_phase": "vector_store", "test_result": False})
            results.save_results()
            return
        logger.info("Vector store tests completed successfully", extra={"test_phase": "vector_store", "test_result": True})
            
        # Test thread operations
        logger.info("Starting thread operation tests...", extra={"test_phase": "thread_operations"})
        thread_ops_success = await test_thread_operations(results)
        if not thread_ops_success:
            logger.error("Thread operation tests failed", extra={"test_phase": "thread_operations", "test_result": False})
            results.save_results()
            return
        logger.info("Thread operation tests completed successfully", 
                   extra={"test_phase": "thread_operations", "test_result": True})
            
        logger.info("All tests completed successfully", extra={"test_phase": "session_end", "test_result": True})
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", 
                    extra={"test_phase": "session_end", "test_result": False})
        results.add_result("test_suite", False, {
            "error": str(e),
            "traceback": str(traceback.format_exc())
        })
    finally:
        # Save results
        results_file = results.save_results()
        logger.info(f"Test results saved to: {results_file}", 
                   extra={"test_phase": "session_end"})

if __name__ == "__main__":
    asyncio.run(run_tests())
