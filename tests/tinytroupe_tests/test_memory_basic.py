"""Tests for basic memory operations in TinyTroupe."""

import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock
from tests.nova.test_utils import (
    with_vector_store_retry,
    TestContext
)

from nia.memory.types.memory_types import (
    Memory, MemoryType, EpisodicMemory, TaskOutput,
    OutputType, TaskStatus, Concept
)

logger = logging.getLogger(__name__)

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
async def test_query_by_context_and_participants(nova):
    """Test querying memories by context and participants."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="query_agent",
            attributes={
                "skills": ["development"],
                "domain": domain
            }
        )
        
        # Store test memories
        memories = [
            {
                "content": "Meeting about project A",
                "context": {"project": "A"},
                "participants": ["Alice", "Bob"],
                "concepts": [
                    {
                        "name": "Project A",
                        "type": "Project",
                        "category": "Project",
                        "description": "Project A meeting and discussion",
                        "attributes": {"status": "active"},
                        "confidence": 0.8
                    }
                ]
            },
            {
                "content": "Meeting about project B",
                "context": {"project": "B"},
                "participants": ["Charlie", "David"],
                "concepts": [
                    {
                        "name": "Project B",
                        "type": "Project",
                        "category": "Project",
                        "description": "Project B meeting and discussion",
                        "attributes": {"status": "active"},
                        "confidence": 0.8
                    }
                ]
            }
        ]
        
        # Store memories
        memory_ids = []
        for memory in memories:
            memory_id = await agent.store_memory(
                content=memory["content"],
                importance=0.8,
                context=memory["context"],
                participants=memory["participants"],
                concepts=memory["concepts"]
            )
            memory_ids.append(memory_id)
        
        # Mock query results
        mock_memories = []
        for i, memory in enumerate(memories):
            mock_memory = nova.create_memory_mock(
                content=memory["content"],
                context=memory["context"],
                participants=memory["participants"],
                concepts=memory["concepts"]
            )
            mock_memory.id = memory_ids[i]
            mock_memories.append(mock_memory)
        
        nova.memory_system.episodic.store.search_vectors = AsyncMock(return_value=mock_memories)
        
        # Query by project context
        results = await agent.recall_memories(
            query={
                "filter": {
                    "context": {
                        "project": "A"
                    }
                }
            }
        )
        
        # Verify project filter
        assert len(results) == 1
        assert results[0].context["project"] == "A"
        assert "Alice" in results[0].participants
        assert "Bob" in results[0].participants
        
        # Query by participants
        results = await agent.recall_memories(
            query={
                "filter": {
                    "participants": ["Charlie"]
                }
            }
        )
        
        # Verify participant filter
        assert len(results) == 1
        assert results[0].context["project"] == "B"
        assert "Charlie" in results[0].participants
        assert "David" in results[0].participants

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
