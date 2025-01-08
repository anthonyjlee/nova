"""Tests for TinyTroupe memory system integration."""

import pytest
from nia.agents.tinytroupe_agent import TinyTroupeAgent
from nia.memory.two_layer import TwoLayerMemorySystem

@pytest.fixture
def memory_system(mock_vector_store, mock_neo4j_store):
    """Create memory system for testing."""
    return TwoLayerMemorySystem(mock_neo4j_store, mock_vector_store)

@pytest.mark.asyncio
async def test_memory_tinytroupe_integration(memory_system):
    """Test memory system integration with TinyTroupe."""
    agent = TinyTroupeAgent(
        name="memory_test",
        memory_system=memory_system
    )
    
    # Store memory
    memory_id = await agent.store_memory(
        content="Test memory",
        importance=0.8,
        context={"type": "test"}
    )
    
    # Verify memory storage
    assert memory_id is not None
    
    # Verify TinyTroupe state update
    assert "memory" in agent.memory_references
    
    # Recall memory
    memories = await agent.recall_memories(
        query={"filter": {"content": "Test memory"}}
    )
    
    assert len(memories) == 1
    assert memories[0].content == "Test memory"
    assert memories[0].importance == 0.8

@pytest.mark.asyncio
async def test_emotion_concept_integration(memory_system):
    """Test emotion concept integration."""
    agent = TinyTroupeAgent(
        name="emotion_test",
        memory_system=memory_system
    )
    
    # Process emotion concept
    await agent.process({
        "content": "Test content",
        "concepts": [{
            "name": "Joy",
            "type": "emotion",
            "description": "Feeling happy",
            "related": []
        }]
    })
    
    # Verify emotion update
    assert "Joy" in agent.emotions
    assert agent.emotions["Joy"] == "Feeling happy"

@pytest.mark.asyncio
async def test_reflection_integration(memory_system):
    """Test reflection across both systems."""
    agent = TinyTroupeAgent(
        name="reflection_test",
        memory_system=memory_system
    )
    
    # Create test memories
    for i in range(3):
        await agent.store_memory(
            content=f"Memory {i}",
            importance=0.8,
            context={"type": "test_memory"}
        )
    
    # Trigger reflection
    await agent.reflect()
    
    # Verify memory reflection
    memories = await agent.recall_memories(
        query={"filter": {"content.type": "reflection"}}
    )
    assert len(memories) == 1
    
    # Verify TinyTroupe state updates
    assert "interest" in agent.emotions
    assert agent.emotions["interest"] == "high"
    assert any("Learn more about" in desire for desire in agent.desires)
