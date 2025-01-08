"""Tests for memory system integration."""

import pytest
from datetime import datetime
from nia.memory.types.memory_types import Memory, MemoryType, Domain, Concept
from nia.memory.two_layer import TwoLayerMemorySystem

@pytest.mark.asyncio
async def test_memory_system_integration(memory_system):
    """Test basic memory system integration."""
    # Store memory
    memory_id = await memory_system.store_experience(Memory(
        content="Test memory about retail strategy",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.RETAIL,
            "access_domain": "professional"
        }
    ))
    
    # Verify memory storage
    assert memory_id is not None
    
    # Recall memory
    memories = await memory_system.query_episodic({
        "filter": {"content": "retail strategy"}
    })
    
    assert len(memories) == 1
    assert memories[0].content == "Test memory about retail strategy"
    assert memories[0].importance == 0.8
    assert memories[0].context["domain"] == Domain.RETAIL
    assert memories[0].context["access_domain"] == "professional"

@pytest.mark.asyncio
async def test_concept_integration(memory_system):
    """Test concept integration in memory system."""
    # Create concept memory
    concept = Concept(
        name="CustomerBehavior",
        type="psychology",
        description="Understanding of customer decision-making patterns"
    )
    
    memory_id = await memory_system.store_experience(Memory(
        content="Analysis of customer behavior in retail",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.PSYCHOLOGY,
            "access_domain": "professional"
        },
        concepts=[concept]
    ))
    
    # Verify concept storage
    assert memory_id is not None
    
    # Query concept
    memories = await memory_system.query_episodic({
        "filter": {"concepts": {"name": "CustomerBehavior"}}
    })
    
    assert len(memories) == 1
    assert len(memories[0].concepts) == 1
    assert memories[0].concepts[0].name == "CustomerBehavior"
    assert memories[0].concepts[0].type == "psychology"

@pytest.mark.asyncio
async def test_cross_vertical_consolidation(memory_system):
    """Test consolidation across different knowledge verticals."""
    # Store retail domain memory
    await memory_system.store_experience(Memory(
        content="Customer purchasing patterns in retail",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.RETAIL,
            "access_domain": "professional"
        },
        concepts=[Concept(
            name="PurchasePattern",
            type="retail",
            description="Patterns in customer purchasing behavior"
        )]
    ))
    
    # Store psychology domain memory
    await memory_system.store_experience(Memory(
        content="Psychological factors in purchase decisions",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.8,
        context={
            "domain": Domain.PSYCHOLOGY,
            "access_domain": "professional"
        },
        concepts=[Concept(
            name="DecisionMaking",
            type="psychology",
            description="Psychological aspects of decision making"
        )]
    ))
    
    # Store business domain memory connecting both
    await memory_system.store_experience(Memory(
        content="Impact of psychology on retail strategy",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.BUSINESS,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Analyzing psychological factors in retail",
                "source_domains": ["retail", "psychology"],
                "target_domain": "business"
            }
        },
        concepts=[
            Concept(name="PurchasePattern", type="retail"),
            Concept(name="DecisionMaking", type="psychology")
        ]
    ))
    
    # Trigger consolidation
    await memory_system.consolidate_memories()
    
    # Verify consolidated knowledge across domains
    business_results = await memory_system.semantic.query_knowledge({
        "domain": Domain.BUSINESS,
        "cross_domain.approved": True
    })
    
    assert len(business_results) > 0
    assert any("retail" in str(r) and "psychology" in str(r) for r in business_results)

@pytest.mark.asyncio
async def test_vertical_knowledge_transfer(memory_system):
    """Test knowledge transfer between different verticals."""
    # Store memory with cross-vertical implications
    memory_id = await memory_system.store_experience(Memory(
        content="Applying psychological principles to retail",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        context={
            "domain": Domain.PSYCHOLOGY,
            "access_domain": "professional",
            "cross_domain": {
                "requested": True,
                "approved": True,
                "justification": "Knowledge transfer from psychology to retail",
                "source_domain": Domain.PSYCHOLOGY,
                "target_domain": Domain.RETAIL
            }
        }
    ))
    
    assert memory_id is not None
    
    # Query with domain filter
    memories = await memory_system.query_episodic({
        "filter": {
            "context": {
                "domain": Domain.PSYCHOLOGY,
                "cross_domain.target_domain": Domain.RETAIL
            }
        }
    })
    
    assert len(memories) == 1
    assert memories[0].context["cross_domain"]["approved"] == True

@pytest.mark.asyncio
async def test_memory_lifecycle(memory_system):
    """Test complete memory lifecycle with domain context."""
    # Store memory
    memory_id = await memory_system.store_experience(Memory(
        content="Research on retail customer behavior",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.7,
        context={
            "domain": Domain.RETAIL,
            "access_domain": "professional",
            "research_phase": "initial"
        }
    ))
    
    # Verify initial storage
    assert memory_id is not None
    
    # Update memory (through consolidation)
    await memory_system.consolidate_memories()
    
    # Verify consolidated state
    memories = await memory_system.query_episodic({
        "filter": {"id": memory_id}
    })
    
    assert len(memories) == 1
    assert memories[0].consolidated == True
    
    # Archive memory
    await memory_system.archive_memory(memory_id)
    
    # Verify archived state
    memories = await memory_system.query_episodic({
        "filter": {
            "id": memory_id,
            "include_archived": True
        }
    })
    
    assert len(memories) == 1
    assert memories[0].archived == True
