"""Tests for TinyTroupe memory integration."""

import pytest
import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from tests.nova.test_utils import (
    with_vector_store_retry,
    TestContext,
    VectorStoreError
)

logger = logging.getLogger(__name__)

from nia.memory.types.memory_types import (
    Memory, MemoryType, EpisodicMemory, TaskOutput,
    OutputType, TaskStatus, Concept, Relationship
)
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.memory.consolidation import ConsolidationManager
from nia.world.environment import NIAWorld
from nia.nova.orchestrator import Nova

def format_timestamp():
    """Helper to format timestamp consistently."""
    dt = datetime.now(timezone.utc)
    # Format timestamp as string to match Memory.timestamp type
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def create_memory_dict(content, memory_type=MemoryType.EPISODIC, context=None, metadata=None, concepts=None, relationships=None):
    """Helper to create memory dictionary with proper timestamp."""
    return {
        "content": content,
        "type": memory_type,
        "timestamp": format_timestamp(),
        "context": context or {},
        "metadata": metadata or {},
        "concepts": concepts or [],
        "relationships": relationships or []
    }

@pytest.fixture
def memory_system():
    """Create memory system with mock stores."""
    vector_store = AsyncMock()
    neo4j_store = AsyncMock()
    system = TwoLayerMemorySystem(neo4j_uri="bolt://localhost:7687", vector_store=vector_store)
    system.semantic.driver = neo4j_store
    system.consolidation_manager = ConsolidationManager(system.episodic, system.semantic)
    
    # Set up async mock behaviors for vector store
    async def store_vector_mock(**kwargs):
        return "memory_id_1"
    vector_store.store_vector = AsyncMock(side_effect=store_vector_mock)
    vector_store.search_vectors = AsyncMock(return_value=[])
    vector_store.archive_memories = AsyncMock()
    vector_store.delete_vectors = AsyncMock()
    
    # Set up async mock behaviors for neo4j store
    async def store_knowledge_mock(knowledge):
        # Filter out any auto-generated concepts and keep only the explicitly defined ones from the test
        concepts = [c for c in knowledge["concepts"] if c["name"] in {
            "API Endpoint", "User Profile", "Task Request", "Agent Collaboration",
            "Hello Function", "User Processing", "API Documentation"
        }]
        return {"concepts": concepts, "relationships": knowledge["relationships"]}
    neo4j_store.store_knowledge = AsyncMock(side_effect=store_knowledge_mock)
    neo4j_store.query_knowledge = AsyncMock(return_value=[])
    neo4j_store.query = AsyncMock(return_value=[])
    
    # Set up async mock behaviors for episodic memory
    system.episodic.store = vector_store
    system.episodic.store_memory = AsyncMock(return_value="memory_id_1")
    system.episodic.get_consolidation_candidates = AsyncMock(return_value=[])
    system.episodic.query_memories = AsyncMock(return_value=[])
    
    # Set up async mock behaviors for semantic memory
    system.semantic.driver = neo4j_store
    system.semantic.store_knowledge = AsyncMock(side_effect=store_knowledge_mock)
    system.semantic.query_knowledge = AsyncMock(return_value=[])
    system.semantic.query = AsyncMock(return_value=[])  # Add query method to semantic layer
    
    return system

@pytest.fixture
def world(memory_system):
    """Create world environment for testing."""
    return NIAWorld(memory_system=memory_system)

@pytest.fixture
def nova(memory_system, world):
    """Create Nova orchestrator for testing."""
    nova = Nova(memory_system=memory_system, world=world)
    
    # Set up mock memory behaviors
    def create_memory_mock(content, memory_type=MemoryType.EPISODIC, context=None, metadata=None, concepts=None, relationships=None):
        timestamp = format_timestamp()
        memory_dict = {
            "content": content,
            "type": memory_type,
            "timestamp": timestamp,
            "context": context or {},
            "metadata": metadata or {},
            "concepts": concepts or [],
            "relationships": relationships or [],
            "consolidated": False
        }
        
        memory = Mock(spec=EpisodicMemory)
        memory.content = content
        memory.type = memory_type
        memory.timestamp = timestamp
        memory.context = memory_dict["context"]
        memory.metadata = memory_dict["metadata"]
        memory.concepts = memory_dict["concepts"]
        memory.relationships = memory_dict["relationships"]
        memory.consolidated = False
        
        # Set up dictionary-like behavior
        memory.get = Mock(return_value=memory_dict)
        memory.keys = Mock(return_value=list(memory_dict.keys()))
        memory.__getitem__ = lambda s, key: memory_dict[key]
        memory.__iter__ = lambda s: iter(memory_dict.items())
        memory.__contains__ = lambda s, key: key in memory_dict
        memory.__len__ = lambda s: len(memory_dict)
        memory.items = lambda: memory_dict.items()
        
        # Set up async behavior
        memory.__aiter__ = AsyncMock(return_value=memory_dict.items())
        memory.__await__ = AsyncMock(return_value=memory_dict)
        
        return memory
    
    nova.create_memory_mock = create_memory_mock
    
    return nova

