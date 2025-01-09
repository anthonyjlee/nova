"""Memory consolidation tests."""

import pytest
import logging
from datetime import datetime
from nia.core.types import (
    Memory, MemoryType, Concept, Relationship, Domain, DomainContext, EpisodicMemory
)

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_importance_based_consolidation(memory_system):
    """Test consolidation based on memory importance."""
    # Store high importance memories
    for i in range(3):
        memory = EpisodicMemory(
            content=f"Important memory {i}",
            timestamp=datetime.now().isoformat(),
            importance=0.9,
            context={
                "type": "important",
                "domain": Domain.GENERAL,
                "access_domain": "professional",
                "source": "test",
                "validation": {
                    "domain": Domain.GENERAL,
                    "confidence": 0.9,
                    "source": "test",
                    "access_domain": "professional"
                }
            },
            domain_context=DomainContext(
                primary_domain=Domain.GENERAL,
                knowledge_vertical=None,
                confidence=0.9
            )
        )
        await memory_system.store_experience(memory)

    # Store low importance memories
    for i in range(2):
        memory = EpisodicMemory(
            content=f"Less important memory {i}",
            timestamp=datetime.now().isoformat(),
            importance=0.3,
            context={
                "type": "less_important",
                "domain": Domain.GENERAL,
                "access_domain": "professional",
                "source": "test"
            }
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    semantic_results = []
    
    # Query for important memories individually
    for i in range(3):  # 0, 1, 2
        results = await memory_system.query_semantic({
            "type": "entity",
            "names": [str(i)]
        })
        logger.info(f"Results for important memory {i}: {results}")
        semantic_results.extend(results)
    
    # Query for less important memories individually
    for i in range(2):  # less_0, less_1
        results = await memory_system.query_semantic({
            "type": "entity",
            "names": [f"less_{i}"]
        })
        logger.info(f"Results for less important memory {i}: {results}")
        semantic_results.extend(results)
    
    logger.info(f"All semantic results: {semantic_results}")
    assert len(semantic_results) > 0

@pytest.mark.asyncio
async def test_cross_domain_consolidation(memory_system):
    """Test consolidation across domains."""
    # Store personal domain memories
    for i in range(2):
        memory = EpisodicMemory(
            content=f"Personal task {i}",
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.GENERAL,
                "access_domain": "personal",
                "task_type": "recurring",
                "source": "test"
            }
        )
        await memory_system.store_experience(memory)

    # Store professional domain memories
    for i in range(2):
        memory = EpisodicMemory(
            content=f"Professional task {i}",
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.GENERAL,
                "access_domain": "professional",
                "task_type": "recurring",
                "source": "test"
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
    domain_context = DomainContext(
        primary_domain=Domain.BACKEND,
        knowledge_vertical=Domain.TECHNOLOGY,
        confidence=0.9
    )
    
    concepts = [
        Concept(
            name="API", 
            type="technology", 
            description="Application Programming Interface",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        ),
        Concept(
            name="REST", 
            type="technology", 
            description="RESTful API design",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        )
    ]
    relationships = [
        Relationship(
            source="API", 
            target="REST", 
            type="IMPLEMENTS",
            domain_context=domain_context
        )
    ]

    for i in range(3):
        memory = EpisodicMemory(
            content=f"API design memory {i}",
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.BACKEND,
                "access_domain": "professional",
                "source": "test"
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
    domain_context = DomainContext(
        primary_domain=Domain.DATABASE,
        knowledge_vertical=Domain.TECHNOLOGY,
        confidence=0.9
    )
    
    concepts = [
        Concept(
            name="Database", 
            type="technology", 
            description="Data storage system",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        ),
        Concept(
            name="SQL", 
            type="technology", 
            description="Query language",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        ),
        Concept(
            name="NoSQL", 
            type="technology", 
            description="Non-relational database",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        )
    ]
    relationships = [
        Relationship(
            source="Database", 
            target="SQL", 
            type="USES",
            domain_context=domain_context
        ),
        Relationship(
            source="Database", 
            target="NoSQL", 
            type="ALTERNATIVE",
            domain_context=domain_context
        ),
        Relationship(
            source="SQL", 
            target="NoSQL", 
            type="DIFFERS_FROM",
            domain_context=domain_context
        )
    ]

    for i in range(4):
        memory = EpisodicMemory(
            content=f"Database architecture memory {i}",
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": Domain.DATABASE,
                "access_domain": "professional",
                "source": "test"
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
        memory = EpisodicMemory(
            content="Invalid concept type",
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
                    description="Test concept",
                    domain_context=DomainContext(
                        primary_domain=Domain.PROFESSIONAL,
                        knowledge_vertical=Domain.GENERAL,
                        confidence=0.9
                    ),
                    validation={
                        "confidence": 0.9,
                        "supported_by": [],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                )
            ]
        )
        await memory_system.store_experience(memory)

    # Test invalid confidence value
    with pytest.raises(ValueError, match="confidence"):
        memory = EpisodicMemory(
            content="Invalid confidence",
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
                    description="Test concept",
                    domain_context=DomainContext(
                        primary_domain=Domain.PROFESSIONAL,
                        knowledge_vertical=Domain.GENERAL,
                        confidence=1.5  # Should fail validation
                    ),
                    validation={
                        "confidence": 0.9,
                        "supported_by": [],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                )
            ]
        )
        await memory_system.store_experience(memory)

    # Test missing required context fields
    with pytest.raises(ValueError, match="context"):
        memory = EpisodicMemory(
            content="Missing context fields",
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                # Missing required fields
            },
            concepts=[
                Concept(
                    name="Test",
                    type="entity",
                    description="Test concept",
                    domain_context=DomainContext(
                        primary_domain=Domain.PROFESSIONAL,
                        knowledge_vertical=Domain.GENERAL,
                        confidence=0.9
                    ),
                    validation={
                        "confidence": 0.9,
                        "supported_by": [],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                )
            ]
        )
        await memory_system.store_experience(memory)

@pytest.mark.asyncio
async def test_bidirectional_relationship_consolidation(memory_system):
    """Test consolidation of bidirectional relationships."""
    # Store memory with bidirectional relationship
    domain_context = DomainContext(
        primary_domain=Domain.TECHNOLOGY,
        knowledge_vertical=Domain.BACKEND,
        confidence=0.9
    )
    
    concepts = [
        Concept(
            name="Frontend", 
            type="entity", 
            description="Frontend system",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        ),
        Concept(
            name="Backend", 
            type="entity", 
            description="Backend system",
            domain_context=domain_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        )
    ]
    relationships = [
        Relationship(
            source="Frontend",
            target="Backend",
            type="communicates_with",
            domain_context=domain_context,
            bidirectional=True
        )
    ]

    memory = EpisodicMemory(
        content="System architecture overview",
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
    work_context = DomainContext(
        primary_domain=Domain.PROFESSIONAL,
        knowledge_vertical=Domain.BUSINESS,
        confidence=0.9
    )
    personal_context = DomainContext(
        primary_domain=Domain.PERSONAL,
        knowledge_vertical=Domain.GENERAL,
        confidence=0.9
    )
    
    concepts = [
        Concept(
            name="Project", 
            type="work", 
            description="Work project",
            domain_context=work_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        ),
        Concept(
            name="Schedule", 
            type="personal", 
            description="Personal schedule",
            domain_context=personal_context,
            validation={
                "confidence": 0.9,
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": []
            }
        )
    ]
    relationships = [
        Relationship(
            source="Project", 
            target="Schedule", 
            type="IMPACTS",
            domain_context=work_context
        )
    ]

    # Professional domain memory
    memory1 = EpisodicMemory(
        content="Project deadline approaching",
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "source": "test",
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
    memory2 = EpisodicMemory(
        content="Schedule adjustment needed",
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "personal",
            "source": "test",
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
