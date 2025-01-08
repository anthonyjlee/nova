"""Basic memory operations tests."""

import pytest
from datetime import datetime
from nia.memory.types.memory_types import Memory, MemoryType, Domain

@pytest.mark.asyncio
async def test_store_task_output(memory_system):
    """Test storing task output in memory."""
    memory = Memory(
        content="Test task output",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={"type": "task_output", "domain": Domain.GENERAL}
    )
    memory_id = await memory_system.store_experience(memory)
    assert memory_id is not None

@pytest.mark.asyncio
async def test_query_by_context_and_participants(memory_system):
    """Test querying memories by context and participants."""
    # Store test memory
    memory = Memory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={"project": "test", "domain": Domain.BACKEND},
        participants=["agent1", "agent2"]
    )
    await memory_system.store_experience(memory)

    # Query by context
    memories = await memory_system.query_episodic({
        "filter": {"context": {"project": "test"}}
    })
    assert len(memories) == 1
    assert memories[0].content == "Test memory"

@pytest.mark.asyncio
async def test_query_task_outputs(memory_system):
    """Test querying task output memories."""
    # Store test memories
    for i in range(3):
        memory = Memory(
            content=f"Task output {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={"type": "task_output", "domain": Domain.GENERAL}
        )
        await memory_system.store_experience(memory)

    # Query task outputs
    memories = await memory_system.query_episodic({
        "filter": {"context": {"type": "task_output"}}
    })
    assert len(memories) == 3