@pytest.mark.asyncio
async def test_store_task_output(nova):
    """Test storing task output in memory system."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="code_agent_store",
            attributes={
                "skills": ["python"],
                "domain": domain
            }
        )
    
    # Create task output
    output = TaskOutput(
        task_id="task1",
        type=OutputType.CODE,
        content="def hello(): print('Hello')",
        metadata={
            "language": "python",
            "agents": [{
                "name": agent.name,
                "type": "worker",
                "skills": ["python"],
                "state": "active"
            }],
            "tasks": [{
                "name": "Implement Hello Function",
                "category": "development",
                "description": "Implement a simple hello function",
                "status": "completed",
                "priority": "medium"
            }]
        }
    )
    
    # Store output through agent
    @with_vector_store_retry
    async def store_memory():
        return await agent.store_memory(
            content=output.content,
            importance=0.8,
            context={
                "task_id": output.task_id,
                "output_type": output.type.value,
                "agent_type": "worker",
                "domain": "development"
            },
            metadata=output.metadata,
            concepts=[{
                "name": "Hello Function",
                "type": "Function",
                "category": "code",
                "description": "Simple hello world function",
                "attributes": {"language": "python"},
                "confidence": 0.9
            }]
        )
    
    # Store and verify
    memory_id = await store_memory()
    stored_memory = nova.memory_system.episodic.store_memory.call_args[0][0]
    
    # Verify storage
    assert stored_memory.content == output.content
    assert stored_memory.type == MemoryType.EPISODIC
    assert stored_memory.context["task_id"] == output.task_id
    assert stored_memory.metadata["agents"][0]["name"] == agent.name
    assert stored_memory.metadata["tasks"][0]["name"] == "Implement Hello Function"

@pytest.mark.asyncio
async def test_query_task_outputs(nova):
    """Test querying task outputs from memory system."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="code_agent_query",
            attributes={
                "skills": ["python"],
                "domain": domain
            }
        )
    
    # Mock stored outputs
    mock_memories = [
        nova.create_memory_mock(
            content="def hello(): print('Hello')",
            context={
                "task_id": "task1",
                "output_type": "code",
                "agent_type": "worker",
                "domain": "development"
            },
            metadata={
                "language": "python",
                "agents": [{
                    "name": agent.name,
                    "type": "worker",
                    "skills": ["python"],
                    "state": "active"
                }]
            }
        ),
        nova.create_memory_mock(
            content="API Documentation",
            context={
                "task_id": "task1",
                "output_type": "document",
                "agent_type": "worker",
                "domain": "development"
            },
            metadata={
                "format": "markdown",
                "agents": [{
                    "name": agent.name,
                    "type": "worker",
                    "skills": ["python"],
                    "state": "active"
                }]
            }
        )
    ]
    
    nova.memory_system.episodic.store.search_vectors = AsyncMock(return_value=mock_memories)
    
    # Query outputs through agent
    @with_vector_store_retry
    async def query_memories():
        return await agent.recall_memories(
            query={
                "filter": {
                    "context": {
                        "task_id": "task1",
                        "agent_type": "worker"
                    }
                }
            }
        )
    
    try:
        results = await query_memories()
        
        # Verify query
        assert len(results) == 2
        assert results[0].content == "def hello(): print('Hello')"
        assert results[0].context["output_type"] == "code"
        assert results[0].metadata["agents"][0]["name"] == agent.name
        assert results[1].content == "API Documentation"
        assert results[1].context["output_type"] == "document"
        assert results[1].metadata["agents"][0]["name"] == agent.name
    except Exception as e:
        logger.error(f"Failed to query memories: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_consolidate_task_knowledge(nova):
    """Test consolidating task outputs into semantic knowledge."""
    domain = "backend"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="backend",
            name="api_agent_consolidate",
            attributes={
                "skills": ["api_development"],
                "domain": domain
            }
        )
    
    # Store memory through agent
    @with_vector_store_retry
    async def store_memory():
        return await agent.store_memory(
            content="Implemented API endpoint for user profiles",
            importance=0.8,
            context={
                "task_id": "task1",
                "domain": "backend",
                "agent_type": "backend"
            },
            metadata={
                "agents": [
                    {
                        "name": agent.name,
                        "type": "backend",
                        "skills": ["api_development"],
                        "state": "active"
                    }
                ],
                "tasks": [
                    {
                        "name": "Implement User API",
                        "category": "development",
                        "description": "Implement REST API for user profiles",
                        "status": "completed",
                        "priority": "high"
                    }
                ]
            },
            concepts=[
                {
                    "name": "API Endpoint",
                    "type": "Component",
                    "category": "backend",
                    "description": "REST API endpoint implementation",
                    "attributes": {},
                    "confidence": 0.9
                },
                {
                    "name": "User Profile",
                    "type": "Domain",
                    "category": "data",
                    "description": "User profile data and operations",
                    "attributes": {},
                    "confidence": 0.9
                }
            ],
            relationships=[
                {
                    "from_concept": "API Endpoint",
                    "to_concept": "User Profile",
                    "type": "manages",
                    "properties": {}
                }
            ]
        )
    
    # Mock consolidation candidates
    memory_dict = create_memory_dict(
        content="Implemented API endpoint for user profiles",
        context={
            "task_id": "task1",
            "domain": "backend",
            "agent_type": "backend"
        },
        metadata={
            "agents": [
                {
                    "name": agent.name,
                    "type": "backend",
                    "skills": ["api_development"],
                    "state": "active"
                }
            ],
            "tasks": [
                {
                    "name": "Implement User API",
                    "category": "development",
                    "description": "Implement REST API for user profiles",
                    "status": "completed",
                    "priority": "high"
                }
            ]
        },
        concepts=[
            {
                "name": "API Endpoint",
                "type": "Component",
                "category": "backend",
                "description": "REST API endpoint implementation",
                "attributes": {},
                "confidence": 0.9
            },
            {
                "name": "User Profile",
                "type": "Domain",
                "category": "data",
                "description": "User profile data and operations",
                "attributes": {},
                "confidence": 0.9
            }
        ],
        relationships=[
            {
                "from_concept": "API Endpoint",
                "to_concept": "User Profile",
                "type": "manages",
                "properties": {}
            }
        ]
    )
    
    # Create mock memory with proper dictionary access
    memory = Mock(spec=EpisodicMemory)
    memory.get = Mock(side_effect=memory_dict.get)
    memory.__getitem__ = Mock(side_effect=memory_dict.__getitem__)
    memory.items = Mock(return_value=memory_dict.items())
    memory.__iter__ = Mock(return_value=iter(memory_dict.items()))
    
    nova.memory_system.episodic.get_consolidation_candidates = AsyncMock(return_value=[memory])
    
    # Trigger consolidation through agent
    @with_vector_store_retry
    async def consolidate():
        return await agent.reflect()
    
    await consolidate()
    
    # Verify semantic storage
    nova.memory_system.semantic.store_knowledge.assert_called_once()
    stored_knowledge = nova.memory_system.semantic.store_knowledge.call_args[0][0]
    
    # Verify concepts were stored
    assert len(stored_knowledge["concepts"]) == 2
    assert stored_knowledge["concepts"][0]["name"] == "API Endpoint"
    assert stored_knowledge["concepts"][1]["name"] == "User Profile"
    
    # Verify relationships were stored
    assert len(stored_knowledge["relationships"]) == 1
    assert stored_knowledge["relationships"][0]["from"] == "API Endpoint"
    assert stored_knowledge["relationships"][0]["to"] == "User Profile"
    assert stored_knowledge["relationships"][0]["type"] == "manages"

