"""Test script for agent storage functionality."""

import asyncio
import json
import logging
import traceback
import shutil
import os
import uuid
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from nia.core.neo4j.agent_store import AgentStore
from nia.memory.two_layer import TwoLayerMemorySystem, Memory, MemoryType

# Configure JSON logging
LOGS_DIR = Path("test_results/agent_storage_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure test-specific paths
TEST_DATA_DIR = Path("test_data/agent_storage")
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

NEO4J_DATA_DIR = Path("data/neo4j")
NEO4J_BACKUP_DIR = TEST_DATA_DIR / "neo4j_backup"
TEST_CONFIG_PATH = TEST_DATA_DIR / "test_config.ini"

# API configuration
API_BASE_URL = "http://localhost:8000/api"
API_KEY = "test-key"  # For testing

# Create session-specific log file
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

def create_test_config():
    """Create test-specific Neo4j configuration."""
    # Create test config in src directory
    src_config = Path(__file__).parent.parent / "src" / "config.ini"
    
    config_content = """[NEO4J]
uri = bolt://localhost:7687
user = neo4j
password = password
database = neo4j

[QDRANT]
host = localhost
port = 6333
collection = test_memories

[PATHS]
project_root = /Users/alee5331/Documents/Projects/NIA
"""
    # Create src config for imports
    src_config.parent.mkdir(parents=True, exist_ok=True)
    src_config.write_text(config_content)
    
    # Create test config
    TEST_CONFIG_PATH.write_text(config_content)
    
    # Set environment variable to use test config
    os.environ["CONFIG_PATH"] = str(TEST_CONFIG_PATH)
    
    return TEST_CONFIG_PATH

def backup_neo4j_data():
    """Backup existing Neo4j data."""
    if NEO4J_DATA_DIR.exists():
        if NEO4J_BACKUP_DIR.exists():
            shutil.rmtree(NEO4J_BACKUP_DIR)
        shutil.copytree(NEO4J_DATA_DIR, NEO4J_BACKUP_DIR)
        logger.info("Neo4j data backed up", extra={"test_phase": "setup"})

def restore_neo4j_data():
    """Restore Neo4j data from backup."""
    if NEO4J_BACKUP_DIR.exists():
        if NEO4J_DATA_DIR.exists():
            shutil.rmtree(NEO4J_DATA_DIR)
        shutil.copytree(NEO4J_BACKUP_DIR, NEO4J_DATA_DIR)
        logger.info("Neo4j data restored", extra={"test_phase": "cleanup"})

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
        
        # Create test config
        create_test_config()
        logger.info("Test configuration created", extra={"test_phase": "setup"})
        
        # Backup existing data
        backup_neo4j_data()
        
        # Check Neo4j
        logger.info("Checking Neo4j connection...", extra={"test_phase": "neo4j_check"})
        agent_store = AgentStore()
        try:
            await agent_store.initialize()
            logger.info("Neo4j is running", extra={"test_phase": "neo4j_check", "test_result": True})
            results.add_result("neo4j_check", True)
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}", 
                        extra={"test_phase": "neo4j_check", "test_result": False})
            results.add_result("neo4j_check", False, {"error": str(e)})
            return False
            
        # Check memory system
        logger.info("Checking memory system...", extra={"test_phase": "memory_check"})
        memory_system = TwoLayerMemorySystem()
        try:
            await memory_system.initialize()
            logger.info("Memory system is running", extra={"test_phase": "memory_check", "test_result": True})
            results.add_result("memory_check", True)
        except Exception as e:
            logger.error(f"Memory system connection failed: {str(e)}", 
                        extra={"test_phase": "memory_check", "test_result": False})
            results.add_result("memory_check", False, {"error": str(e)})
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

