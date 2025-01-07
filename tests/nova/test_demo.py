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
from nia.core.interfaces.llm_interface import LLMInterface
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
    async def test_user_profile(self, memory_system, analytics_agent, llm_interface, world):
        """Test user profile endpoints."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test questionnaire submission
            questionnaire_data = {
                "personality": {
                    "openness": 0.8,
                    "conscientiousness": 0.7,
                    "extraversion": 0.6,
                    "agreeableness": 0.75,
                    "neuroticism": 0.4
                },
                "learning_style": {
                    "visual": 0.8,
                    "auditory": 0.6,
                    "kinesthetic": 0.7
                },
                "communication_preferences": {
                    "detail_level": "high",
                    "feedback_frequency": "frequent",
                    "interaction_style": "collaborative"
                }
            }
            
            response = client.post(
                "/api/users/profile/questionnaire",
                headers={"X-API-Key": TEST_API_KEY},
                json=questionnaire_data
            )
            assert response.status_code == 200
            profile_id = response.json()["profile_id"]
            
            # Test profile data retrieval
            profile_response = client.get(
                "/api/users/profile",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            assert profile_data["personality"]["openness"] == 0.8
            assert profile_data["learning_style"]["visual"] == 0.8
            
            # Test preference updates
            preference_updates = {
                "auto_approval": {
                    "task_creation": True,
                    "memory_operations": False
                },
                "ui_preferences": {
                    "theme": "dark",
                    "message_density": "compact"
                }
            }
            
            pref_response = client.put(
                "/api/users/profile/preferences",
                headers={"X-API-Key": TEST_API_KEY},
                json=preference_updates
            )
            assert pref_response.status_code == 200
            
            # Test learning style retrieval
            style_response = client.get(
                "/api/users/profile/learning-style",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert style_response.status_code == 200
            style_data = style_response.json()
            assert "visual" in style_data
            assert "auditory" in style_data
            assert "kinesthetic" in style_data
            
            # Test auto-approval settings update
            approval_settings = {
                "task_creation": True,
                "memory_operations": False,
                "swarm_creation": True
            }
            
            approval_response = client.put(
                "/api/users/profile/auto-approval",
                headers={"X-API-Key": TEST_API_KEY},
                json=approval_settings
            )
            assert approval_response.status_code == 200
            
            # Verify updated settings
            profile_response = client.get(
                "/api/users/profile",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert profile_response.status_code == 200
            updated_data = profile_response.json()
            assert updated_data["preferences"]["auto_approval"]["task_creation"] == True
            assert updated_data["preferences"]["auto_approval"]["memory_operations"] == False
            
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_agent_identity(self, memory_system, analytics_agent, llm_interface, tiny_factory, world):
        """Test agent identity endpoints."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test agent capabilities retrieval
            capabilities_response = client.get(
                "/api/agents/test-agent/capabilities",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert capabilities_response.status_code == 200
            capabilities_data = capabilities_response.json()
            assert "capabilities" in capabilities_data
            assert isinstance(capabilities_data["capabilities"], list)
            
            # Test agent type listing
            types_response = client.get(
                "/api/agents/types",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert types_response.status_code == 200
            types_data = types_response.json()
            assert "agent_types" in types_data
            assert isinstance(types_data["agent_types"], list)
            
            # Test agent search by capability
            search_response = client.get(
                "/api/agents/search",
                headers={"X-API-Key": TEST_API_KEY},
                params={"capability": "task_execution"}
            )
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert "agents" in search_data
            assert isinstance(search_data["agents"], list)
            
            # Test agent history retrieval
            history_response = client.get(
                "/api/agents/test-agent/history",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert history_response.status_code == 200
            history_data = history_response.json()
            assert "interactions" in history_data
            assert isinstance(history_data["interactions"], list)
            
            # Test agent metrics retrieval
            metrics_response = client.get(
                "/api/agents/test-agent/metrics",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            assert "performance_metrics" in metrics_data
            assert "task_completion_rate" in metrics_data["performance_metrics"]
            assert "average_response_time" in metrics_data["performance_metrics"]
            assert "memory_utilization" in metrics_data["performance_metrics"]
            
            # Test agent activation/deactivation
            activate_response = client.post(
                "/api/agents/test-agent/activate",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert activate_response.status_code == 200
            
            deactivate_response = client.post(
                "/api/agents/test-agent/deactivate",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert deactivate_response.status_code == 200
            
            # Test agent status retrieval
            status_response = client.get(
                "/api/agents/test-agent/status",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "status" in status_data
            assert status_data["status"] == "inactive"
            
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_knowledge_graph(self, memory_system, analytics_agent, llm_interface, world):
        """Test knowledge graph endpoints."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test graph pruning
            prune_response = client.post(
                "/api/graph/prune",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "min_relevance_score": 0.5,
                    "max_age_days": 30,
                    "exclude_domains": ["critical", "system"]
                }
            )
            assert prune_response.status_code == 200
            prune_data = prune_response.json()
            assert "nodes_removed" in prune_data
            assert "edges_removed" in prune_data
            
            # Test graph health check
            health_response = client.get(
                "/api/graph/health",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert health_response.status_code == 200
            health_data = health_response.json()
            assert "node_count" in health_data
            assert "edge_count" in health_data
            assert "orphaned_nodes" in health_data
            assert "invalid_edges" in health_data
            assert "consistency_score" in health_data
            
            # Test graph structure optimization
            optimize_response = client.post(
                "/api/graph/optimize",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "target_metrics": ["query_performance", "storage_efficiency"],
                    "optimization_level": "aggressive"
                }
            )
            assert optimize_response.status_code == 200
            optimize_data = optimize_response.json()
            assert "performance_improvement" in optimize_data
            assert "space_saved" in optimize_data
            
            # Test graph statistics
            stats_response = client.get(
                "/api/graph/statistics",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert stats_response.status_code == 200
            stats_data = stats_response.json()
            assert "node_distribution" in stats_data
            assert "edge_types" in stats_data
            assert "domain_stats" in stats_data
            assert "query_performance" in stats_data
            assert "memory_usage" in stats_data
            
            # Test graph backup creation
            backup_response = client.post(
                "/api/graph/backup",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "include_domains": ["all"],
                    "backup_format": "cypher",
                    "compression": True
                }
            )
            assert backup_response.status_code == 200
            backup_data = backup_response.json()
            assert "backup_id" in backup_data
            assert "timestamp" in backup_data
            assert "file_size" in backup_data
            assert "node_count" in backup_data
            assert "edge_count" in backup_data
            
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_advanced_swarms(self, memory_system, analytics_agent, llm_interface, tiny_factory, world):
        """Test advanced swarm operations."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test graph workflow
            workflow_response = client.post(
                "/api/swarms/graph-workflow",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "nodes": [
                        {"id": "task1", "type": "data_collection"},
                        {"id": "task2", "type": "analysis"},
                        {"id": "task3", "type": "validation"}
                    ],
                    "edges": [
                        {"from": "task1", "to": "task2"},
                        {"from": "task2", "to": "task3"}
                    ],
                    "execution_config": {
                        "parallel_tasks": True,
                        "error_handling": "retry"
                    }
                }
            )
            assert workflow_response.status_code == 200
            workflow_data = workflow_response.json()
            assert "workflow_id" in workflow_data
            assert "execution_status" in workflow_data
            
            # Test majority voting
            voting_response = client.post(
                "/api/swarms/majority-vote",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "question": "What is the optimal approach?",
                    "options": ["approach_a", "approach_b", "approach_c"],
                    "voting_config": {
                        "min_votes": 3,
                        "threshold": 0.6,
                        "timeout": 30
                    }
                }
            )
            assert voting_response.status_code == 200
            voting_data = voting_response.json()
            assert "selected_option" in voting_data
            assert "vote_distribution" in voting_data
            assert "confidence_score" in voting_data
            
            # Test round robin
            round_robin_response = client.post(
                "/api/swarms/round-robin",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "tasks": [
                        {"id": "task1", "type": "analysis"},
                        {"id": "task2", "type": "validation"},
                        {"id": "task3", "type": "synthesis"}
                    ],
                    "agent_pool": ["agent1", "agent2", "agent3"],
                    "scheduling_config": {
                        "time_slice": 5,
                        "fair_distribution": True
                    }
                }
            )
            assert round_robin_response.status_code == 200
            round_robin_data = round_robin_response.json()
            assert "schedule" in round_robin_data
            assert "agent_assignments" in round_robin_data
            
            # Test group chat
            group_chat_response = client.post(
                "/api/swarms/group-chat",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "participants": ["agent1", "agent2", "agent3"],
                    "topic": "Solution Design",
                    "chat_config": {
                        "max_rounds": 5,
                        "consensus_required": True
                    }
                }
            )
            assert group_chat_response.status_code == 200
            group_chat_data = group_chat_response.json()
            assert "chat_id" in group_chat_data
            assert "discussion_summary" in group_chat_data
            assert "consensus_reached" in group_chat_data
            
            # Test agent registry
            registry_response = client.post(
                "/api/swarms/registry",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "agent": {
                        "id": "new_agent",
                        "type": "specialized",
                        "capabilities": ["analysis", "validation"],
                        "resources": {
                            "memory_limit": "2GB",
                            "cpu_share": 0.5
                        }
                    }
                }
            )
            assert registry_response.status_code == 200
            registry_data = registry_response.json()
            assert "agent_id" in registry_data
            assert "registration_status" in registry_data
            
            # Verify agent registration
            verify_response = client.get(
                "/api/swarms/registry/new_agent",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert verify_response.status_code == 200
            verify_data = verify_response.json()
            assert verify_data["type"] == "specialized"
            assert "analysis" in verify_data["capabilities"]
            assert "validation" in verify_data["capabilities"]
            
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
            
    @pytest.mark.asyncio
    async def test_graph_visualization(self, memory_system, analytics_agent, llm_interface, tiny_factory, world):
        """Test graph visualization endpoints."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_analytics_agent: lambda: analytics_agent,
            get_llm_interface: lambda: llm_interface,
            get_tiny_factory: lambda: tiny_factory,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Create test pattern
            pattern_response = client.post(
                "/api/swarms/registry",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "pattern_type": "hierarchical",
                    "config": {
                        "tasks": [
                            {
                                "id": "supervisor",
                                "type": "supervisor",
                                "config": {}
                            },
                            {
                                "id": "worker1",
                                "type": "worker",
                                "config": {},
                                "dependencies": ["supervisor"]
                            },
                            {
                                "id": "worker2",
                                "type": "worker",
                                "config": {},
                                "dependencies": ["supervisor"]
                            }
                        ]
                    }
                }
            )
            assert pattern_response.status_code == 200
            pattern_data = pattern_response.json()
            pattern_id = pattern_data["pattern_id"]
            
            # Execute pattern
            execution_response = client.post(
                f"/api/swarms/execute/{pattern_id}",
                headers={"X-API-Key": TEST_API_KEY},
                json={}
            )
            assert execution_response.status_code == 200
            execution_data = execution_response.json()
            execution_id = execution_data["execution_id"]
            
            # Test DAG visualization
            dag_response = client.get(
                f"/api/visualization/dag/{execution_id}",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert dag_response.status_code == 200
            dag_data = dag_response.json()
            assert "visualization" in dag_data
            assert dag_data["visualization"]["type"] == "dag"
            
            # Test pattern visualization
            pattern_viz_response = client.get(
                f"/api/visualization/pattern/{pattern_id}",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert pattern_viz_response.status_code == 200
            pattern_viz_data = pattern_viz_response.json()
            assert "visualization" in pattern_viz_data
            assert pattern_viz_data["visualization"]["type"] == "pattern"
            
            # Test integrated visualization
            integrated_response = client.get(
                f"/api/visualization/integrated/{pattern_id}/{execution_id}",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert integrated_response.status_code == 200
            integrated_data = integrated_response.json()
            assert "visualization" in integrated_data
            assert integrated_data["visualization"]["type"] == "integrated"
            
            # Test pattern list visualization
            list_response = client.get(
                "/api/visualization/patterns",
                headers={"X-API-Key": TEST_API_KEY},
                params={"pattern_type": "hierarchical", "limit": 5}
            )
            assert list_response.status_code == 200
            list_data = list_response.json()
            assert "visualization" in list_data
            assert list_data["patterns"] > 0
            
            # Test execution history visualization
            history_response = client.get(
                f"/api/visualization/executions/{pattern_id}",
                headers={"X-API-Key": TEST_API_KEY},
                params={"limit": 5}
            )
            assert history_response.status_code == 200
            history_data = history_response.json()
            assert "visualization" in history_data
            assert history_data["executions"] > 0
            
            # Test error handling
            invalid_dag_response = client.get(
                "/api/visualization/dag/invalid_id",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert invalid_dag_response.status_code == 404
            
            invalid_pattern_response = client.get(
                "/api/visualization/pattern/invalid_id",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert invalid_pattern_response.status_code == 404
            
            invalid_integrated_response = client.get(
                "/api/visualization/integrated/invalid_pattern/invalid_execution",
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert invalid_integrated_response.status_code == 404
            
        finally:
            app.dependency_overrides.clear()
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