@pytest.mark.asyncio
async def test_query_task_knowledge(nova):
    """Test querying consolidated task knowledge."""
    domain = "backend"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="backend",
            name="api_agent_query",
            attributes={
                "skills": ["api_development"],
                "domain": domain
            }
        )
    
    # Mock semantic query results
    mock_results = [
        {
            "name": "API Endpoint",
            "type": "Component",
            "description": "REST API endpoint implementation",
            "metadata": {
                "agent": agent.name,
                "domain": "backend"
            },
            "related": [
                {
                    "name": "User Profile",
                    "type": "Domain",
                    "relationship": "manages",
                    "metadata": {
                        "agent": agent.name,
                        "domain": "backend"
                    }
                }
            ]
        }
    ]
    
    nova.memory_system.semantic.query_knowledge = AsyncMock(return_value=mock_results)
    
    # Query semantic knowledge through agent
    results = await agent.query_knowledge({
        "type": "Component",
        "domain": "backend",
        "agent": agent.name
    })
    
    # Verify query results
    assert len(results) == 1
    assert results[0]["name"] == "API Endpoint"
    assert results[0]["metadata"]["agent"] == agent.name
    assert len(results[0]["related"]) == 1
    assert results[0]["related"][0]["name"] == "User Profile"
    assert results[0]["related"][0]["metadata"]["agent"] == agent.name