async def test_agent_storage(results: TestResults):
    """Test agent storage functionality."""
    try:
        logger.info("Starting agent storage test", extra={"test_phase": "agent_storage"})
        
        # Initialize stores
        logger.info("Initializing stores...", extra={"test_phase": "store_init"})
        agent_store = AgentStore()
        await agent_store.initialize()
        logger.info("Agent store initialized", extra={"test_phase": "store_init", "test_result": True})
        results.add_result("store_init", True)
        
        memory_system = TwoLayerMemorySystem()
        await memory_system.initialize()
        logger.info("Memory system initialized", extra={"test_phase": "store_init", "test_result": True})
        
        # Test 1: Create test thread
        logger.info("Creating test thread...", extra={"test_phase": "create_thread"})
        thread_id = str(uuid.uuid4())  # Use UUID for thread ID
        thread_data = {
            "id": thread_id,
            "name": "Test Thread",
            "type": "test",
            "domain": "test",
            "messages": [],
            "participants": [],
            "metadata": {
                "type": "test",
                "system": False,
                "pinned": False
            }
        }
        
        # Create Memory object with proper structure
        # First verify thread doesn't exist
        existing = await memory_system.get_memory(thread_id)
        if existing:
            logger.warning(f"Thread {thread_id} already exists")
            
        # Create test memory content
        memory_content = {
            "thread_id": thread_id,
            "name": "Test Thread",
            "type": "test",
            "domain": "test",
            "messages": [],
            "participants": []
        }
        
        # Create thread with complete metadata per 0113 requirements
        memory_id = str(uuid.uuid4())  # Generate unique memory ID
        thread_memory = Memory(
            id=memory_id,  # Use generated memory ID
            content=json.dumps(memory_content),  # Serialize content to string
            type=MemoryType.EPISODIC,
            importance=0.8,
            timestamp=datetime.now().isoformat(),
            context={
                "domain": "test",  # Required domain
                "source": "test",
                "type": "thread",
                "workspace": "test"  # Required workspace
            },
            metadata={
                "thread_id": thread_id,  # Store thread ID in metadata
                "type": "thread",  # Required type
                "system": False,    # Required system flag
                "pinned": False,    # Required pinned flag
                "description": "Test thread for agent storage",  # Required description
                "consolidated": False
            }
        )
        
        # Store memory
        logger.info(f"Storing thread memory with ID: {memory_id}", 
                   extra={"test_phase": "create_thread"})
        logger.info(f"Thread memory content: {thread_memory.content}", 
                   extra={"test_phase": "create_thread"})
        logger.info(f"Thread memory metadata: {json.dumps(thread_memory.metadata, indent=2)}", 
                   extra={"test_phase": "create_thread"})
        
        await memory_system.store_experience(thread_memory)
        
        # Verify storage by retrieving the memory
        logger.info(f"Verifying memory storage with ID: {memory_id}", 
                   extra={"test_phase": "create_thread"})
                   
        # Verify using get_experience
        retrieved_memory = await memory_system.get_experience(memory_id)
        if retrieved_memory is None:
            raise Exception(f"Failed to retrieve memory with ID: {memory_id}")
            
        # Log retrieved data for debugging
        logger.info(f"Retrieved memory content: {retrieved_memory.content}", 
                   extra={"test_phase": "create_thread"})
        logger.info(f"Retrieved memory metadata: {json.dumps(retrieved_memory.metadata, indent=2)}", 
                   extra={"test_phase": "create_thread"})
        
        # Parse content to compare
        try:
            original_content = json.loads(thread_memory.content)
            retrieved_content = json.loads(retrieved_memory.content)
            
            if original_content != retrieved_content:
                raise Exception(
                    f"Content mismatch - "
                    f"Original: {json.dumps(original_content)}, "
                    f"Retrieved: {json.dumps(retrieved_content)}"
                )
                
            # Verify metadata matches
            if retrieved_memory.metadata != thread_memory.metadata:
                raise Exception(
                    f"Metadata mismatch - "
                    f"Original: {json.dumps(thread_memory.metadata)}, "
                    f"Retrieved: {json.dumps(retrieved_memory.metadata)}"
                )
                
            logger.info("Memory verification successful", 
                       extra={"test_phase": "create_thread"})
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse memory content: {str(e)}")
        logger.info("Test thread created", extra={"test_phase": "create_thread", "test_result": True})
        results.add_result("create_thread", True)
        
        # Test 2: Create test agent
        logger.info("Creating test agent...", extra={"test_phase": "create_agent"})
        agent_id = str(uuid.uuid4())  # Use UUID for agent ID
        agent_data = {
            "id": agent_id,
            "name": "Test Agent",
            "type": "test",
            "workspace": "test",
            "domain": "test",
            "status": "active",
            "metadata_type": "agent",
            "metadata_capabilities": ["testing"],
            "metadata_created_at": datetime.now().isoformat()
        }
        
        await agent_store.store_agent(agent_data, thread_id)
        logger.info(f"Test agent created with ID: {agent_id}", 
                   extra={"test_phase": "create_agent", "test_result": True})
        results.add_result("create_agent", True, {"agent_id": agent_id})
        
        # Test 3: Verify agent in Neo4j
        logger.info("Verifying agent in Neo4j...", extra={"test_phase": "verify_neo4j"})
        stored_agent = await agent_store.get_agent(agent_id)
        assert stored_agent is not None, "Agent not found in Neo4j"
        assert stored_agent["id"] == agent_id, "Agent ID mismatch"
        assert stored_agent["name"] == agent_data["name"], "Agent name mismatch"
        logger.info("Agent verified in Neo4j", 
                   extra={"test_phase": "verify_neo4j", "test_result": True})
        results.add_result("verify_neo4j", True, {
            "agent_id": agent_id,
            "stored_data": stored_agent
        })
        
        # Test 4: Verify agent in thread
        logger.info("Verifying agent in thread...", extra={"test_phase": "verify_thread"})
        thread_agents = await agent_store.get_thread_agents(thread_id)
        assert len(thread_agents) == 1, "Wrong number of agents in thread"
        assert thread_agents[0]["id"] == agent_id, "Agent not found in thread"
        logger.info("Agent verified in thread", 
                   extra={"test_phase": "verify_thread", "test_result": True})
        results.add_result("verify_thread", True, {
            "agent_id": agent_id,
            "thread_id": thread_id,
            "thread_agents": thread_agents
        })
        
        # Test 5: Create agent relationship
        logger.info("Creating agent relationship...", extra={"test_phase": "create_relationship"})
        other_agent_id = str(uuid.uuid4())  # Use UUID for other agent ID
        other_agent_data = {
            "id": other_agent_id,
            "name": "Other Test Agent",
            "type": "test",
            "workspace": "test",
            "domain": "test",
            "status": "active",
            "metadata_type": "agent",
            "metadata_capabilities": ["testing"],
            "metadata_created_at": datetime.now().isoformat()
        }
        await agent_store.store_agent(other_agent_data)
        
        await agent_store.create_agent_relationship(
            agent_id,
            other_agent_id,
            "COLLABORATES_WITH",
            {"test_property": "test_value"}
        )
        logger.info("Agent relationship created", 
                   extra={"test_phase": "create_relationship", "test_result": True})
        results.add_result("create_relationship", True, {
            "source_id": agent_id,
            "target_id": other_agent_id,
            "type": "COLLABORATES_WITH"
        })
        
        # Test 6: Verify relationship
        logger.info("Verifying agent relationship...", extra={"test_phase": "verify_relationship"})
        updated_agent = await agent_store.get_agent(agent_id)
        assert len(updated_agent["relationships"]) == 1, "Wrong number of relationships"
        assert updated_agent["relationships"][0]["target_id"] == other_agent_id, "Wrong relationship target"
        logger.info("Agent relationship verified", 
                   extra={"test_phase": "verify_relationship", "test_result": True})
        results.add_result("verify_relationship", True, {
            "agent_id": agent_id,
            "relationships": updated_agent["relationships"]
        })
        
        # Test 7: Update agent status
        logger.info("Updating agent status...", extra={"test_phase": "update_status"})
        await agent_store.update_agent_status(agent_id, "inactive")
        updated_agent = await agent_store.get_agent(agent_id)
        assert updated_agent["status"] == "inactive", "Status not updated"
        logger.info("Agent status updated", 
                   extra={"test_phase": "update_status", "test_result": True})
        results.add_result("update_status", True, {
            "agent_id": agent_id,
            "new_status": "inactive"
        })
        
        # Test 8: Search agents
        logger.info("Searching agents...", extra={"test_phase": "search_agents"})
        search_results = await agent_store.search_agents(
            properties={"status": "inactive"},
            agent_type="test",
            workspace="test",
            domain="test"
        )
        assert len(search_results) == 1, "Wrong number of search results"
        assert search_results[0]["id"] == agent_id, "Wrong agent found"
        logger.info("Agent search successful", 
                   extra={"test_phase": "search_agents", "test_result": True})
        results.add_result("search_agents", True, {
            "search_criteria": {
                "status": "inactive",
                "type": "test",
                "workspace": "test",
                "domain": "test"
            },
            "results": search_results
        })
        
        # Test 9: Remove agent from thread
        logger.info("Removing agent from thread...", extra={"test_phase": "remove_from_thread"})
        await agent_store.remove_agent_from_thread(agent_id, thread_id)
        thread_agents = await agent_store.get_thread_agents(thread_id)
        assert len(thread_agents) == 0, "Agent not removed from thread"
        logger.info("Agent removed from thread", 
                   extra={"test_phase": "remove_from_thread", "test_result": True})
        results.add_result("remove_from_thread", True, {
            "agent_id": agent_id,
            "thread_id": thread_id
        })
        
        # Test 10: Delete agents
        logger.info("Deleting agents...", extra={"test_phase": "delete_agents"})
        await agent_store.delete_agent(agent_id)
        await agent_store.delete_agent(other_agent_id)
        deleted_agent = await agent_store.get_agent(agent_id)
        assert deleted_agent is None, "Agent not deleted"
        logger.info("Agents deleted", 
                   extra={"test_phase": "delete_agents", "test_result": True})
        results.add_result("delete_agents", True, {
            "deleted_agents": [agent_id, other_agent_id]
        })
        
        logger.info("All tests passed successfully!", 
                   extra={"test_phase": "agent_storage", "test_result": True})
        return True
        
    except AssertionError as e:
        logger.error(f"Test failed: {str(e)}", 
                    extra={"test_phase": "agent_storage", "test_result": False})
        results.add_result("agent_storage", False, {
            "error": str(e),
            "type": "assertion_error"
        })
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", 
                    extra={"test_phase": "agent_storage", "test_result": False})
        results.add_result("agent_storage", False, {
            "error": str(e),
            "traceback": str(traceback.format_exc())
        })
        return False
    finally:
        # Cleanup
        try:
            await agent_store.cleanup()
            await memory_system.cleanup()
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

