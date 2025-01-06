"""Integration tests for demo functionality."""

import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_analytics_agent,
    get_llm_interface,
    get_tiny_factory
)
from nia.nova.core.test_data import VALID_TASK
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.agents.specialized.analytics_agent import AnalyticsAgent
from nia.memory.llm_interface import LLMInterface
from nia.agents.tinytroupe_agent import TinyFactory

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

@pytest.fixture
async def memory_system():
    """Create real memory system for testing."""
    memory = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store_host="localhost",
        vector_store_port=6333
    )
    try:
        await memory.semantic.connect()
        await memory.episodic.connect()
        await memory.vector_store.connect()
        await memory.episodic.ensure_collection()
        await memory.vector_store.ensure_collection()
        yield memory
    finally:
        await memory.semantic.close()
        await memory.episodic.close()
        await memory.vector_store.close()

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

@pytest.mark.integration
class TestDemoFunctionality:
    """Test demo script functionality."""
    
    @pytest.mark.asyncio
    async def test_memory_storage(self, memory_system, llm_interface):
        """Test storing initial knowledge in memory system."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        app.dependency_overrides[get_llm_interface] = lambda: llm_interface
        
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
    async def test_query_parsing(self, memory_system, analytics_agent, llm_interface):
        """Test parsing user queries."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface
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
    async def test_agent_coordination(self, memory_system, analytics_agent, llm_interface):
        """Test agent coordination through WebSocket."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface
        })
        
        try:
            client = TestClient(app)
            
            with client.websocket_connect(
                "/api/analytics/ws",
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
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
                
                assert updates_received > 0
                assert response_received
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_memory_analytics(self, memory_system, analytics_agent):
        """Test memory pattern analysis."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent
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
    async def test_swarm_coordination(self, memory_system, analytics_agent, llm_interface, tiny_factory):
        """Test swarm coordination capabilities."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory
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
            with client.websocket_connect(
                "/api/analytics/ws",
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                # Monitor swarm activity
                websocket.send_json({
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
                    data = websocket.receive_json()
                    if data["type"] == "swarm_update":
                        pattern = data.get("pattern")
                        if pattern in events_received:
                            events_received[pattern] = True
                
                assert all(events_received.values())
            
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
    async def test_error_handling(self, memory_system, analytics_agent, llm_interface, tiny_factory):
        """Test error handling in demo script."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory
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
            with client.websocket_connect(
                "/api/analytics/ws",
                headers={"X-API-Key": TEST_API_KEY}
            ) as websocket:
                # Send invalid message
                websocket.send_json({
                    "type": "invalid_type",
                    "content": "test"
                })
                
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "message" in response
            
            # Test cleanup with invalid swarm ID
            invalid_cleanup_response = client.delete(
                "/api/orchestration/swarms",
                headers={"X-API-Key": TEST_API_KEY},
                json={"swarm_ids": ["invalid_id"]}
            )
            assert invalid_cleanup_response.status_code == 404
        finally:
            app.dependency_overrides.clear()
