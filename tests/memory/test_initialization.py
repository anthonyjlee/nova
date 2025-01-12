"""Tests for memory system initialization and cold-start functionality."""

import pytest
import logging
from datetime import datetime, timezone

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.types.memory_types import (
    ValidationSchema,
    CrossDomainSchema,
    BaseDomain,
    TaskState,
    TaskValidation
)

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_task_structures_initialization(memory_system):
    """Test initialization of task-specific structures."""
    # Verify task states
    result = await memory_system.semantic.run_query(
        "MATCH (s:TaskState) RETURN count(s) as count"
    )
    record = await result.single()
    assert record["count"] == 4, "Task states not properly initialized"

    # Verify task templates
    result = await memory_system.semantic.run_query(
        "MATCH (t:Concept) WHERE t.type = 'task_template' RETURN count(t) as count"
    )
    record = await result.single()
    assert record["count"] >= 2, "Task templates not properly initialized"

    # Verify domain boundaries
    result = await memory_system.semantic.run_query(
        """
        MATCH (d:Domain)
        WHERE d.name IN ['tasks', 'professional', 'personal']
        RETURN count(d) as count
        """
    )
    record = await result.single()
    assert record["count"] == 3, "Domain boundaries not properly initialized"

    # Verify access rules
    result = await memory_system.semantic.run_query(
        """
        MATCH (d:Domain)-[:HAS_RULE]->(r:AccessRule)
        WHERE r.type = 'domain_access'
        RETURN count(r) as count
        """
    )
    record = await result.single()
    assert record["count"] == 3, "Access rules not properly initialized"

@pytest.mark.asyncio
async def test_task_collection_setup(memory_system):
    """Test setup of task-specific collections and indexes."""
    # Verify task_updates collection exists
    collections = await memory_system.episodic.store.list_collections()
    assert "task_updates" in collections, "Task updates collection not created"

    # Verify indexes
    indexes = await memory_system.episodic.store.list_indexes("task_updates")
    required_indexes = ["task_id", "status", "domain", "timestamp"]
    for index in required_indexes:
        assert any(i["field_name"] == index for i in indexes), f"Missing index: {index}"

@pytest.mark.asyncio
async def test_test_data_creation(memory_system):
    """Test creation and validation of test data."""
    # Verify test tasks exist
    result = await memory_system.semantic.run_query(
        """
        MATCH (t:Task)
        WHERE t.id IN ['TEST-001', 'TEST-002']
        RETURN count(t) as count
        """
    )
    record = await result.single()
    assert record["count"] == 2, "Test tasks not properly created"

    # Verify test relationships
    result = await memory_system.semantic.run_query(
        """
        MATCH (t1:Task {id: 'TEST-001'})-[:BLOCKS]->(t2:Task {id: 'TEST-002'})
        RETURN count(*) as count
        """
    )
    record = await result.single()
    assert record["count"] == 1, "Test task relationship not properly created"

@pytest.mark.asyncio
async def test_task_state_transitions(memory_system):
    """Test task state transition validation."""
    # Create test task
    task_id = "TEST-003"
    await memory_system.semantic.run_query(
        """
        CREATE (t:Task {
            id: $id,
            status: $status,
            domain: $domain
        })
        """,
        {
            "id": task_id,
            "status": TaskState.PENDING.value,
            "domain": "professional"
        }
    )

    # Test valid transition
    validation = TaskValidation(
        state=TaskState.IN_PROGRESS,
        domain="professional",
        team_id="test-team"
    )
    assert await validation.validate_state_transition(task_id, TaskState.IN_PROGRESS.value)

    # Test invalid transition
    validation.state = TaskState.COMPLETED
    with pytest.raises(Exception):
        await validation.validate_state_transition(task_id, TaskState.BLOCKED.value)

@pytest.mark.asyncio
async def test_domain_access_validation(memory_system):
    """Test domain access validation."""
    # Test valid domain access
    assert await memory_system.semantic.validate_domain_access("professional")

    # Test invalid domain access
    with pytest.raises(Exception):
        await memory_system.semantic.validate_domain_access("invalid_domain")

@pytest.mark.asyncio
async def test_task_template_validation(memory_system):
    """Test task template validation."""
    # Verify professional template
    result = await memory_system.semantic.run_query(
        """
        MATCH (t:Concept)
        WHERE t.type = 'task_template'
        AND t.domain = 'professional'
        RETURN t
        """
    )
    templates = [record["t"] async for record in result]
    assert len(templates) >= 1, "Professional task template not found"
    template = templates[0]
    assert template["metadata"]["category"] == "development"
    assert template["metadata"]["default_state"] == "pending"

    # Verify personal template
    result = await memory_system.semantic.run_query(
        """
        MATCH (t:Concept)
        WHERE t.type = 'task_template'
        AND t.domain = 'personal'
        RETURN t
        """
    )
    templates = [record["t"] async for record in result]
    assert len(templates) >= 1, "Personal task template not found"
    template = templates[0]
    assert template["metadata"]["category"] == "organization"
    assert template["metadata"]["default_state"] == "pending"

if __name__ == "__main__":
    pytest.main([__file__])
