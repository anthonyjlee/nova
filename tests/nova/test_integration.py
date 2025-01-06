"""Integration tests for Nova's complete system."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_analytics_agent,
    get_memory_system,
    get_orchestration_agent,
    get_parsing_agent
)
from nia.nova.core.test_data import (
    VALID_ANALYTICS_REQUEST,
    VALID_TASK,
    VALID_COORDINATION_REQUEST
)
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.nova.core.analytics import AnalyticsAgent
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.world.environment import NIAWorld

# Test API key
TEST_API_KEY = "test-key"
assert TEST_API_KEY in API_KEYS, "Test API key not found in API_KEYS"

import docker
from docker import DockerClient
import neo4j
from neo4j import AsyncGraphDatabase
import time
import asyncio
import websockets
import os
import aiohttp

async def wait_for_neo4j(max_attempts=5, delay=5):
    """Wait for Neo4j to be ready with retries."""
    for attempt in range(max_attempts):
        try:
            driver = AsyncGraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "password")  # Default Neo4j credentials
            )
            await driver.verify_connectivity()
            await driver.close()
            return True
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(delay)
    return False

@pytest.fixture(autouse=True)
async def check_infrastructure():
    """Verify required infrastructure is running."""
    docker_client = None
    try:
        # Initialize Docker client
        docker_client = DockerClient(
            base_url='unix:///Users/alee5331/.docker/run/docker.sock',
            timeout=30
        )
        
        # Check and manage Neo4j container
        try:
            neo4j_container = docker_client.containers.get('nia-neo4j-1')
            if neo4j_container.status != 'running':
                neo4j_container.start()
                await asyncio.sleep(10)  # Wait for Neo4j to start
        except docker.errors.NotFound:
            pytest.skip("Neo4j container not found. Please run docker-compose up -d neo4j")
        
        # Check Neo4j connection
        await wait_for_neo4j()
        
        # Check and manage vector store container
        try:
            qdrant_container = docker_client.containers.get('nia-qdrant-1')
            if qdrant_container.status != 'running':
                qdrant_container.start()
                await asyncio.sleep(5)  # Wait for Qdrant to start
        except docker.errors.NotFound:
            pytest.skip("Qdrant container not found. Please run docker-compose up -d qdrant")
        
        # Check vector store connection
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:6333/collections") as response:
                if response.status != 200:
                    pytest.skip("Vector store not responding. Please check Qdrant container logs.")
            
    except docker.errors.DockerException as e:
        pytest.skip(f"Docker error: {str(e)}")
    except neo4j.exceptions.ServiceUnavailable:
        pytest.skip("Neo4j not responding. Please check container logs.")
    except aiohttp.ClientError:
        pytest.skip("Vector store not responding. Please check container logs.")
    except Exception as e:
        pytest.skip(f"Infrastructure check failed: {str(e)}")
    finally:
        if docker_client:
            docker_client.close()

@pytest.fixture
def docker_client():
    """Create Docker client for container management."""
    return DockerClient(
        base_url='unix:///Users/alee5331/.docker/run/docker.sock',
        timeout=30
    )

@pytest.mark.integration
class TestDockerServices:
    """Test Docker service management."""
    
    @pytest.mark.asyncio
    async def test_container_health(self, docker_client):
        """Test container health checks."""
        try:
            # Check Neo4j container
            neo4j_container = docker_client.containers.get('nia-neo4j-1')
            assert neo4j_container.status == 'running'
            
            # Check container logs for errors
            neo4j_logs = neo4j_container.logs(tail=100).decode('utf-8')
            assert "ERROR" not in neo4j_logs
            
            # Check Qdrant container
            qdrant_container = docker_client.containers.get('nia-qdrant-1')
            assert qdrant_container.status == 'running'
            
            # Check container logs for errors
            qdrant_logs = qdrant_container.logs(tail=100).decode('utf-8')
            assert "ERROR" not in qdrant_logs
            
            # Verify Neo4j connection
            await wait_for_neo4j()
            
            # Verify Qdrant connection
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:6333/collections") as response:
                    assert response.status == 200
        finally:
            docker_client.close()
    
    @pytest.mark.asyncio
    async def test_container_restart(self, docker_client):
        """Test container restart capabilities."""
        try:
            # Test Neo4j restart
            neo4j_container = docker_client.containers.get('nia-neo4j-1')
            neo4j_container.restart()
            await asyncio.sleep(20)  # Wait longer for restart
            assert neo4j_container.status == 'running'
            
            # Verify Neo4j connection after restart with retries
            await wait_for_neo4j(max_attempts=10, delay=5)  # More retries and longer delay
            
            # Test Qdrant restart
            qdrant_container = docker_client.containers.get('nia-qdrant-1')
            qdrant_container.restart()
            await asyncio.sleep(5)  # Wait for restart
            assert qdrant_container.status == 'running'
            
            # Verify Qdrant connection after restart
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:6333/collections") as response:
                    assert response.status == 200
        finally:
            docker_client.close()
    
    @pytest.mark.asyncio
    async def test_container_resource_usage(self, docker_client):
        """Test container resource monitoring."""
        try:
            # Check Neo4j resource usage
            neo4j_container = docker_client.containers.get('nia-neo4j-1')
            neo4j_stats = next(neo4j_container.stats(decode=True))
            
            # Verify CPU usage is reasonable (if stats are available)
            if 'cpu_stats' in neo4j_stats and 'precpu_stats' in neo4j_stats:
                cpu_stats = neo4j_stats['cpu_stats']
                precpu_stats = neo4j_stats['precpu_stats']
                
                if ('cpu_usage' in cpu_stats and 'cpu_usage' in precpu_stats and
                    'total_usage' in cpu_stats['cpu_usage'] and 'total_usage' in precpu_stats['cpu_usage'] and
                    'system_cpu_usage' in cpu_stats and 'system_cpu_usage' in precpu_stats):
                    
                    cpu_delta = float(cpu_stats['cpu_usage']['total_usage']) - \
                               float(precpu_stats['cpu_usage']['total_usage'])
                    system_delta = float(cpu_stats['system_cpu_usage']) - \
                                 float(precpu_stats['system_cpu_usage'])
                    if system_delta > 0:  # Avoid division by zero
                        cpu_percent = (cpu_delta / system_delta) * 100.0
                        assert cpu_percent < 90  # CPU usage should be under 90%
            
            # Verify memory usage is reasonable
            memory_usage = float(neo4j_stats['memory_stats']['usage'])
            memory_limit = float(neo4j_stats['memory_stats']['limit'])
            memory_percent = (memory_usage / memory_limit) * 100.0
            assert memory_percent < 90  # Memory usage should be under 90%
            
            # Check Qdrant resource usage
            qdrant_container = docker_client.containers.get('nia-qdrant-1')
            qdrant_stats = next(qdrant_container.stats(decode=True))
            
            # Verify CPU usage is reasonable (if stats are available)
            if 'cpu_stats' in qdrant_stats and 'precpu_stats' in qdrant_stats:
                cpu_stats = qdrant_stats['cpu_stats']
                precpu_stats = qdrant_stats['precpu_stats']
                
                if ('cpu_usage' in cpu_stats and 'cpu_usage' in precpu_stats and
                    'total_usage' in cpu_stats['cpu_usage'] and 'total_usage' in precpu_stats['cpu_usage'] and
                    'system_cpu_usage' in cpu_stats and 'system_cpu_usage' in precpu_stats):
                    
                    cpu_delta = float(cpu_stats['cpu_usage']['total_usage']) - \
                               float(precpu_stats['cpu_usage']['total_usage'])
                    system_delta = float(cpu_stats['system_cpu_usage']) - \
                                 float(precpu_stats['system_cpu_usage'])
                    if system_delta > 0:  # Avoid division by zero
                        cpu_percent = (cpu_delta / system_delta) * 100.0
                        assert cpu_percent < 90  # CPU usage should be under 90%
            
            # Verify memory usage is reasonable
            memory_usage = float(qdrant_stats['memory_stats']['usage'])
            memory_limit = float(qdrant_stats['memory_stats']['limit'])
            memory_percent = (memory_usage / memory_limit) * 100.0
            assert memory_percent < 90  # Memory usage should be under 90%
            
            # Verify connections are still healthy
            await wait_for_neo4j()
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:6333/collections") as response:
                    assert response.status == 200
        finally:
            docker_client.close()

@pytest.fixture
async def memory_system(request):
    """Create real memory system for testing."""
    memory = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        neo4j_auth=("neo4j", "password"),  # Default Neo4j credentials
        vector_store_host="localhost",
        vector_store_port=6333
    )
    
    async def cleanup():
        """Clean up test data."""
        try:
            # Clean up Neo4j test data
            await memory.semantic.store.run_query(
                "MATCH (n) WHERE n.domain = 'test' DETACH DELETE n"
            )
            
            # Clean up vector store test data
            await memory.vector_store.delete_collection()
            
            # Close connections
            await memory.semantic.close()
            await memory.episodic.close()
            await memory.vector_store.close()
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
    
    try:
        # Initialize connections
        await memory.semantic.connect()
        await memory.episodic.connect()
        await memory.vector_store.connect()
        
        # Create test collections
        await memory.episodic.ensure_collection()
        await memory.vector_store.ensure_collection()
        
        yield memory
    finally:
        # Register cleanup
        request.addfinalizer(cleanup)

@pytest.fixture
async def world():
    """Create world instance for testing."""
    return NIAWorld()

@pytest.fixture
async def analytics_agent(memory_system):
    """Create real analytics agent for testing."""
    agent = AnalyticsAgent(
        domain="test",
        store=memory_system.semantic.store,
        vector_store=memory_system.vector_store
    )
    return agent

@pytest.fixture
async def orchestration_agent(memory_system, world):
    """Create real orchestration agent for testing."""
    agent = OrchestrationAgent(
        name="test_orchestrator",
        memory_system=memory_system,
        domain="test"
    )
    return agent

@pytest.fixture
async def parsing_agent(memory_system, world):
    """Create real parsing agent for testing."""
    agent = ParsingAgent(
        name="test_parser",
        memory_system=memory_system,
        world=world,
        domain="test"
    )
    return agent

@pytest.fixture
async def tiny_factory(memory_system):
    """Create TinyFactory instance for testing."""
    from nia.agents.tinytroupe_agent import TinyFactory
    factory = TinyFactory(memory_system=memory_system)
    return factory

@pytest.mark.integration
class TestFullSystemIntegration:
    """Test complete system flow with real components."""
    
    @pytest.mark.asyncio
    async def test_websocket_memory_flow(self, memory_system, analytics_agent, world):
        """Test WebSocket with real memory operations."""
        # Override dependencies with real components
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        app.dependency_overrides[get_analytics_agent] = lambda: analytics_agent
        app.dependency_overrides[get_world] = lambda: world
        
        try:
            client = TestClient(app)
            async with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                try:
                    # Store test data in memory
                    test_data = {
                        "type": "test_content",
                        "content": "Test analytics data",
                        "timestamp": datetime.now().isoformat()
                    }
                    await memory_system.episodic.store(test_data)
                    
                    # Send analytics request
                    await websocket.send_json({
                        **VALID_ANALYTICS_REQUEST,
                        "content": test_data
                    })
                    
                    # Verify response includes memory context
                    data = await websocket.receive_json()
                    assert data["type"] == "analytics_update"
                    assert data["analytics"]["memory_context"] is not None
                    assert len(data["insights"]) > 0
                    
                    # Verify data was stored
                    stored_data = await memory_system.episodic.search(
                        query=test_data["content"]
                    )
                    assert len(stored_data) > 0
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, memory_system, analytics_agent, world):
        """Test concurrent memory operations through WebSocket."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        app.dependency_overrides[get_analytics_agent] = lambda: analytics_agent
        app.dependency_overrides[get_world] = lambda: world
        
        try:
            client = TestClient(app)
            # Create multiple connections
            async with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as ws1, \
                      client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as ws2:
                try:
                    # Store different test data through each connection
                    test_data_1 = {
                        "type": "test_content",
                        "content": "Test analytics data 1",
                        "timestamp": datetime.now().isoformat()
                    }
                    test_data_2 = {
                        "type": "test_content",
                        "content": "Test analytics data 2",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send concurrent requests
                    await asyncio.gather(
                        ws1.send_json({**VALID_ANALYTICS_REQUEST, "content": test_data_1}),
                        ws2.send_json({**VALID_ANALYTICS_REQUEST, "content": test_data_2})
                    )
                    
                    # Verify both responses
                    data1, data2 = await asyncio.gather(
                        ws1.receive_json(),
                        ws2.receive_json()
                    )
                    
                    assert data1["type"] == "analytics_update"
                    assert data2["type"] == "analytics_update"
                    
                    # Verify both sets of data were stored
                    stored_data = await memory_system.episodic.search(
                        query="Test analytics data"
                    )
                    assert len(stored_data) >= 2
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_memory_consolidation(self, memory_system, analytics_agent, world):
        """Test memory consolidation through WebSocket operations."""
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        app.dependency_overrides[get_analytics_agent] = lambda: analytics_agent
        app.dependency_overrides[get_world] = lambda: world
        
        try:
            client = TestClient(app)
            async with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                try:
                    # Store multiple related pieces of data
                    test_data_sequence = [
                        {
                            "type": "test_content",
                            "content": f"Test analytics data sequence {i}",
                            "timestamp": datetime.now().isoformat()
                        }
                        for i in range(5)
                    ]
                    
                    # Send sequence of requests
                    for data in test_data_sequence:
                        await websocket.send_json({
                            **VALID_ANALYTICS_REQUEST,
                            "content": data
                        })
                        response = await websocket.receive_json()
                        assert response["type"] == "analytics_update"
                    
                    # Verify data was consolidated
                    semantic_data = await memory_system.semantic.search(
                        query="Test analytics data sequence"
                    )
                    assert len(semantic_data) > 0
                    
                    # Verify relationships were created
                    relationships = await memory_system.semantic.get_relationships(
                        semantic_data[0]["id"]
                    )
                    assert len(relationships) > 0
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_full_task_flow(self, memory_system, orchestration_agent, parsing_agent, world):
        """Test complete task flow with real components."""
        # Override dependencies
        app.dependency_overrides[get_memory_system] = lambda: memory_system
        app.dependency_overrides[get_orchestration_agent] = lambda: orchestration_agent
        app.dependency_overrides[get_parsing_agent] = lambda: parsing_agent
        app.dependency_overrides[get_world] = lambda: world
        
        try:
            client = TestClient(app)
            
            # Create a task
            task_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json=VALID_TASK
            )
            assert task_response.status_code == 200
            task_data = task_response.json()
            task_id = task_data["task_id"]
            
            # Verify task was stored in memory
            stored_task = await memory_system.semantic.get_node(task_id)
            assert stored_task is not None
            
            # Coordinate agents for task
            coord_response = client.post(
                "/api/orchestration/agents/coordinate",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_COORDINATION_REQUEST,
                    "task_id": task_id
                }
            )
            assert coord_response.status_code == 200
            coord_data = coord_response.json()
            
            # Verify agent assignments were stored
            agent_assignments = await memory_system.semantic.get_relationships(
                task_id,
                relationship_type="ASSIGNED_TO"
            )
            assert len(agent_assignments) > 0
            
            # Monitor task progress through WebSocket
            async with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                try:
                    await websocket.send_json({
                        "type": "task_monitor",
                        "task_id": task_id
                    })
                    
                    # Should receive initial status
                    status = await websocket.receive_json()
                    assert status["type"] == "task_update"
                    assert status["task_id"] == task_id
                    
                    # Update task status
                    update_response = client.put(
                        f"/api/orchestration/tasks/{task_id}",
                        headers={"X-API-Key": TEST_API_KEY},
                        json={
                            **VALID_TASK,
                            "status": "in_progress"
                        }
                    )
                    assert update_response.status_code == 200
                    
                    # Should receive status update
                    status = await websocket.receive_json()
                    assert status["type"] == "task_update"
                    assert status["task_id"] == task_id
                    assert status["status"] == "in_progress"
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_swarm_task_creation(self, memory_system, orchestration_agent, world):
        """Test creating tasks with different swarm patterns."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_orchestration_agent: lambda: orchestration_agent,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Test hierarchical swarm
            hierarchical_task = {
                **VALID_TASK,
                "swarm_pattern": "hierarchical",
                "swarm_config": {
                    "name": "test_hierarchical",
                    "description": "Test hierarchical swarm",
                    "agents": ["agent1", "agent2", "agent3"],
                    "supervisor_id": "agent1",
                    "worker_ids": ["agent2", "agent3"]
                }
            }
            
            response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json=hierarchical_task
            )
            assert response.status_code == 200
            task_data = response.json()
            assert task_data["orchestration"]["swarm_pattern"] == "hierarchical"
            
            # Test parallel swarm
            parallel_task = {
                **VALID_TASK,
                "swarm_pattern": "parallel",
                "swarm_config": {
                    "name": "test_parallel",
                    "description": "Test parallel swarm",
                    "agents": ["agent1", "agent2", "agent3"],
                    "batch_size": 2,
                    "load_balancing": True
                }
            }
            
            response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json=parallel_task
            )
            assert response.status_code == 200
            task_data = response.json()
            assert task_data["orchestration"]["swarm_pattern"] == "parallel"
            
            # Test invalid swarm config
            invalid_task = {
                **VALID_TASK,
                "swarm_pattern": "hierarchical",
                "swarm_config": {
                    "name": "test_invalid",
                    "description": "Test invalid config",
                    "agents": ["agent1"]
                    # Missing required supervisor_id and worker_ids
                }
            }
            
            response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json=invalid_task
            )
            assert response.status_code == 422  # Validation error
            
        finally:
            app.dependency_overrides.clear()
            
    @pytest.mark.asyncio
    async def test_swarm_pattern_execution(self, memory_system, orchestration_agent, world):
        """Test execution of different swarm patterns."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_orchestration_agent: lambda: orchestration_agent,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Create a sequential swarm task
            sequential_task = {
                **VALID_TASK,
                "swarm_pattern": "sequential",
                "swarm_config": {
                    "name": "test_sequential",
                    "description": "Test sequential swarm",
                    "agents": ["agent1", "agent2", "agent3"],
                    "stages": [
                        {"stage": "parse", "agent": "agent1"},
                        {"stage": "analyze", "agent": "agent2"},
                        {"stage": "validate", "agent": "agent3"}
                    ],
                    "progress_tracking": True
                }
            }
            
            response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json=sequential_task
            )
            assert response.status_code == 200
            task_id = response.json()["task_id"]
            
            # Monitor task execution through WebSocket
            async with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                try:
                    await websocket.send_json({
                        "type": "task_monitor",
                        "task_id": task_id
                    })
                    
                    # Should receive stage updates
                    for _ in range(3):  # 3 stages
                        status = await websocket.receive_json()
                        assert status["type"] == "task_update"
                        assert "current_stage" in status
                    
                    # Verify execution order in memory
                    execution_sequence = await memory_system.semantic.get_relationships(
                        task_id,
                        relationship_type="EXECUTED_IN_SEQUENCE"
                    )
                    assert len(execution_sequence) == 3
                    stages = [record["stage_type"] for record in execution_sequence]
                    assert stages == ["parse", "analyze", "validate"]
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
                
        finally:
            app.dependency_overrides.clear()
            
    @pytest.mark.asyncio
    async def test_agent_interaction_flow(self, memory_system, orchestration_agent, parsing_agent, analytics_agent, world):
        """Test interactions between multiple agents."""
        # Override all dependencies
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_orchestration_agent: lambda: orchestration_agent,
            get_parsing_agent: lambda: parsing_agent,
            get_analytics_agent: lambda: analytics_agent,
            get_world: lambda: world
        })
        
        try:
            client = TestClient(app)
            
            # Start monitoring agent interactions
            async with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                try:
                    # Create a task that requires multiple agents
                    task_response = client.post(
                        "/api/orchestration/tasks",
                        headers={"X-API-Key": TEST_API_KEY},
                        json={
                            **VALID_TASK,
                            "requires_parsing": True,
                            "requires_analytics": True
                        }
                    )
                    task_id = task_response.json()["task_id"]
                    
                    # Monitor agent interactions
                    await websocket.send_json({
                        "type": "agent_monitor",
                        "task_id": task_id
                    })
                    
                    # Should see parsing agent activity
                    parsing_update = await websocket.receive_json()
                    assert parsing_update["type"] == "agent_update"
                    assert parsing_update["agent_type"] == "parsing"
                    
                    # Should see analytics agent activity
                    analytics_update = await websocket.receive_json()
                    assert analytics_update["type"] == "agent_update"
                    assert analytics_update["agent_type"] == "analytics"
                    
                    # Verify agent interactions were recorded
                    interactions = await memory_system.semantic.get_relationships(
                        task_id,
                        relationship_type="AGENT_INTERACTION"
                    )
                    assert len(interactions) > 0
                    
                    # Verify memory was shared between agents
                    shared_memory = await memory_system.semantic.get_relationships(
                        task_id,
                        relationship_type="SHARED_MEMORY"
                    )
                    assert len(shared_memory) > 0
                except websockets.exceptions.ConnectionClosed:
                    pytest.fail("WebSocket connection closed unexpectedly")
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    raise
        finally:
            app.dependency_overrides.clear()
