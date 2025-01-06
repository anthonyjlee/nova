"""Integration tests for demo functionality."""

import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime
import websockets
from contextlib import asynccontextmanager

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_tiny_factory,
    get_world
)
from nia.nova.core.test_data import VALID_TASK
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.agents.specialized.analytics_agent import AnalyticsAgent
from nia.memory.llm_interface import LLMInterface
from nia.agents.tinytroupe_agent import TinyFactory

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.fixture(autouse=True)
async def check_infrastructure():
    """Verify required infrastructure is running."""
    import neo4j
    from neo4j import AsyncGraphDatabase
    import aiohttp
    
    # Initialize resources outside try block
    driver = None
    session = aiohttp.ClientSession()
    
    try:
        # Check Neo4j
        driver = AsyncGraphDatabase.driver("bolt://localhost:7687")
        await driver.verify_connectivity()
        
        # Check vector store
        async with session.get("http://localhost:6333/collections") as response:
            if response.status != 200:
                pytest.skip("Vector store not available. Please ensure Qdrant is running on port 6333.")
            
    except neo4j.exceptions.ServiceUnavailable:
        pytest.skip("Neo4j not available. Please ensure Neo4j is running on port 7687.")
    except aiohttp.ClientError:
        pytest.skip("Vector store not available. Please ensure Qdrant is running on port 6333.")
    except Exception as e:
        pytest.skip(f"Infrastructure check failed: {str(e)}")
    finally:
        # Clean up resources
        if driver:
            await driver.close()
        if session:
            await session.close()

@pytest.fixture
async def memory_system(request):
    """Create real memory system for testing."""
    from nia.memory.vector.vector_store import VectorStore
    from nia.memory.vector.embeddings import EmbeddingService
    
    # Create vector store with connection details
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        embedding_service=embedding_service,
        host="localhost",
        port=6333
    )
    
    memory = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store=vector_store
    )
    
    async def cleanup():
        """Clean up test data."""
        try:
            # Clean up Neo4j test data
            await memory.semantic.store.run_query(
                "MATCH (n) WHERE n.domain = 'test' DETACH DELETE n"
            )
            
            # Clean up vector store test data
            if hasattr(memory.episodic.store, 'delete_collection'):
                await memory.episodic.store.delete_collection()
            
            # Close connections
            await memory.cleanup()
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
    
    try:
        # Initialize connections
        await memory.initialize()
        
        # Create test collections with unique names for isolation
        if hasattr(memory.episodic.store, 'ensure_collection'):
            await memory.episodic.store.ensure_collection("test_demo_episodic")
        
        yield memory
    finally:
        # Register cleanup
        request.addfinalizer(cleanup)

@pytest.fixture
async def llm_interface():
    """Create mock LLM interface for testing."""
    return LLMInterface(
        chat_model="test-chat-model",
        embedding_model="test-embedding-model"
    )

@pytest.fixture
async def analytics_agent(memory_system, llm_interface):
    """Create analytics agent for testing."""
    agent = AnalyticsAgent(
        domain="test",
        store=memory_system.semantic.store,
        vector_store=memory_system.vector_store,
        llm_interface=llm_interface
    )
    return agent

@pytest.fixture
async def tiny_factory(memory_system):
    """Create TinyFactory instance for testing."""
    return TinyFactory(memory_system=memory_system)

@pytest.fixture
async def world():
    """Create world instance for testing."""
    from nia.world.environment import NIAWorld
    return NIAWorld()

