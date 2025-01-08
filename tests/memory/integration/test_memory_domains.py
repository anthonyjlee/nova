"""Memory domain separation tests."""

import pytest
from datetime import datetime
from nia.memory.types.memory_types import Memory, MemoryType, Domain, Concept

@pytest.mark.asyncio
async def test_vertical_domain_separation(memory_system):
    """Test separation between knowledge verticals."""
    # Store memory in retail domain
    retail_memory = Memory(
        content="Customer segmentation analysis",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.RETAIL,
            "access_domain": "professional"
        }
    )
    await memory_system.store_experience(retail_memory)

    # Store memory in psychology domain
    psych_memory = Memory(
        content="Consumer behavior patterns",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.PSYCHOLOGY,
            "access_domain": "professional"
        }
    )
    await memory_system.store_experience(psych_memory)

    # Query retail domain
    retail_results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "domain": Domain.RETAIL,
                "access_domain": "professional"
            }
        }
    })
    assert len(retail_results) == 1
    assert retail_results[0].content == "Customer segmentation analysis"

    # Query psychology domain
    psych_results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "domain": Domain.PSYCHOLOGY,
                "access_domain": "professional"
            }
        }
    })
    assert len(psych_results) == 1
    assert psych_results[0].content == "Consumer behavior patterns"

@pytest.mark.asyncio
async def test_cross_vertical_knowledge_transfer(memory_system):
    """Test knowledge transfer between verticals."""
    # Store memory with cross-vertical implications
    memory = Memory(
        content="Applying psychological principles to retail strategy",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.BUSINESS,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Integrating psychology insights into retail",
                "source_domains": [Domain.PSYCHOLOGY, Domain.RETAIL],
                "target_domain": Domain.BUSINESS
            }
        },
        concepts=[
            Concept(name="ConsumerPsychology", type="psychology"),
            Concept(name="RetailStrategy", type="business")
        ]
    )
    memory_id = await memory_system.store_experience(memory)
    assert memory_id is not None

    # Query with cross-domain filter
    results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "cross_domain.source_domains": Domain.PSYCHOLOGY
            }
        }
    })
    assert len(results) == 1
    assert Domain.PSYCHOLOGY in str(results[0].context["cross_domain"]["source_domains"])

@pytest.mark.asyncio
async def test_domain_validation(memory_system):
    """Test domain validation during memory operations."""
    # Test valid domain combination
    valid_memory = Memory(
        content="Valid domain test",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.RETAIL,
            "access_domain": "professional"
        }
    )
    memory_id = await memory_system.store_experience(valid_memory)
    assert memory_id is not None

    # Test invalid domain
    invalid_memory = Memory(
        content="Invalid domain test",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": "invalid_domain",
            "access_domain": "professional"
        }
    )
    with pytest.raises(ValueError):
        await memory_system.store_experience(invalid_memory)

    # Test missing domain
    missing_domain = Memory(
        content="Missing domain test",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={}
    )
    # Should default to general domain
    memory_id = await memory_system.store_experience(missing_domain)
    assert memory_id is not None

    # Verify defaulted domain
    result = await memory_system.get_memory(memory_id)
    assert result.context.get("domain") == Domain.GENERAL

@pytest.mark.asyncio
async def test_interdisciplinary_knowledge(memory_system):
    """Test handling of interdisciplinary knowledge."""
    # Store memories in different verticals
    domains = [Domain.PSYCHOLOGY, Domain.BUSINESS, Domain.TECHNOLOGY]
    concepts = []
    
    for domain in domains:
        memory = Memory(
            content=f"Knowledge in {domain}",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.8,
            context={
                "domain": domain,
                "access_domain": "professional"
            },
            concepts=[Concept(
                name=f"{domain}Concept",
                type=domain.lower(),
                description=f"Core concept in {domain}"
            )]
        )
        await memory_system.store_experience(memory)
        concepts.append(f"{domain}Concept")

    # Store interdisciplinary insight
    interdisciplinary = Memory(
        content="Interdisciplinary analysis",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.GENERAL,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Interdisciplinary research",
                "source_domains": domains,
                "target_domain": Domain.GENERAL
            }
        },
        concepts=[Concept(name=c, type="interdisciplinary") for c in concepts]
    )
    await memory_system.store_experience(interdisciplinary)

    # Verify interdisciplinary connections
    results = await memory_system.query_episodic({
        "filter": {
            "context": {
                "cross_domain.source_domains": {"$contains": domains}
            }
        }
    })
    assert len(results) == 1
    assert all(d in str(results[0].context["cross_domain"]["source_domains"]) for d in domains)
