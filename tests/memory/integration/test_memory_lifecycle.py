"""Memory lifecycle tests."""

import pytest
from datetime import datetime, timedelta
from nia.memory.types.memory_types import Memory, MemoryType, Domain

@pytest.mark.asyncio
async def test_memory_cleanup(memory_system):
    """Test memory cleanup operations."""
    # Store memories with different timestamps
    old_memory = Memory(
        content="Old memory",
        type=MemoryType.EPISODIC,
        timestamp=(datetime.now() - timedelta(days=31)).isoformat(),
        importance=0.3,
        context={
            "type": "old",
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        }
    )
    await memory_system.store_experience(old_memory)

    recent_memory = Memory(
        content="Recent memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.3,
        context={
            "type": "recent",
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        }
    )
    await memory_system.store_experience(recent_memory)

    # Trigger cleanup
    cleanup_stats = await memory_system.prune()
    assert cleanup_stats["pruned_memories"] > 0

    # Verify old memory was cleaned up
    old_results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "type": "old",
                "access_domain": "professional"
            }
        }
    })
    assert len(old_results) == 0

    # Verify recent memory remains
    recent_results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "type": "recent",
                "access_domain": "professional"
            }
        }
    })
    assert len(recent_results) == 1

@pytest.mark.asyncio
async def test_cross_domain_cleanup(memory_system):
    """Test cleanup respects domain boundaries."""
    # Store old memories in different domains
    old_prof_memory = Memory(
        content="Old professional memory",
        type=MemoryType.EPISODIC,
        timestamp=(datetime.now() - timedelta(days=31)).isoformat(),
        importance=0.3,
        context={
            "type": "old",
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        }
    )
    await memory_system.store_experience(old_prof_memory)

    old_personal_memory = Memory(
        content="Old personal memory",
        type=MemoryType.EPISODIC,
        timestamp=(datetime.now() - timedelta(days=31)).isoformat(),
        importance=0.8,  # Higher importance
        context={
            "type": "old",
            "domain": Domain.GENERAL,
            "access_domain": "personal"
        }
    )
    await memory_system.store_experience(old_personal_memory)

    # Trigger cleanup
    cleanup_stats = await memory_system.prune()
    assert cleanup_stats["pruned_memories"] > 0

    # Verify low importance professional memory was cleaned up
    prof_results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "access_domain": "professional",
                "type": "old"
            }
        }
    })
    assert len(prof_results) == 0

    # Verify high importance personal memory remains
    personal_results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "access_domain": "personal",
                "type": "old"
            }
        }
    })
    assert len(personal_results) == 1

@pytest.mark.asyncio
async def test_task_output_lifecycle(memory_system):
    """Test complete lifecycle of task output memories."""
    # Store task output
    memory = Memory(
        content="Task output",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "type": "task_output",
            "status": "pending",
            "domain": Domain.BACKEND,
            "access_domain": "professional"
        }
    )
    memory_id = await memory_system.store_experience(memory)

    # Update task status
    updated_memory = Memory(
        content="Task output",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "type": "task_output",
            "status": "completed",
            "domain": Domain.BACKEND,
            "access_domain": "professional"
        }
    )
    await memory_system.store_experience(updated_memory)

    # Verify status update
    result = await memory_system.get_memory(memory_id)
    assert result.context["status"] == "completed"

    # Archive task output
    await memory_system.consolidate_memories()

    # Verify task was archived
    results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "type": "task_output",
                "status": "completed",
                "domain": Domain.BACKEND,
                "access_domain": "professional"
            }
        }
    })
    assert len(results) == 0  # Should be moved to semantic layer

@pytest.mark.asyncio
async def test_cross_domain_task_lifecycle(memory_system):
    """Test lifecycle of tasks that span domains."""
    # Store cross-domain task
    memory = Memory(
        content="Cross-domain task",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "type": "task_output",
            "status": "pending",
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Task spans personal and professional domains",
                "source_domain": "professional",
                "target_domain": "personal"
            }
        }
    )
    memory_id = await memory_system.store_experience(memory)

    # Update task status
    updated_memory = Memory(
        content="Cross-domain task",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "type": "task_output",
            "status": "completed",
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Task spans personal and professional domains",
                "source_domain": "professional",
                "target_domain": "personal"
            }
        }
    )
    await memory_system.store_experience(updated_memory)

    # Verify status update preserved cross-domain context
    result = await memory_system.get_memory(memory_id)
    assert result.context["status"] == "completed"
    assert result.context["cross_domain"]["approved"] == True

    # Archive task
    await memory_system.consolidate_memories()

    # Verify task was archived with cross-domain context
    results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "type": "task_output",
                "status": "completed",
                "cross_domain.approved": True
            }
        }
    })
    assert len(results) == 0  # Should be moved to semantic layer

    # Verify task is accessible from both domains in semantic layer
    prof_results = await memory_system.query_semantic({
        "type": "task",
        "context": {
            "access_domain": "professional",
            "cross_domain.approved": True
        }
    })
    assert len(prof_results) > 0

    personal_results = await memory_system.query_semantic({
        "type": "task",
        "context": {
            "access_domain": "personal",
            "cross_domain.approved": True
        }
    })
    assert len(personal_results) > 0