@pytest.mark.integration
class TestDemoFunctionality:
    """Test demo script functionality."""
    
    @pytest.mark.asyncio
    async def test_memory_storage(self, memory_system, llm_interface, world):
        """Test storing initial knowledge in memory system."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        app.dependency_overrides[get_llm_interface] = lambda: llm_interface
        app.dependency_overrides[get_world] = lambda: world
        
        try:
            client = TestClient(app)
            
            # Store initial knowledge
            memory_request = {
                "content": "The sky is blue because of Rayleigh scattering of sunlight.",
                "type": "fact",
                "importance": 0.95,
                "context": {"domain": "science"},
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            
            response = client.post(
                "/api/orchestration/memory/store",
                headers={"X-API-Key": TEST_API_KEY},
                json=memory_request
            )
            assert response.status_code == 200
            data = response.json()
            assert "memory_id" in data
            
            # Verify storage in both layers
            stored_data = await memory_system.episodic.search(
                query="sky blue Rayleigh scattering"
            )
            assert len(stored_data) > 0
            
            semantic_data = await memory_system.semantic.search(
                query="domain:science"
            )
            assert len(semantic_data) > 0
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_query_parsing(self, memory_system, analytics_agent, llm_interface, world):
        """Test parsing user queries."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Parse test query
            parse_request = {
                "text": "Why is the sky blue?",
                "domain": "science",
                "llm_config": {
                    "chat_model": "test-chat-model",
                    "embedding_model": "test-embedding-model"
                }
            }
            
            response = client.post(
                "/api/analytics/parse",
                headers={"X-API-Key": TEST_API_KEY},
                json=parse_request
            )
            assert response.status_code == 200
            data = response.json()
            assert "parsed_content" in data
            assert "confidence" in data
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_agent_coordination(self, memory_system, analytics_agent, llm_interface, world):
        """Test agent coordination through WebSocket."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Create WebSocket URL
            ws_url = f"ws://testserver/api/analytics/ws"
            
            # Use TestClient's websocket_connect as context manager
            with client.websocket_connect(
                ws_url,
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                try:
                    # Send coordination request
                    await websocket.send_json({
                        "type": "agent_coordination",
                        "content": "Why is the sky blue?",
                        "domain": "science",
                        "llm_config": {
                            "chat_model": "test-chat-model",
                            "embedding_model": "test-embedding-model"
                        }
                    })
                    
                    # Track agent updates
                    updates_received = 0
                    response_received = False
                    
                    while True:
                        try:
                            data = await websocket.receive_json()
                            
                            if data["type"] == "analytics_update":
                                updates_received += 1
                                assert "analytics" in data
                                for agent, update in data["analytics"].items():
                                    assert "message" in update
                            
                            elif data["type"] == "response":
                                response_received = True
                                assert "content" in data
                                break
                        except websockets.exceptions.ConnectionClosed:
                            break
                    
                    assert updates_received > 0
                    assert response_received
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_memory_analytics(self, memory_system, analytics_agent, world):
        """Test memory pattern analysis."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            response = client.get(
                "/api/analytics/flows",
                headers={"X-API-Key": TEST_API_KEY},
                params={"domain": "science"}
            )
            assert response.status_code == 200
            data = response.json()
            
            assert "analytics" in data
            assert "insights" in data
            assert isinstance(data["insights"], list)
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_swarm_coordination(self, memory_system, analytics_agent, llm_interface, tiny_factory, world):
        """Test swarm coordination capabilities."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Request swarm creation through Nova's orchestration
            swarm_request = {
                "type": "swarm_creation",
                "domain": "test",
                "swarm_requirements": {
                    "patterns": [
                        "hierarchical",
                        "parallel",
                        "sequential",
                        "mesh",
                        "round_robin",
                        "majority_voting"
                    ],
                    "capabilities": [
                        "task_execution",
                        "communication",
                        "coordination"
                    ]
                }
            }
            
            # Create swarms through Nova's orchestration
            response = client.post(
                "/api/orchestration/swarms",
                headers={"X-API-Key": TEST_API_KEY},
                json=swarm_request
            )
            assert response.status_code == 200
            swarm_data = response.json()
            
            # Test swarm coordination through WebSocket
            # Create WebSocket URL
            ws_url = f"ws://testserver/api/analytics/ws"
            
            # Use TestClient's websocket_connect as context manager
            with client.websocket_connect(
                ws_url,
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                try:
                    # Monitor swarm activity
                    await websocket.send_json({
                        "type": "swarm_monitor",
                        "swarm_ids": [
                            swarm_data["swarms"]["hierarchical"]["swarm_id"],
                            swarm_data["swarms"]["parallel"]["swarm_id"],
                            swarm_data["swarms"]["sequential"]["swarm_id"],
                            swarm_data["swarms"]["mesh"]["swarm_id"],
                            swarm_data["swarms"]["round_robin"]["swarm_id"],
                            swarm_data["swarms"]["majority_voting"]["swarm_id"]
                        ]
                    })
                    
                    # Track swarm events
                    events_received = {pattern: False for pattern in swarm_data["swarms"]}
                    
                    while not all(events_received.values()):
                        try:
                            data = await websocket.receive_json()
                            if data["type"] == "swarm_update":
                                pattern = data.get("pattern")
                                if pattern in events_received:
                                    events_received[pattern] = True
                        except websockets.exceptions.ConnectionClosed:
                            break
                    
                    assert all(events_received.values())
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
            
            # Cleanup swarms through Nova's orchestration
            cleanup_response = client.delete(
                "/api/orchestration/swarms",
                headers={"X-API-Key": TEST_API_KEY},
                json={"swarm_ids": list(swarm_data["swarms"].values())}
            )
            assert cleanup_response.status_code == 200
            
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, memory_system, analytics_agent, llm_interface, tiny_factory, world):
        """Test error handling in demo script."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test invalid swarm creation
            invalid_swarm_response = client.post(
                "/api/orchestration/swarms",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "type": "swarm_creation",
                    "domain": "test",
                    "swarm_requirements": {
                        "patterns": ["invalid_pattern"],
                        "capabilities": []
                    }
                }
            )
            assert invalid_swarm_response.status_code == 400
            
            # Test WebSocket error handling
            # Create WebSocket URL
            ws_url = f"ws://testserver/api/analytics/ws"
            
            # Use TestClient's websocket_connect as context manager
            with client.websocket_connect(
                ws_url,
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                try:
                    # Send invalid message
                    await websocket.send_json({
                        "type": "invalid_type",
                        "content": "test"
                    })
                    
                    response = await websocket.receive_json()
                    assert response["type"] == "error"
                    assert "message" in response
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
            
            # Test cleanup with invalid swarm ID
            invalid_cleanup_response = client.delete(
                "/api/orchestration/swarms",
                headers={"X-API-Key": TEST_API_KEY},
                json={"swarm_ids": ["invalid_id"]}
            )
            assert invalid_cleanup_response.status_code == 404
        finally:
            app.dependency_overrides.clear()
