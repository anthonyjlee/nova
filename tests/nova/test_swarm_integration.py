"""Integration tests for Nova's swarm architecture and domain management."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from nia.nova.core.app import app
from nia.nova.core.auth import API_KEYS
from nia.nova.core.endpoints import (
    get_memory_system,
    get_coordination_agent,
    get_tiny_factory,
    get_orchestration_agent
)
from nia.nova.core.test_data import VALID_TASK
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.agents.specialized.coordination_agent import CoordinationAgent
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.tinytroupe_agent import TinyFactory
from nia.world.environment import NIAWorld

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
async def world():
    """Create world instance for testing."""
    return NIAWorld()

@pytest.fixture
async def coordination_agent(memory_system, world):
    """Create real coordination agent for testing."""
    agent = CoordinationAgent(
        name="test_coordinator",
        memory_system=memory_system,
        world=world,
        domain="test"
    )
    return agent

@pytest.fixture
async def tiny_factory(memory_system, world):
    """Create real TinyFactory for testing."""
    factory = TinyFactory(
        memory_system=memory_system,
        world=world
    )
    return factory

@pytest.mark.integration
class TestSwarmArchitecture:
    """Test swarm architecture patterns and domain management."""
    
    @pytest.mark.asyncio
    async def test_hierarchical_swarm(self, memory_system, coordination_agent, tiny_factory):
        """Test hierarchical swarm pattern with supervisor and worker agents."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create supervisor agent
            supervisor_response = client.post(
                "/api/orchestration/agents/create",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "agent_type": "supervisor",
                    "domain": "test",
                    "capabilities": ["task_delegation", "performance_monitoring"]
                }
            )
            assert supervisor_response.status_code == 200
            supervisor_id = supervisor_response.json()["agent_id"]
            
            # Create worker agents
            worker_ids = []
            for i in range(3):
                worker_response = client.post(
                    "/api/orchestration/agents/create",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "agent_type": "worker",
                        "domain": "test",
                        "capabilities": ["task_execution"],
                        "supervisor_id": supervisor_id
                    }
                )
                assert worker_response.status_code == 200
                worker_ids.append(worker_response.json()["agent_id"])
            
            # Monitor swarm through WebSocket
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                # Create task for swarm
                task_response = client.post(
                    "/api/orchestration/tasks",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        **VALID_TASK,
                        "swarm_pattern": "hierarchical",
                        "supervisor_id": supervisor_id,
                        "worker_ids": worker_ids
                    }
                )
                task_id = task_response.json()["task_id"]
                
                # Monitor swarm activity
                websocket.send_json({
                    "type": "swarm_monitor",
                    "task_id": task_id
                })
                
                # Verify supervisor delegation
                delegation = websocket.receive_json()
                assert delegation["type"] == "swarm_update"
                assert delegation["event_type"] == "task_delegation"
                assert delegation["supervisor_id"] == supervisor_id
                
                # Verify worker execution
                for worker_id in worker_ids:
                    execution = websocket.receive_json()
                    assert execution["type"] == "swarm_update"
                    assert execution["event_type"] == "task_execution"
                    assert execution["worker_id"] in worker_ids
                
                # Verify results aggregation
                aggregation = websocket.receive_json()
                assert aggregation["type"] == "swarm_update"
                assert aggregation["event_type"] == "results_aggregation"
                
                # Verify swarm relationships in memory
                swarm_structure = await memory_system.semantic.get_relationships(
                    supervisor_id,
                    relationship_type="SUPERVISES"
                )
                assert len(swarm_structure) == len(worker_ids)
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_domain_boundaries(self, memory_system, coordination_agent, tiny_factory):
        """Test domain separation and cross-domain operations."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create agents in different domains
            personal_agent_response = client.post(
                "/api/orchestration/agents/create",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "agent_type": "worker",
                    "domain": "personal",
                    "capabilities": ["task_execution"]
                }
            )
            personal_agent_id = personal_agent_response.json()["agent_id"]
            
            professional_agent_response = client.post(
                "/api/orchestration/agents/create",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    "agent_type": "worker",
                    "domain": "professional",
                    "capabilities": ["task_execution"]
                }
            )
            professional_agent_id = professional_agent_response.json()["agent_id"]
            
            # Test cross-domain operation without approval
            cross_domain_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "domain": "personal",
                    "assigned_agents": [professional_agent_id]
                }
            )
            assert cross_domain_response.status_code == 403
            
            # Test cross-domain operation with approval
            approved_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "domain": "personal",
                    "assigned_agents": [professional_agent_id],
                    "cross_domain_approved": True
                }
            )
            assert approved_response.status_code == 200
            
            # Verify domain boundaries in memory
            personal_data = await memory_system.semantic.search(
                query="domain:personal"
            )
            professional_data = await memory_system.semantic.search(
                query="domain:professional"
            )
            
            assert all(item["domain"] == "personal" for item in personal_data)
            assert all(item["domain"] == "professional" for item in professional_data)
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_swarm_voting(self, memory_system, coordination_agent, tiny_factory):
        """Test majority voting swarm pattern."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create voting agents
            voter_ids = []
            for i in range(5):
                voter_response = client.post(
                    "/api/orchestration/agents/create",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "agent_type": "voter",
                        "domain": "test",
                        "capabilities": ["decision_making"]
                    }
                )
                assert voter_response.status_code == 200
                voter_ids.append(voter_response.json()["agent_id"])
            
            # Create decision task
            task_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "swarm_type": "MajorityVoting",
                    "voter_ids": voter_ids,
                    "decision_threshold": 0.6
                }
            )
            task_id = task_response.json()["task_id"]
            
            # Monitor voting through WebSocket
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                websocket.send_json({
                    "type": "swarm_monitor",
                    "task_id": task_id
                })
                
                # Verify voting process
                votes_received = 0
                for _ in range(len(voter_ids)):
                    vote = websocket.receive_json()
                    assert vote["type"] == "swarm_update"
                    assert vote["event_type"] == "vote_cast"
                    votes_received += 1
                
                # Verify decision
                decision = websocket.receive_json()
                assert decision["type"] == "swarm_update"
                assert decision["event_type"] == "decision_made"
                assert "confidence" in decision
                
                # Verify voting record in memory
                voting_record = await memory_system.semantic.get_relationships(
                    task_id,
                    relationship_type="VOTE_CAST"
                )
                assert len(voting_record) == votes_received
        finally:
            app.dependency_overrides.clear()
            
    @pytest.mark.asyncio
    async def test_parallel_swarm(self, memory_system, coordination_agent, tiny_factory):
        """Test parallel swarm pattern with independent agents."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create parallel processing agents
            agent_ids = []
            for i in range(5):
                agent_response = client.post(
                    "/api/orchestration/agents/create",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "agent_type": "processor",
                        "domain": "test",
                        "capabilities": ["parallel_processing"]
                    }
                )
                assert agent_response.status_code == 200
                agent_ids.append(agent_response.json()["agent_id"])
            
            # Create parallel task
            task_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "swarm_pattern": "parallel",
                    "agent_ids": agent_ids,
                    "subtasks": [
                        {"id": f"subtask_{i}", "data": f"data_{i}"}
                        for i in range(5)
                    ]
                }
            )
            task_id = task_response.json()["task_id"]
            
            # Monitor parallel processing
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                websocket.send_json({
                    "type": "swarm_monitor",
                    "task_id": task_id
                })
                
                # Verify parallel execution
                completed_subtasks = set()
                for _ in range(5):
                    update = websocket.receive_json()
                    assert update["type"] == "swarm_update"
                    assert update["event_type"] == "subtask_completed"
                    completed_subtasks.add(update["subtask_id"])
                
                assert len(completed_subtasks) == 5
                
                # Verify results aggregation
                aggregation = websocket.receive_json()
                assert aggregation["type"] == "swarm_update"
                assert aggregation["event_type"] == "results_aggregation"
                
                # Verify parallel execution records
                execution_records = await memory_system.semantic.get_relationships(
                    task_id,
                    relationship_type="EXECUTED_BY"
                )
                assert len(execution_records) == 5
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_sequential_swarm(self, memory_system, coordination_agent, tiny_factory):
        """Test sequential swarm pattern with ordered task processing."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create sequential processing agents
            agent_ids = []
            agent_types = ["parser", "analyzer", "validator"]
            for agent_type in agent_types:
                agent_response = client.post(
                    "/api/orchestration/agents/create",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "agent_type": agent_type,
                        "domain": "test",
                        "capabilities": [f"{agent_type}_processing"]
                    }
                )
                assert agent_response.status_code == 200
                agent_ids.append(agent_response.json()["agent_id"])
            
            # Create sequential task
            task_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "swarm_pattern": "sequential",
                    "agent_sequence": list(zip(agent_ids, agent_types)),
                    "input_data": "test_data"
                }
            )
            task_id = task_response.json()["task_id"]
            
            # Monitor sequential processing
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                websocket.send_json({
                    "type": "swarm_monitor",
                    "task_id": task_id
                })
                
                # Verify sequential execution
                for agent_type in agent_types:
                    update = websocket.receive_json()
                    assert update["type"] == "swarm_update"
                    assert update["event_type"] == "stage_completed"
                    assert update["stage_type"] == agent_type
                
                # Verify final result
                final = websocket.receive_json()
                assert final["type"] == "swarm_update"
                assert final["event_type"] == "sequence_completed"
                
                # Verify sequential execution order
                execution_sequence = await memory_system.semantic.get_relationships(
                    task_id,
                    relationship_type="EXECUTED_IN_SEQUENCE"
                )
                assert len(execution_sequence) == len(agent_types)
                for i, record in enumerate(execution_sequence):
                    assert record["stage_type"] == agent_types[i]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_mesh_swarm(self, memory_system, coordination_agent, tiny_factory):
        """Test mesh swarm pattern with free-form agent communication."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create mesh agents
            agent_ids = []
            for i in range(5):
                agent_response = client.post(
                    "/api/orchestration/agents/create",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "agent_type": "mesh_node",
                        "domain": "test",
                        "capabilities": ["mesh_communication", "local_processing"]
                    }
                )
                assert agent_response.status_code == 200
                agent_ids.append(agent_response.json()["agent_id"])
            
            # Create mesh task
            task_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "swarm_pattern": "mesh",
                    "agent_ids": agent_ids,
                    "communication_patterns": ["broadcast", "direct", "group"]
                }
            )
            task_id = task_response.json()["task_id"]
            
            # Monitor mesh communication
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                websocket.send_json({
                    "type": "swarm_monitor",
                    "task_id": task_id
                })
                
                # Test broadcast communication
                broadcast = websocket.receive_json()
                assert broadcast["type"] == "swarm_update"
                assert broadcast["event_type"] == "broadcast_message"
                assert len(broadcast["recipients"]) == len(agent_ids)
                
                # Test direct communication
                direct = websocket.receive_json()
                assert direct["type"] == "swarm_update"
                assert direct["event_type"] == "direct_message"
                assert len(direct["recipients"]) == 1
                
                # Test group communication
                group = websocket.receive_json()
                assert group["type"] == "swarm_update"
                assert group["event_type"] == "group_message"
                assert 1 < len(group["recipients"]) < len(agent_ids)
                
                # Verify communication patterns in memory
                communication_records = await memory_system.semantic.get_relationships(
                    task_id,
                    relationship_type="COMMUNICATION_PATTERN"
                )
                pattern_types = [record["pattern_type"] for record in communication_records]
                assert "broadcast" in pattern_types
                assert "direct" in pattern_types
                assert "group" in pattern_types
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_nova_swarm_decisions(self, memory_system, coordination_agent, tiny_factory):
        """Test Nova's decision-making about swarm patterns."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory,
            get_orchestration_agent: lambda: OrchestrationAgent(
                name="test_orchestrator",
                memory_system=memory_system,
                domain="test"
            )
        })
        
        try:
            client = TestClient(app)
            
            # Test Nova's pattern selection for different task types
            test_cases = [
                {
                    "task": {
                        "type": "data_processing",
                        "subtasks": [{"id": f"subtask_{i}"} for i in range(10)],
                        "requirements": {
                            "parallel_execution": True,
                            "independent_tasks": True
                        }
                    },
                    "expected_pattern": "parallel"
                },
                {
                    "task": {
                        "type": "workflow",
                        "stages": ["parse", "analyze", "validate"],
                        "requirements": {
                            "ordered_execution": True,
                            "stage_dependencies": True
                        }
                    },
                    "expected_pattern": "sequential"
                },
                {
                    "task": {
                        "type": "decision_making",
                        "options": ["A", "B", "C"],
                        "requirements": {
                            "consensus_needed": True,
                            "multiple_perspectives": True
                        }
                    },
                    "expected_pattern": "majority_voting"
                }
            ]
            
            for test_case in test_cases:
                # Request Nova to decide swarm pattern
                decision_response = client.post(
                    "/api/orchestration/swarms/decide",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "task": test_case["task"],
                        "domain": "test"
                    }
                )
                assert decision_response.status_code == 200
                decision_data = decision_response.json()
                
                # Verify Nova chose the expected pattern
                assert decision_data["selected_pattern"] == test_case["expected_pattern"]
                assert "reasoning" in decision_data
                assert "confidence" in decision_data
                
                # Verify decision was stored in memory
                decision_record = await memory_system.semantic.search(
                    query=f"type:swarm_decision AND task_id:{decision_data['task_id']}"
                )
                assert len(decision_record) > 0
                assert decision_record[0]["selected_pattern"] == test_case["expected_pattern"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_round_robin_swarm(self, memory_system, coordination_agent, tiny_factory):
        """Test round-robin swarm type with cyclic task distribution."""
        app.dependency_overrides.update({
            get_memory_system: lambda: memory_system,
            get_coordination_agent: lambda: coordination_agent,
            get_tiny_factory: lambda: tiny_factory
        })
        
        try:
            client = TestClient(app)
            
            # Create round-robin agents
            agent_ids = []
            for i in range(3):
                agent_response = client.post(
                    "/api/orchestration/agents/create",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={
                        "agent_type": "processor",
                        "domain": "test",
                        "capabilities": ["task_processing"]
                    }
                )
                assert agent_response.status_code == 200
                agent_ids.append(agent_response.json()["agent_id"])
            
            # Create round-robin task
            task_response = client.post(
                "/api/orchestration/tasks",
                headers={"X-API-Key": TEST_API_KEY},
                json={
                    **VALID_TASK,
                    "swarm_type": "RoundRobin",
                    "agent_ids": agent_ids,
                    "subtasks": [
                        {"id": f"subtask_{i}", "data": f"data_{i}"}
                        for i in range(9)  # 9 tasks for 3 agents = 3 full cycles
                    ]
                }
            )
            task_id = task_response.json()["task_id"]
            
            # Monitor round-robin distribution
            with client.websocket_connect("/api/analytics/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
                websocket.send_json({
                    "type": "swarm_monitor",
                    "task_id": task_id
                })
                
                # Track task assignments
                assignments = {agent_id: [] for agent_id in agent_ids}
                for _ in range(9):
                    update = websocket.receive_json()
                    assert update["type"] == "swarm_update"
                    assert update["event_type"] == "task_assigned"
                    assignments[update["agent_id"]].append(update["subtask_id"])
                
                # Verify even distribution
                for agent_id in agent_ids:
                    assert len(assignments[agent_id]) == 3
                
                # Verify cyclic pattern
                for i in range(3):
                    cycle = [assignments[agent_id][i] for agent_id in agent_ids]
                    assert cycle == [f"subtask_{i*3+j}" for j in range(3)]
                
                # Verify round-robin records in memory
                distribution_records = await memory_system.semantic.get_relationships(
                    task_id,
                    relationship_type="TASK_DISTRIBUTION"
                )
                assert len(distribution_records) == 9
        finally:
            app.dependency_overrides.clear()