@pytest.mark.asyncio
async def test_task_output_lifecycle(nova):
    """Test complete lifecycle of task outputs through memory system."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="code_agent_lifecycle",
            attributes={
                "skills": ["python"],
                "domain": domain
            }
        )
    
    # 1. Store initial output through agent
    output = TaskOutput(
        task_id="task1",
        type=OutputType.CODE,
        content="def process_user(data): ...",
        metadata={
            "language": "python",
            "agents": [{
                "name": agent.name,
                "type": "worker",
                "skills": ["python"],
                "state": "active"
            }]
        }
    )
    
    @with_vector_store_retry
    async def store_initial_memory():
        return await agent.store_memory(
            content=output.content,
            importance=0.8,
            context={
                "task_id": output.task_id,
                "output_type": output.type.value,
                "agent_type": "worker",
                "domain": "development"
            },
            metadata=output.metadata,
            concepts=[
                Concept(
                    name="User Processing",
                    type="Function",
                    description="Function to process user data"
                )
            ]
        )
    
    # 2. Store related output through agent
    related_output = TaskOutput(
        task_id="task1",
        type=OutputType.DOCUMENT,
        content="## User Processing API\n\nEndpoint for processing user data...",
        metadata={
            "format": "markdown",
            "agents": [{
                "name": agent.name,
                "type": "worker",
                "skills": ["python"],
                "state": "active"
            }]
        }
    )
    
    @with_vector_store_retry
    async def store_related_memory():
        return await agent.store_memory(
            content=related_output.content,
            importance=0.8,
            context={
                "task_id": output.task_id,
                "output_type": related_output.type.value,
                "agent_type": "worker",
                "domain": "development"
            },
            metadata=related_output.metadata,
            concepts=[
                Concept(
                    name="API Documentation",
                    type="Document",
                    description="Documentation for user processing API"
                ),
                Concept(
                    name="User Processing",
                    type="Function",
                    description="Function to process user data"
                )
            ],
            relationships=[
                Relationship(
                    from_="API Documentation",
                    to="User Processing",
                    type="documents"
                )
            ]
        )
    
    # 3. Query outputs through agent
    mock_memories = [
        nova.create_memory_mock(
            content=output.content,
            context={
                "task_id": "task1",
                "output_type": output.type.value,
                "agent_type": "worker",
                "domain": "development"
            },
            metadata={
                "language": "python",
                "agents": [{
                    "name": agent.name,
                    "type": "worker",
                    "skills": ["python"],
                    "state": "active"
                }]
            }
        ),
        nova.create_memory_mock(
            content=related_output.content,
            context={
                "task_id": "task1",
                "output_type": related_output.type.value,
                "agent_type": "worker",
                "domain": "development"
            },
            metadata={
                "format": "markdown",
                "agents": [{
                    "name": agent.name,
                    "type": "worker",
                    "skills": ["python"],
                    "state": "active"
                }]
            }
        )
    ]
    
    nova.memory_system.episodic.store.search_vectors = AsyncMock(return_value=mock_memories)
    @with_vector_store_retry
    async def query_memories():
        return await agent.recall_memories(
            query={
                "filter": {
                    "context": {
                        "task_id": "task1",
                        "agent_type": "worker"
                    }
                }
            }
        )
    
    try:
        results = await query_memories()
        
        assert len(results) == 2
        assert results[0].content == output.content
        assert results[0].metadata["agents"][0]["name"] == agent.name
        assert results[1].content == related_output.content
        assert results[1].metadata["agents"][0]["name"] == agent.name
    except Exception as e:
        logger.error(f"Failed to query memories: {str(e)}")
        raise
    
    # 4. Mock consolidation candidates
    memory_dict = create_memory_dict(
        content=output.content,
        context={
            "task_id": output.task_id,
            "output_type": output.type.value,
            "agent_type": "worker",
            "domain": "development"
        },
        metadata={
            "agents": [{
                "name": agent.name,
                "type": "worker",
                "skills": ["python"],
                "state": "active"
            }],
            "tasks": [{
                "name": "User Processing",
                "category": "function",
                "description": "Function to process user data",
                "status": "completed",
                "priority": "high"
            }]
        },
        concepts=[{
            "name": "User Processing",
            "type": "Function",
            "category": "backend",
            "description": "Function to process user data",
            "attributes": {},
            "confidence": 0.9
        }]
    )
    
    # Create mock memory with proper dictionary access
    memory = Mock(spec=EpisodicMemory)
    memory.get = Mock(side_effect=memory_dict.get)
    memory.__getitem__ = Mock(side_effect=memory_dict.__getitem__)
    memory.items = Mock(return_value=memory_dict.items())
    memory.__iter__ = Mock(return_value=iter(memory_dict.items()))
    
    nova.memory_system.episodic.get_consolidation_candidates = AsyncMock(return_value=[memory])
    
    # Trigger consolidation through agent
    @with_vector_store_retry
    async def consolidate():
        return await agent.reflect()
    
    await consolidate()
    
    # 5. Mock semantic query results
    mock_results = [{
        "name": "User Processing",
        "type": "Function",
        "description": "Function to process user data",
        "metadata": {
            "agent": agent.name,
            "domain": "development"
        },
        "related": [{
            "name": "API Documentation",
            "type": "Document",
            "relationship": "documents",
            "metadata": {
                "agent": agent.name,
                "domain": "development"
            }
        }]
    }]
    
    nova.memory_system.semantic.query_knowledge = AsyncMock(return_value=mock_results)
    
    # Query consolidated knowledge through agent
    semantic_results = await agent.query_knowledge({
        "type": "Function",
        "domain": "development",
        "agent": agent.name
    })
    
    assert len(semantic_results) == 1
    assert semantic_results[0]["name"] == "User Processing"
    assert semantic_results[0]["metadata"]["agent"] == agent.name
    assert semantic_results[0]["related"][0]["name"] == "API Documentation"
    assert semantic_results[0]["related"][0]["metadata"]["agent"] == agent.name

@pytest.mark.asyncio
async def test_memory_error_handling(nova):
    """Test error handling in memory system."""
    domain = "testing"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="test_agent",
            attributes={
                "skills": ["testing"],
                "domain": domain
            }
        )
    
    # Mock store errors
    async def raise_storage_error(*args, **kwargs):
        raise VectorStoreError("Storage error")
    nova.memory_system.episodic.store_memory = AsyncMock(side_effect=raise_storage_error)
    
    # Test storage error handling through agent
    @with_vector_store_retry
    async def store_memory():
        return await agent.store_memory(
            content="Test content",
            importance=0.8,
            context={
                "task_id": "test_task",
                "agent_type": "worker",
                "domain": "testing"
            },
            metadata={
                "agents": [{
                    "name": agent.name,
                    "type": "worker",
                    "skills": ["testing"],
                    "state": "active"
                }]
            }
        )
    
    try:
        await store_memory()
        pytest.fail("Expected VectorStoreError")
    except VectorStoreError as e:
        assert "Storage error" in str(e)
    
    # Mock consolidation error
    async def raise_consolidation_error(*args, **kwargs):
        raise VectorStoreError("Failed to extract knowledge")
    nova.memory_system.consolidation_manager.extract_knowledge = AsyncMock(side_effect=raise_consolidation_error)
    nova.memory_system.episodic.get_consolidation_candidates = AsyncMock(return_value=[Mock()])
    
    # Test consolidation error handling through agent
    @with_vector_store_retry
    async def consolidate():
        return await agent.reflect()
    
    try:
        await consolidate()
        pytest.fail("Expected VectorStoreError")
    except VectorStoreError as e:
        assert "Failed to extract knowledge" in str(e)

@pytest.mark.asyncio
async def test_tinytroupe_agent_interaction(nova):
    """Test interaction between TinyTroupe agents."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create supervisor and worker agents
        supervisor = await nova.spawn_agent(
            agent_type="supervisor",
            name="supervisor_agent",
            attributes={
                "skills": ["task_delegation"],
                "domain": domain
            }
        )
        
        worker = await nova.spawn_agent(
            agent_type="worker",
            name="worker_agent",
            attributes={
                "skills": ["task_execution"],
                "domain": domain
            }
        )
    
    # Store interaction through supervisor agent
    @with_vector_store_retry
    async def store_interaction():
        return await supervisor.store_memory(
            content="Requested task completion from worker agent",
            importance=0.8,
            context={
                "agent_from": supervisor.name,
                "agent_to": worker.name,
                "interaction_type": "task_request",
                "domain": "development"
            },
            metadata={
                "agents": [
                    {
                        "name": supervisor.name,
                        "type": "supervisor",
                        "skills": ["task_delegation"],
                        "state": "active"
                    },
                    {
                        "name": worker.name,
                        "type": "worker",
                        "skills": ["task_execution"],
                        "state": "available"
                    }
                ],
                "tasks": [
                    {
                        "name": "Task Request Pattern",
                        "category": "interaction",
                        "description": "Agent interaction pattern for task delegation",
                        "status": "active",
                        "priority": "high"
                    }
                ]
            },
            concepts=[
                {
                    "name": "Task Request",
                    "type": "Interaction",
                    "category": "pattern",
                    "description": "Agent requesting task completion",
                    "attributes": {
                        "from_type": "supervisor",
                        "to_type": "worker"
                    },
                    "confidence": 0.9
                },
                {
                    "name": "Agent Collaboration",
                    "type": "Pattern",
                    "category": "behavior",
                    "description": "Agents working together on tasks",
                    "attributes": {
                        "pattern_type": "delegation"
                    },
                    "confidence": 0.9
                }
            ],
            relationships=[
                {
                    "from_concept": "Task Request",
                    "to_concept": "Agent Collaboration",
                    "type": "implements",
                    "properties": {
                        "strength": 0.8,
                        "context": "task_delegation"
                    }
                }
            ]
        )
    
    await store_interaction()

