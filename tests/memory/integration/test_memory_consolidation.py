"""Integration tests for memory consolidation."""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, List

from nia.core.types.memory_types import (
    Memory, MemoryType, EpisodicMemory, MockMemory,
    Concept, Relationship, DomainContext, BaseDomain, KnowledgeVertical,
    ValidationSchema, CrossDomainSchema
)
from nia.core.types.concept_utils.validation import validate_concept_structure

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_importance_based_consolidation(memory_system, event_loop):
    """Test consolidation based on importance scores."""
    # Create validation schema
    validation = ValidationSchema(
        domain="professional",
        access_domain="professional",
        confidence=0.9,
        source="professional",
        cross_domain=CrossDomainSchema(
            approved=True,
            requested=True,
            source_domain="professional",
            target_domain="professional",
            justification="Test justification"
        )
    )

    # Create domain context
    domain_context = DomainContext(
        primary_domain=BaseDomain.PROFESSIONAL,
        knowledge_vertical=KnowledgeVertical.GENERAL,
        validation=validation
    )

    # Create test memories
    memory1 = MockMemory(
        content="Test memory 1",
        type=MemoryType.EPISODIC,
        importance=0.8,
        knowledge={
            "concepts": [
                {
                    "name": "test_concept_1",
                    "type": "entity",
                    "description": "Test concept 1",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    memory2 = MockMemory(
        content="Test memory 2",
        type=MemoryType.EPISODIC,
        importance=0.9,
        knowledge={
            "concepts": [
                {
                    "name": "test_concept_2",
                    "type": "entity",
                    "description": "Test concept 2",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memories
    await memory_system.episodic.store_memory(memory1)
    await memory_system.episodic.store_memory(memory2)
    
    # Run consolidation
    await memory_system.consolidate_memories()
    
    # Verify consolidated concepts
    concepts = await memory_system.semantic.get_concepts_by_type("entity")
    assert len(concepts) == 2
    
    # Verify validation data is preserved
    for concept in concepts:
        assert concept["validation"]["confidence"] >= 0.8
        assert concept["validation"]["source"] == "professional"
        assert concept["validation"]["cross_domain"]["approved"] is True

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_cross_domain_consolidation(memory_system, event_loop):
    """Test consolidation with cross-domain validation."""
    # Create validation schema
    validation = ValidationSchema(
        domain="professional",
        access_domain="professional",
        confidence=0.9,
        source="professional",
        cross_domain=CrossDomainSchema(
            approved=True,
            requested=True,
            source_domain="professional",
            target_domain="professional",
            justification="Test justification"
        )
    )

    # Create domain context
    domain_context = DomainContext(
        primary_domain=BaseDomain.PROFESSIONAL,
        knowledge_vertical=KnowledgeVertical.GENERAL,
        validation=validation
    )

    # Create test memory
    memory = MockMemory(
        content="Cross domain test",
        type=MemoryType.EPISODIC,
        knowledge={
            "concepts": [
                {
                    "name": "cross_domain_concept",
                    "type": "entity",
                    "description": "Test cross domain concept",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.episodic.store_memory(memory)
    
    # Run consolidation
    await memory_system.consolidate_memories()
    
    # Verify consolidated concept
    concepts = await memory_system.semantic.get_concepts_by_type("entity")
    assert len(concepts) == 1
    
    concept = concepts[0]
    assert concept["validation"]["cross_domain"]["approved"] is True
    assert concept["validation"]["cross_domain"]["source_domain"] == "professional"
    assert concept["validation"]["cross_domain"]["target_domain"] == "professional"

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_memory_consolidation_patterns(memory_system, event_loop):
    """Test consolidation pattern matching."""
    # Create validation schema
    validation = ValidationSchema(
        domain="professional",
        access_domain="professional",
        confidence=0.9,
        source="professional",
        cross_domain=CrossDomainSchema(
            approved=True,
            requested=True,
            source_domain="professional",
            target_domain="professional",
            justification="Test justification"
        )
    )

    # Create domain context
    domain_context = DomainContext(
        primary_domain=BaseDomain.PROFESSIONAL,
        knowledge_vertical=KnowledgeVertical.GENERAL,
        validation=validation
    )

    # Create test memory
    memory = MockMemory(
        content="Pattern test",
        type=MemoryType.EPISODIC,
        knowledge={
            "concepts": [
                {
                    "name": "pattern_concept",
                    "type": "entity",
                    "description": "Test pattern concept",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.episodic.store_memory(memory)
    
    # Run consolidation
    await memory_system.consolidate_memories()
    
    # Verify pattern matching
    concepts = await memory_system.semantic.search_concepts("pattern")
    assert len(concepts) == 1
    assert concepts[0]["validation"]["cross_domain"]["approved"] is True

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_complex_pattern_consolidation(memory_system, event_loop):
    """Test consolidation with complex patterns."""
    # Create validation schema
    validation = ValidationSchema(
        domain="professional",
        access_domain="professional",
        confidence=0.9,
        source="professional",
        cross_domain=CrossDomainSchema(
            approved=True,
            requested=True,
            source_domain="professional",
            target_domain="professional",
            justification="Test justification"
        )
    )

    # Create domain context
    domain_context = DomainContext(
        primary_domain=BaseDomain.PROFESSIONAL,
        knowledge_vertical=KnowledgeVertical.GENERAL,
        validation=validation
    )

    # Create test memory
    memory = MockMemory(
        content="Complex pattern test",
        type=MemoryType.EPISODIC,
        knowledge={
            "concepts": [
                {
                    "name": "complex_pattern",
                    "type": "entity",
                    "description": "Test complex pattern",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.episodic.store_memory(memory)
    
    # Run consolidation
    await memory_system.consolidate_memories()
    
    # Verify complex pattern matching
    concepts = await memory_system.semantic.search_concepts("complex")
    assert len(concepts) == 1
    assert concepts[0]["validation"]["cross_domain"]["approved"] is True

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_basic_concept_storage_and_retrieval(memory_system, event_loop):
    """Test basic concept storage and retrieval with validation."""
    concept = {
        "name": "test_concept",
        "type": "entity",
        "description": "Test concept",
        "validation": {
            "confidence": 0.9,
            "source": "professional",
            "access_domain": "professional",
            "domain": "professional",
            "cross_domain": {
                "approved": True,
                "requested": True,
                "source_domain": "professional",
                "target_domain": "professional"
            }
        }
    }
    
    # Store concept
    await memory_system.semantic.store_concept(
        name=concept["name"],
        type=concept["type"],
        description=concept["description"],
        validation=concept["validation"]
    )
    
    # Retrieve concept
    stored_concept = await memory_system.semantic.get_concept(concept["name"])
    assert stored_concept is not None
    assert stored_concept["validation"]["cross_domain"]["approved"] is True

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_pattern_validation_errors(event_loop):
    """Test validation error handling."""
    # Test invalid concept type
    with pytest.raises(ValueError) as exc_info:
        validate_concept_structure({
            "name": "test",
            "type": "invalid_type",
            "description": "Test"
        })
    assert "Type must be one of: entity, action, property, event, abstract" in str(exc_info.value)
    
    # Test missing required fields
    with pytest.raises(ValueError) as exc_info:
        validate_concept_structure({
            "name": "test"
        })
    assert "Missing required fields" in str(exc_info.value)

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_bidirectional_relationship_consolidation(memory_system, event_loop):
    """Test consolidation of bidirectional relationships."""
    # Create validation schema
    validation = ValidationSchema(
        domain="professional",
        access_domain="professional",
        confidence=0.9,
        source="professional",
        cross_domain=CrossDomainSchema(
            approved=True,
            requested=True,
            source_domain="professional",
            target_domain="professional",
            justification="Test justification"
        )
    )

    # Create domain context
    domain_context = DomainContext(
        primary_domain=BaseDomain.PROFESSIONAL,
        knowledge_vertical=KnowledgeVertical.GENERAL,
        validation=validation
    )

    # Create test memory
    memory = MockMemory(
        content="Relationship test",
        type=MemoryType.EPISODIC,
        knowledge={
            "concepts": [
                {
                    "name": "concept_a",
                    "type": "entity",
                    "description": "Test concept A",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                },
                {
                    "name": "concept_b",
                    "type": "entity",
                    "description": "Test concept B",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ],
            "relationships": [
                {
                    "source": "concept_a",
                    "target": "concept_b",
                    "type": "RELATED_TO",
                    "bidirectional": True,
                    "domain_context": domain_context.dict(),
                    "confidence": 0.9
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.episodic.store_memory(memory)
    
    # Run consolidation
    await memory_system.consolidate_memories()
    
    # Verify bidirectional relationship
    concept_a = await memory_system.semantic.get_concept("concept_a")
    concept_b = await memory_system.semantic.get_concept("concept_b")
    
    assert concept_a is not None, "concept_a not found"
    assert concept_b is not None, "concept_b not found"
    
    # Verify relationships exist
    assert "relationships" in concept_a, "relationships key missing in concept_a"
    assert "relationships" in concept_b, "relationships key missing in concept_b"
    
    # Verify relationships are not None
    assert concept_a["relationships"] is not None, "relationships is None in concept_a"
    assert concept_b["relationships"] is not None, "relationships is None in concept_b"
    
    # Verify bidirectional relationships
    assert any(r["name"] == "concept_b" for r in concept_a["relationships"]), "concept_b not found in concept_a relationships"
    assert any(r["name"] == "concept_a" for r in concept_b["relationships"]), "concept_a not found in concept_b relationships"

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.consolidation
async def test_cross_domain_pattern_consolidation(memory_system, event_loop):
    """Test consolidation with cross-domain pattern matching."""
    # Create validation schema
    validation = ValidationSchema(
        domain="professional",
        access_domain="professional",
        confidence=0.9,
        source="professional",
        cross_domain=CrossDomainSchema(
            approved=True,
            requested=True,
            source_domain="professional",
            target_domain="professional",
            justification="Test justification"
        )
    )

    # Create domain context
    domain_context = DomainContext(
        primary_domain=BaseDomain.PROFESSIONAL,
        knowledge_vertical=KnowledgeVertical.GENERAL,
        validation=validation
    )

    # Create test memory
    memory = MockMemory(
        content="Cross domain pattern test",
        type=MemoryType.EPISODIC,
        knowledge={
            "concepts": [
                {
                    "name": "cross_domain_pattern",
                    "type": "entity",
                    "description": "Test cross domain pattern",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.episodic.store_memory(memory)
    
    # Run consolidation
    await memory_system.consolidate_memories()
    
    # Search with cross-domain filter
    concepts = await memory_system.semantic.query_knowledge({
        "type": "concept",
        "pattern": "pattern",
        "context": {
            "cross_domain.approved": True
        }
    })
    
    # First verify that concepts were found
    assert len(concepts) > 0, "No concepts found matching the cross-domain pattern"
    
    # Verify validation data exists
    assert "validation" in concepts[0], "validation missing in concept"
    assert "cross_domain" in concepts[0]["validation"], "cross_domain missing in validation"
    
    # Then verify the validation data
    assert concepts[0]["validation"]["domain"] == "professional", "incorrect domain"
    assert concepts[0]["validation"]["cross_domain"]["approved"] is True, "cross_domain.approved should be True"
    assert concepts[0]["validation"]["cross_domain"]["source_domain"] == "professional", "incorrect source_domain"
    assert concepts[0]["validation"]["cross_domain"]["target_domain"] == "professional", "incorrect target_domain"
