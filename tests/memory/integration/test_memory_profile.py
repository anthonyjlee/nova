"""Memory profile integration tests."""

import pytest
from datetime import datetime
from nia.memory.types.memory_types import (
    Memory, MemoryType, Domain, MockMemory,
    ValidationSchema, CrossDomainSchema, DomainContext,
    BaseDomain, KnowledgeVertical
)

@pytest.mark.asyncio
async def test_profile_adaptations(memory_system):
    """Test storing and retrieving profile adaptations."""
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
        content="Test with profile adaptations",
        type=MemoryType.EPISODIC,
        importance=0.8,
        context={
            "profile": {
                "user_profile_id": "test_user",
                "adaptations": {
                    "communication_style": "technical",
                    "detail_level": "high",
                    "learning_style": "visual"
                }
            }
        },
        validation=validation,
        domain_context=domain_context
    )
    memory_id = await memory_system.store_experience(memory)
    assert memory_id is not None

    # Verify adaptations were stored
    result = await memory_system.get_memory(memory_id)
    assert result.context["profile"]["adaptations"]["communication_style"] == "technical"

@pytest.mark.asyncio
async def test_consolidate_profile_patterns(memory_system):
    """Test consolidation of profile-based patterns."""
    # Store multiple memories with similar adaptations
    for i in range(3):
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
            content=f"Test memory {i}",
            type=MemoryType.EPISODIC,
            importance=0.8,
            context={
                "profile": {
                    "user_profile_id": "test_user",
                    "adaptations": {
                        "communication_style": "technical",
                        "detail_level": "high"
                    }
                }
            },
            validation=validation,
            domain_context=domain_context
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify pattern was detected and stored
    semantic_results = await memory_system.query_semantic({
        "type": "profile_pattern",
        "context": {
            "user_profile_id": "test_user"
        }
    })
    assert len(semantic_results) > 0
    assert any("communication_style" in str(result) for result in semantic_results)

@pytest.mark.asyncio
async def test_domain_specific_confidence(memory_system):
    """Test building domain-specific confidence scores."""
    # Store memories with successful adaptations in different domains
    domains = [Domain.RETAIL, Domain.PSYCHOLOGY]
    for domain in domains:
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
            content=f"Test in {domain}",
            type=MemoryType.EPISODIC,
            importance=0.9,
            context={
                "profile": {
                    "user_profile_id": "test_user",
                    "adaptations": {
                        "communication_style": "technical",
                        "success_rate": 0.9
                    }
                }
            },
            validation=validation,
            domain_context=domain_context
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify domain-specific confidence scores
    for domain in domains:
        results = await memory_system.query_semantic({
            "type": "domain_confidence",
            "context": {
                "domain": domain,
                "user_profile_id": "test_user"
            }
        })
        assert len(results) > 0
        assert any(float(result.get("confidence", 0)) > 0.8 for result in results)

@pytest.mark.asyncio
async def test_track_user_preferences(memory_system):
    """Test tracking and evolving user preferences."""
    # Store memories showing preference evolution
    preferences = [
        {"detail_level": "low", "timestamp": "2025-01-01T00:00:00"},
        {"detail_level": "medium", "timestamp": "2025-01-05T00:00:00"},
        {"detail_level": "high", "timestamp": "2025-01-09T00:00:00"}
    ]

    for pref in preferences:
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
            content="Test preference tracking",
            type=MemoryType.EPISODIC,
            importance=0.8,
            context={
                "profile": {
                    "user_profile_id": "test_user",
                    "preferences": {
                        "detail_level": pref["detail_level"]
                    }
                }
            },
            validation=validation,
            domain_context=domain_context,
            timestamp=pref["timestamp"]
        )
        await memory_system.store_experience(memory)

    # Trigger consolidation
    await memory_system.consolidate_memories()

    # Verify preference evolution was tracked
    results = await memory_system.query_semantic({
        "type": "preference_evolution",
        "context": {
            "user_profile_id": "test_user"
        }
    })
    assert len(results) > 0
    
    # Verify most recent preference
    latest_pref = None
    latest_timestamp = None
    for result in results:
        timestamp = result.get("timestamp")
        if not latest_timestamp or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_pref = result.get("preferences", {}).get("detail_level")
    
    assert latest_pref == "high"

@pytest.mark.asyncio
async def test_cross_domain_profile_adaptations(memory_system):
    """Test profile adaptations across domains."""
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
            target_domain="personal",
            justification="Profile adaptation testing"
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
        content="Cross-domain adaptation test",
        type=MemoryType.EPISODIC,
        importance=0.9,
        context={
            "profile": {
                "user_profile_id": "test_user",
                "adaptations": {
                    "communication_style": "technical",
                    "detail_level": "high",
                    "cross_domain_confidence": 0.85
                }
            }
        },
        validation=validation,
        domain_context=domain_context
    )
    memory_id = await memory_system.store_experience(memory)

    # Verify cross-domain adaptations
    result = await memory_system.get_memory(memory_id)
    assert result.context["profile"]["adaptations"]["cross_domain_confidence"] > 0.8
    assert result.context["cross_domain"]["approved"] == True
