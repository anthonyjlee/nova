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
from typing import Dict, Any, List, Optional

from nia.core.neo4j.agent_store import AgentStore
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.types.memory_types import Memory, MemoryType, ValidationSchema, CrossDomainSchema
from nia.core.types.domain_types import DomainContext, DomainTransfer

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
        """Emit a log record."""
        try:
            # Create log entry with safe attribute access
            log_entry = {
                "timestamp": datetime.fromtimestamp(getattr(record, 'created', datetime.now().timestamp())).isoformat(),
                "level": record.levelname if hasattr(record, 'levelname') else "NOTSET",
                "message": record.getMessage() if hasattr(record, 'getMessage') else str(record),
                "module": record.name if hasattr(record, 'name') else "test_agent_storage",
                "function": record.funcName if hasattr(record, 'funcName') else "",
                "line": record.lineno if hasattr(record, 'lineno') else 0,
                "thread_id": record.thread if hasattr(record, 'thread') else None,
                "process_id": record.process if hasattr(record, 'process') else None
            }

            # Add extra fields from record
            extra = getattr(record, 'extra', {})
            if extra:
                for key, value in extra.items():
                    log_entry[key] = value
            
            # Add exception info if present
            exc_info = getattr(record, 'exc_info', None)
            if exc_info and isinstance(exc_info, tuple) and len(exc_info) == 3:
                exc_type, exc_value, exc_tb = exc_info
                if exc_type and exc_value and exc_tb:
                    try:
                        log_entry["exception"] = {
                            "type": exc_type.__name__ if hasattr(exc_type, '__name__') else str(exc_type),
                            "message": str(exc_value),
                            "traceback": traceback.format_exception(exc_type, exc_value, exc_tb)
                        }
                    except Exception as e:
                        # Fallback for exception handling errors
                        log_entry["exception"] = {
                            "type": "Error",
                            "message": "Failed to format exception",
                            "error": str(e)
                        }
                
            self.logs.append(log_entry)
            self._save_logs()
        except Exception as e:
            # Fallback logging in case of errors
            print(f"Error in JsonLogHandler.emit: {str(e)}\n{traceback.format_exc()}")
        
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

# Configure root logger for all modules
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure test logger
logger = logging.getLogger("test_agent_storage")
logger.setLevel(logging.DEBUG)

# Enable debug logging for key modules
for module in [
    'nia.memory.types.memory_types',
    'nia.nova.core.base',
    'nia.memory.chunking',
    'nia.memory.vector_store',
    'nia.core.neo4j.agent_store'
]:
    logging.getLogger(module).setLevel(logging.DEBUG)

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

def create_test_result(test_name: str, success: bool, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a test result entry."""
    return {
        "test_name": test_name,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "details": details if details is not None else {}
    }

class TestResults:
    """Manage test results and output."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        
    def add_result(self, test_name: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
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
                "system": False,
                "pinned": False
            }
        }
        
        # Create Memory object with proper structure
        # First verify thread doesn't exist
        existing = await memory_system.get_experience(thread_id)
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
        memory_type = "thread"  # Use custom type for thread
        
        # Create validation schema
        validation = ValidationSchema(
            domain="test",
            confidence=0.9,
            source="test_agent_storage",
            timestamp=datetime.now().isoformat()
        )

        # Create domain context
        domain_context = DomainContext(
            domain="test",
            confidence=0.9,
            source="test_agent_storage",
            timestamp=datetime.now().isoformat(),
            metadata={
                "thread_id": thread_id,
                "operation": "create",
                "transfer": DomainTransfer(
                    from_domain="test",
                    to_domain="test",
                    operation="create",
                    data={"thread_id": thread_id},
                    approved=True,
                    requested=False
                ).dict()
            }
        )

        # Create thread memory with proper validation
        thread_memory = Memory(
            id=memory_id,
            content=memory_content,
            type=MemoryType.THREAD.value,
            importance=0.8,
            timestamp=datetime.now(),
            context={
                "domain": "test",
                "source": "test_agent_storage",
                "type": MemoryType.THREAD.value,
                "workspace": "test"
            },
            metadata={
                "thread_id": thread_id,
                "type": MemoryType.THREAD.value,
                "system": False,
                "pinned": False,
                "description": "Test thread for agent storage",
                "consolidated": False
            },
            domain_context=domain_context,
            validation=validation,
            source="test_agent_storage"
        )
        
        logger.debug(f"Created thread memory with type: {memory_type}")
        
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
        
        # Compare content directly since it's already a dict
        if retrieved_memory.content != thread_memory.content:
            raise Exception(
                f"Content mismatch - "
                f"Original: {json.dumps(thread_memory.content)}, "
                f"Retrieved: {json.dumps(retrieved_memory.content)}"
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
        if stored_agent is None:
            raise Exception("Agent not found in Neo4j")
        if stored_agent.get("id") != agent_id:
            raise Exception("Agent ID mismatch")
        if stored_agent.get("name") != agent_data["name"]:
            raise Exception("Agent name mismatch")
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
        if not updated_agent or not updated_agent.get("relationships"):
            raise Exception("No relationships found")
        relationships = updated_agent.get("relationships", [])
        if len(relationships) != 1:
            raise Exception("Wrong number of relationships")
        if relationships[0].get("target_id") != other_agent_id:
            raise Exception("Wrong relationship target")
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
        if not updated_agent or updated_agent.get("status") != "inactive":
            raise Exception("Status not updated")
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
        # Cleanup memory system only
        try:
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

if __name__ == "__main__":
    asyncio.run(run_tests())