@pytest.mark.asyncio
async def test_tinytroupe_memory_query(nova):
    """Test querying memories between TinyTroupe agents."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create supervisor and worker agents
        supervisor = await nova.spawn_agent(
            agent_type="supervisor",
            name="supervisor_agent",
            attributes={
                "skills": ["task_delegation"],
                "domain": domain
            }
        )
        
        worker = await nova.spawn_agent(
            agent_type="worker",
            name="worker_agent",
            attributes={
                "skills": ["task_execution"],
                "domain": domain
            }
        )
    
    # Mock memory for query
    mock_memory = nova.create_memory_mock(
        content="Requested task completion from worker agent",
        context={
            "agent_from": supervisor.name,
            "agent_to": worker.name,
            "interaction_type": "task_request",
            "domain": "development"
        },
        metadata={
            "agents": [
                {
                    "name": supervisor.name,
                    "type": "supervisor",
                    "skills": ["task_delegation"],
                    "state": "active"
                },
                {
                    "name": worker.name,
                    "type": "worker",
                    "skills": ["task_execution"],
                    "state": "available"
                }
            ],
            "tasks": [
                {
                    "name": "Task Request Pattern",
                    "category": "interaction",
                    "description": "Agent interaction pattern for task delegation",
                    "status": "active",
                    "priority": "high"
                }
            ]
        }
    )
    
    nova.memory_system.episodic.store.search_vectors = AsyncMock(return_value=[mock_memory])
    @with_vector_store_retry
    async def query_memories():
        return await worker.recall_memories(
            query={
                "filter": {
                    "context": {
                        "agent_to": worker.name,
                        "interaction_type": "task_request"
                    }
                }
            }
        )
    
    try:
        results = await query_memories()
        
        assert len(results) == 1
        assert results[0].content == mock_memory.content
        assert results[0].context["agent_from"] == supervisor.name
        assert results[0].context["agent_to"] == worker.name
    except Exception as e:
        logger.error(f"Failed to query memories: {str(e)}")
        raise
