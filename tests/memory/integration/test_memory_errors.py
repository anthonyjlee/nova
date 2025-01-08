"""Memory error handling tests."""

import pytest
from datetime import datetime
from nia.memory.types.memory_types import Memory, MemoryType, Domain

@pytest.mark.asyncio
async def test_memory_error_handling(memory_system):
    """Test error handling during memory operations."""
    # Test missing required fields
    invalid_memory = Memory(
        content="",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={},
        concepts=[],
        relationships=[],
        participants=[]
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_memory)

    # Test invalid memory type
    invalid_type_memory = Memory(
        content="Test memory",
        type="invalid_type",
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        },
        concepts=[],
        relationships=[],
        participants=[]
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_type_memory)

    # Test invalid importance value
    invalid_importance = Memory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=2.0,  # Should be between 0 and 1
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        },
        concepts=[],
        relationships=[],
        participants=[]
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_importance)

@pytest.mark.asyncio
async def test_domain_error_handling(memory_system):
    """Test error handling for domain-related operations."""
    # Test invalid access domain
    invalid_access_domain = Memory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "invalid_domain"
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_access_domain)

    # Test invalid cross-domain configuration
    invalid_cross_domain = Memory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "source_domain": "invalid_source",  # Invalid source domain
                "target_domain": "professional"
            }
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_cross_domain)

    # Test missing cross-domain approval
    unapproved_cross_domain = Memory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": False,  # Not approved
                "source_domain": "personal",
                "target_domain": "professional"
            }
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(unapproved_cross_domain)

@pytest.mark.asyncio
async def test_invalid_memory_operations(memory_system):
    """Test handling of invalid memory operations."""
    # Test querying with invalid filter
    with pytest.raises(ValueError):
        await memory_system.query_episodic({
            "invalid_filter": "value",
            "filter": {"invalid": True}
        })

    # Test querying with invalid domain filter
    with pytest.raises(ValueError):
        await memory_system.query_episodic({
            "filter": {
                "context": {
                    "access_domain": "invalid_domain"
                }
            }
        })

    # Test getting non-existent memory
    result = await memory_system.get_memory("non_existent_id")
    assert result is None

@pytest.mark.asyncio
async def test_cross_domain_error_handling(memory_system):
    """Test error handling for cross-domain operations."""
    # Test invalid cross-domain query
    with pytest.raises(ValueError):
        await memory_system.query_episodic({
            "filter": {
                "context": {
                    "cross_domain": {
                        "source_domain": "invalid_domain"
                    }
                }
            }
        })

    # Test cross-domain operation without justification
    invalid_cross_domain = Memory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "source_domain": "professional",
                "target_domain": "personal"
                # Missing justification
            }
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_cross_domain)

@pytest.mark.asyncio
async def test_memory_edge_cases(memory_system):
    """Test memory system edge cases."""
    # Test empty content
    empty_content = Memory(
        content="",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(empty_content)

    # Test very long content
    long_content = Memory(
        content="x" * 1000000,  # Very long string
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional"
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(long_content)

    # Test special characters in content with cross-domain context
    special_chars = Memory(
        content="Test with special chars: !@#$%^&*()",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Test special characters",
                "source_domain": "professional",
                "target_domain": "personal"
            }
        }
    )
    memory_id = await memory_system.store_experience(special_chars)
    assert memory_id is not None

    # Verify special characters and cross-domain context were preserved
    result = await memory_system.get_memory(memory_id)
    assert result.content == "Test with special chars: !@#$%^&*()"
    assert result.context["cross_domain"]["approved"] == True