async def test_agent_api(results: TestResults):
    """Test agent-related API endpoints."""
    try:
        logger.info("Starting API tests...", extra={"test_phase": "api_tests"})
        
        async with aiohttp.ClientSession() as session:
            # Test 1: List available agents
            logger.info("Testing GET /api/agents...", extra={"test_phase": "api_list_agents"})
            async with session.get(f"{API_BASE_URL}/agents") as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                agents = await response.json()
                assert isinstance(agents, list), "Expected list of agents"
                logger.info("GET /api/agents successful", 
                          extra={"test_phase": "api_list_agents", "test_result": True})
                results.add_result("api_list_agents", True, {
                    "agents_count": len(agents)
                })
            
            # Test 2: Get agent graph
            logger.info("Testing GET /api/agents/graph...", extra={"test_phase": "api_agent_graph"})
            async with session.get(f"{API_BASE_URL}/agents/graph") as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                graph = await response.json()
                assert "nodes" in graph, "Expected nodes in graph"
                assert "edges" in graph, "Expected edges in graph"
                logger.info("GET /api/agents/graph successful", 
                          extra={"test_phase": "api_agent_graph", "test_result": True})
                results.add_result("api_agent_graph", True, {
                    "nodes_count": len(graph["nodes"]),
                    "edges_count": len(graph["edges"])
                })
            
            # Test 3: Create test thread
            logger.info("Testing POST /api/chat/threads/create...", 
                       extra={"test_phase": "api_create_thread"})
            thread_data = {
                "title": "Test Thread",
                "domain": "test",
                "metadata": {
                    "type": "test",
                    "system": False,
                    "pinned": False,
                    "description": "Test thread for agent API testing"
                }
            }
            async with session.post(
                f"{API_BASE_URL}/chat/threads/create",
                json=thread_data
            ) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                thread = await response.json()
                thread_id = thread["id"]
                logger.info("POST /api/chat/threads/create successful", 
                          extra={"test_phase": "api_create_thread", "test_result": True})
                results.add_result("api_create_thread", True, {
                    "thread_id": thread_id
                })
            
            # Test 4: Add agent to thread
            logger.info("Testing POST /api/chat/threads/{thread_id}/agents...", 
                       extra={"test_phase": "api_add_thread_agent"})
            agent_data = {
                "agentType": "test",
                "workspace": "test",
                "domain": "test"
            }
            async with session.post(
                f"{API_BASE_URL}/chat/threads/{thread_id}/agents",
                json=agent_data
            ) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                agent = await response.json()
                logger.info("POST /api/chat/threads/{thread_id}/agents successful", 
                          extra={"test_phase": "api_add_thread_agent", "test_result": True})
                results.add_result("api_add_thread_agent", True, {
                    "agent_id": agent["id"]
                })
            
            # Test 5: Get thread agents
            logger.info("Testing GET /api/chat/threads/{thread_id}/agents...", 
                       extra={"test_phase": "api_get_thread_agents"})
            async with session.get(
                f"{API_BASE_URL}/chat/threads/{thread_id}/agents"
            ) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                agents = await response.json()
                assert len(agents) > 0, "Expected at least one agent in thread"
                logger.info("GET /api/chat/threads/{thread_id}/agents successful", 
                          extra={"test_phase": "api_get_thread_agents", "test_result": True})
                results.add_result("api_get_thread_agents", True, {
                    "agents_count": len(agents)
                })
        
        logger.info("All API tests passed successfully!", 
                   extra={"test_phase": "api_tests", "test_result": True})
        return True
        
    except AssertionError as e:
        logger.error(f"API test failed: {str(e)}", 
                    extra={"test_phase": "api_tests", "test_result": False})
        results.add_result("api_tests", False, {
            "error": str(e),
            "type": "assertion_error"
        })
        return False
    except Exception as e:
        logger.error(f"Unexpected error in API tests: {str(e)}", 
                    extra={"test_phase": "api_tests", "test_result": False})
        results.add_result("api_tests", False, {
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
        
        # Test agent storage
        logger.info("Starting agent storage tests...", extra={"test_phase": "agent_storage"})
        agent_storage_success = await test_agent_storage(results)
        if not agent_storage_success:
            logger.error("Agent storage tests failed", 
                        extra={"test_phase": "agent_storage", "test_result": False})
            results.save_results()
            return
        logger.info("Agent storage tests completed successfully", 
                   extra={"test_phase": "agent_storage", "test_result": True})
        
        # Test agent APIs
        logger.info("Starting agent API tests...", extra={"test_phase": "api_tests"})
        api_success = await test_agent_api(results)
        if not api_success:
            logger.error("Agent API tests failed", 
                        extra={"test_phase": "api_tests", "test_result": False})
            results.save_results()
            return
        logger.info("Agent API tests completed successfully", 
                   extra={"test_phase": "api_tests", "test_result": True})
            
        logger.info("All tests completed successfully", 
                   extra={"test_phase": "session_end", "test_result": True})
        
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

async def cleanup():
    """Clean up test environment."""
    try:
        logger.info("Starting cleanup...", extra={"test_phase": "cleanup"})
        
        # Restore original Neo4j data
        restore_neo4j_data()
        
        # Remove test config
        if TEST_CONFIG_PATH.exists():
            TEST_CONFIG_PATH.unlink()
            logger.info("Test configuration removed", extra={"test_phase": "cleanup"})
        
        # Remove test data directory if empty
        if TEST_DATA_DIR.exists() and not any(TEST_DATA_DIR.iterdir()):
            TEST_DATA_DIR.rmdir()
            logger.info("Test data directory removed", extra={"test_phase": "cleanup"})
            
        logger.info("Cleanup completed", extra={"test_phase": "cleanup"})
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", 
                    extra={"test_phase": "cleanup", "test_result": False})

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    finally:
        # Always attempt cleanup
        asyncio.run(cleanup())
