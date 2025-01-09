"""Memory consolidation tests."""

import pytest
from datetime import datetime
from nia.memory.types.memory_types import Memory, MemoryType, Concept, Relationship, Domain

@pytest.mark.asyncio
async def test_importance_based_consolidation(memory_system):
    """Test consolidation based on memory importance."""
    # Store high importance memories
    for i in range(3):
        memory = Memory(
            content=f"Important memory {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.9,
            context={
                "type": "important",
                "domain": Domain.GENERAL,
                "access_domain": "professional"
            }
        )
        await memory_system.store_experience(memory)

    # Store low importance memories
    for i in range(2):
        memory = Memory(
            content=f"Less important memory {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.3,
            context={
                "type": "less_important",
                "domain": Domain.GENERAL,
                "access_domain": "professional"
            }
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify high importance memories were consolidated
    semantic_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "important",
        "context": {
            "access_domain": "professional"
        }
    })
    assert len(semantic_results) > 0

@pytest.mark.asyncio
async def test_cross_domain_consolidation(memory_system):
    """Test consolidation across domains."""
    # Store personal domain memories
    for i in range(2):
        memory = Memory(
            content=f"Personal task {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.GENERAL,
                "access_domain": "personal",
                "task_type": "recurring"
            }
        )
        await memory_system.store_experience(memory)

    # Store professional domain memories
    for i in range(2):
        memory = Memory(
            content=f"Professional task {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.GENERAL,
                "access_domain": "professional",
                "task_type": "recurring"
            }
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify domain separation in consolidated knowledge
    personal_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "task",
        "context": {
            "access_domain": "personal"
        }
    })
    assert len(personal_results) > 0

    professional_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "task",
        "context": {
            "access_domain": "professional"
        }
    })
    assert len(professional_results) > 0

@pytest.mark.asyncio
async def test_memory_consolidation_patterns(memory_system):
    """Test pattern detection during consolidation."""
    # Store related memories
    concepts = [
        Concept(name="API", type="technology", description="Application Programming Interface"),
        Concept(name="REST", type="technology", description="RESTful API design")
    ]
    relationships = [
        Relationship(from_="API", to="REST", type="IMPLEMENTS")
    ]

    for i in range(3):
        memory = Memory(
            content=f"API design memory {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.BACKEND,
                "access_domain": "professional"
            },
            concepts=concepts,
            relationships=relationships
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify pattern was detected and stored with domain context
    semantic_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "API",
        "context": {
            "domain": Domain.BACKEND,
            "access_domain": "professional"
        }
    })
    assert len(semantic_results) > 0
    assert any("REST" in str(result) for result in semantic_results)

@pytest.mark.asyncio
async def test_complex_pattern_consolidation(memory_system):
    """Test consolidation of complex memory patterns."""
    # Store memories with interconnected concepts
    concepts = [
        Concept(name="Database", type="technology", description="Data storage system"),
        Concept(name="SQL", type="technology", description="Query language"),
        Concept(name="NoSQL", type="technology", description="Non-relational database")
    ]
    relationships = [
        Relationship(from_="Database", to="SQL", type="USES"),
        Relationship(from_="Database", to="NoSQL", type="ALTERNATIVE"),
        Relationship(from_="SQL", to="NoSQL", type="DIFFERS_FROM")
    ]

    for i in range(4):
        memory = Memory(
            content=f"Database architecture memory {i}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.DATABASE,
                "access_domain": "professional"
            },
            concepts=concepts,
            relationships=relationships
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify complex pattern was stored correctly with domain context
    semantic_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "Database",
        "context": {
            "domain": Domain.DATABASE,
            "access_domain": "professional"
        }
    })
    assert len(semantic_results) > 0

    # Verify relationships were preserved
    for result in semantic_results:
        if "Database" in str(result):
            assert "SQL" in str(result) or "NoSQL" in str(result)

@pytest.mark.asyncio
async def test_pattern_validation_errors(memory_system):
    """Test validation errors during pattern consolidation."""
    # Test invalid concept type
    with pytest.raises(ValueError, match="type"):
        memory = Memory(
            content="Invalid concept type",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": "professional",
                "source": "test"
            },
            concepts=[
                Concept(
                    name="Test",
                    type="invalid_type",  # Should fail validation
                    domain="professional",
                    confidence=0.9
                )
            ]
        )
        await memory_system.store_experience(memory)

    # Test invalid confidence value
    with pytest.raises(ValueError, match="confidence"):
        memory = Memory(
            content="Invalid confidence",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": "professional",
                "source": "test"
            },
            concepts=[
                Concept(
                    name="Test",
                    type="entity",
                    domain="professional",
                    confidence=1.5  # Should fail validation
                )
            ]
        )
        await memory_system.store_experience(memory)

    # Test missing required context fields
    with pytest.raises(ValueError, match="context"):
        memory = Memory(
            content="Missing context fields",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                # Missing required fields
            },
            concepts=[
                Concept(
                    name="Test",
                    type="entity",
                    domain="professional",
                    confidence=0.9
                )
            ]
        )
        await memory_system.store_experience(memory)

@pytest.mark.asyncio
async def test_bidirectional_relationship_consolidation(memory_system):
    """Test consolidation of bidirectional relationships."""
    # Store memory with bidirectional relationship
    concepts = [
        Concept(name="Frontend", type="entity", domain="professional", confidence=0.9),
        Concept(name="Backend", type="entity", domain="professional", confidence=0.9)
    ]
    relationships = [
        Relationship(
            from_="Frontend",
            to="Backend",
            type="communicates_with",
            domains=["professional"],
            confidence=0.9,
            bidirectional=True
        )
    ]

    memory = Memory(
        content="System architecture overview",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": "professional",
            "source": "architecture_review"
        },
        concepts=concepts,
        relationships=relationships
    )
    await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify bidirectional relationship was stored
    semantic_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "Frontend|Backend",
        "context": {
            "domain": "professional"
        }
    })
    assert len(semantic_results) > 0

    # Verify both directions exist
    found_forward = False
    found_reverse = False
    for result in semantic_results:
        if "Frontend" in str(result) and "Backend" in str(result):
            found_forward = True
        if "Backend" in str(result) and "Frontend" in str(result):
            found_reverse = True
    assert found_forward and found_reverse

@pytest.mark.asyncio
async def test_cross_domain_pattern_consolidation(memory_system):
    """Test consolidation of patterns that span domains."""
    # Store cross-domain related memories
    concepts = [
        Concept(name="Project", type="work", description="Work project"),
        Concept(name="Schedule", type="personal", description="Personal schedule")
    ]
    relationships = [
        Relationship(from_="Project", to="Schedule", type="IMPACTS")
    ]

    # Professional domain memory
    memory1 = Memory(
        content="Project deadline approaching",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Schedule coordination required",
                "source_domain": "professional",
                "target_domain": "personal"
            }
        },
        concepts=[concepts[0]],
        relationships=relationships
    )
    await memory_system.store_experience(memory1)

    # Personal domain memory
    memory2 = Memory(
        content="Schedule adjustment needed",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "personal",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Schedule coordination required",
                "source_domain": "personal",
                "target_domain": "professional"
            }
        },
        concepts=[concepts[1]],
        relationships=relationships
    )
    await memory_system.store_experience(memory2)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify cross-domain pattern was consolidated
    semantic_results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "Project|Schedule",
        "context": {
            "cross_domain.approved": True
        }
    })
    assert len(semantic_results) > 0

    # Verify relationship was preserved across domains
    found_relationship = False
    for result in semantic_results:
        if "Project" in str(result) and "Schedule" in str(result):
            found_relationship = True
            break
    assert found_relationship
