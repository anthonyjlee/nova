"""Tests for memory consolidation system."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import Field, ConfigDict

from nia.memory.consolidation import (
    ConsolidationPattern,
    TinyTroupePattern,
    ConsolidationManager
)
from nia.memory.types.memory_types import Memory, Concept, Relationship, MemoryType

class MockAgent:
    """Mock TinyTroupe agent for testing."""
    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.type = agent_type
        self.skills = ["test_skill"]
        self.state = "active"

class MockTask:
    """Mock TinyTroupe task for testing."""
    def __init__(self, name: str):
        self.name = name
        self.category = "test"
        self.description = "Test task"
        self.status = "pending"
        self.priority = "high"

class MockInteraction:
    """Mock TinyTroupe interaction for testing."""
    def __init__(self, source: str, target: str):
        self.source_agent = source
        self.target_agent = target
        self.type = "COLLABORATES_WITH"
        self.timestamp = datetime.now().isoformat()
        self.context = "test context"

class MockObservation:
    """Mock TinyTroupe observation for testing."""
    def __init__(self, agent: str, capability: str):
        self.type = "capability"
        self.agent = agent
        self.capability = capability
        self.confidence = 0.9

class MockMemory(dict):
    """Mock memory for testing."""
    def __init__(self, content: str, importance: float = 0.5):
        super().__init__()
        self.update({
            "content": content,
            "type": MemoryType.EPISODIC,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "agents": [],
                "tasks": [],
                "interactions": [],
                "observations": []
            },
            "importance": importance,
            "consolidated": False
        })
        
    def add_agent(self, agent: MockAgent):
        """Add agent to metadata."""
        self["metadata"]["agents"].append({
            "name": agent.name,
            "type": agent.type,
            "skills": agent.skills,
            "state": agent.state
        })
        
    def add_task(self, task: MockTask):
        """Add task to metadata."""
        self["metadata"]["tasks"].append({
            "name": task.name,
            "category": task.category,
            "description": task.description,
            "status": task.status,
            "priority": task.priority
        })
        
    def add_interaction(self, interaction: MockInteraction):
        """Add interaction to metadata."""
        self["metadata"]["interactions"].append({
            "source_agent": interaction.source_agent,
            "target_agent": interaction.target_agent,
            "type": interaction.type,
            "timestamp": interaction.timestamp,
            "context": interaction.context
        })
        
    def add_observation(self, observation: MockObservation):
        """Add observation to metadata."""
        self["metadata"]["observations"].append({
            "type": observation.type,
            "agent": observation.agent,
            "capability": observation.capability,
            "confidence": observation.confidence
        })

@pytest.fixture
def mock_episodic_layer():
    """Mock episodic layer for testing."""
    class MockEpisodicLayer:
        def __init__(self):
            self.memories = []
            
        async def get_consolidation_candidates(self) -> List[Dict]:
            return self.memories
            
    return MockEpisodicLayer()

@pytest.fixture
def mock_semantic_layer():
    """Mock semantic layer for testing."""
    class MockSemanticLayer:
        def __init__(self):
            self.stored_knowledge = {
                "concepts": [],
                "relationships": [],
                "beliefs": []
            }
            
        async def store_knowledge(self, knowledge: Dict):
            self.stored_knowledge = knowledge
            
    return MockSemanticLayer()

@pytest.mark.asyncio
async def test_tinytroupe_pattern():
    """Test TinyTroupe-specific knowledge extraction."""
    pattern = TinyTroupePattern()
    
    # Create test memory with TinyTroupe data
    memory = MockMemory("Test memory")
    
    # Add agents
    memory.add_agent(MockAgent("Agent1", "DialogueAgent"))
    memory.add_agent(MockAgent("Agent2", "TaskAgent"))
    
    # Add tasks
    memory.add_task(MockTask("Task1"))
    
    # Add interactions
    memory.add_interaction(MockInteraction("Agent1", "Agent2"))
    
    # Add observations
    memory.add_observation(MockObservation("Agent1", "conversation"))
    memory.add_observation(MockObservation("Agent2", "planning"))
    
    # Extract knowledge
    knowledge = await pattern.extract_knowledge([memory])
    
    # Verify extracted concepts
    assert len(knowledge["concepts"]) == 3  # 2 agents + 1 task
    assert any(c["name"] == "Agent1" and c["type"] == "Agent" for c in knowledge["concepts"])
    assert any(c["name"] == "Agent2" and c["type"] == "Agent" for c in knowledge["concepts"])
    assert any(c["name"] == "Task1" and c["type"] == "Task" for c in knowledge["concepts"])
    
    # Verify extracted relationships
    assert len(knowledge["relationships"]) == 1
    assert knowledge["relationships"][0]["from"] == "Agent1"
    assert knowledge["relationships"][0]["to"] == "Agent2"
    assert knowledge["relationships"][0]["type"] == "COLLABORATES_WITH"
    
    # Verify extracted beliefs
    assert len(knowledge["beliefs"]) == 2
    assert any(b["subject"] == "Agent1" and b["object"] == "conversation" for b in knowledge["beliefs"])
    assert any(b["subject"] == "Agent2" and b["object"] == "planning" for b in knowledge["beliefs"])

@pytest.mark.asyncio
async def test_consolidation_triggers(mock_episodic_layer, mock_semantic_layer):
    """Test consolidation trigger conditions."""
    manager = ConsolidationManager(mock_episodic_layer, mock_semantic_layer)
    
    # Test time-based trigger
    manager.last_consolidation = datetime.now() - timedelta(minutes=10)
    assert await manager.should_consolidate()
    
    # Test importance-based trigger
    manager.last_consolidation = datetime.now()  # Reset time
    memory = MockMemory("Important memory", importance=0.9)
    mock_episodic_layer.memories = [memory]
    assert await manager.should_consolidate()
    
    # Test volume-based trigger
    mock_episodic_layer.memories = [MockMemory(f"Memory {i}") for i in range(15)]
    assert await manager.should_consolidate()

@pytest.mark.asyncio
async def test_knowledge_deduplication(mock_episodic_layer, mock_semantic_layer):
    """Test deduplication of extracted knowledge."""
    manager = ConsolidationManager(mock_episodic_layer, mock_semantic_layer)
    
    # Create test memories with overlapping knowledge
    memory1 = MockMemory("Memory 1")
    memory1.add_agent(MockAgent("Agent1", "DialogueAgent"))
    memory1.add_observation(MockObservation("Agent1", "conversation"))
    
    memory2 = MockMemory("Memory 2")
    memory2.add_agent(MockAgent("Agent1", "DialogueAgent"))  # Same agent
    memory2.add_observation(MockObservation("Agent1", "conversation"))  # Same observation
    
    # Extract knowledge
    knowledge = await manager.extract_knowledge([memory1, memory2])
    
    # Verify deduplication
    assert len(knowledge["concepts"]) == 1  # Only one agent concept
    assert len(knowledge["beliefs"]) == 1  # Only one belief about the agent's capability

@pytest.mark.asyncio
async def test_consolidation_metadata():
    """Test consolidated field handling in metadata."""
    manager = ConsolidationManager(None, None)
    
    # Create test memory
    memory = MockMemory("Test memory")
    assert not memory["consolidated"]  # Should start as False
    
    # Simulate consolidation
    memory["consolidated"] = True
    assert memory["consolidated"]  # Should be updated to True
    
    # Verify metadata structure
    assert "consolidated" in memory
    assert isinstance(memory["consolidated"], bool)

@pytest.mark.asyncio
async def test_pattern_management():
    """Test adding and removing consolidation patterns."""
    manager = ConsolidationManager(None, None)
    
    # Create custom pattern
    class CustomPattern(ConsolidationPattern):
        def __init__(self):
            super().__init__("custom", threshold=0.5)
            
        async def extract_knowledge(self, memories: List[Memory]) -> Dict:
            return {"concepts": [], "relationships": [], "beliefs": []}
    
    # Add custom pattern
    custom_pattern = CustomPattern()
    manager.add_pattern(custom_pattern)
    assert len(manager.patterns) == 2  # TinyTroupePattern + CustomPattern
    assert any(p.name == "custom" for p in manager.patterns)
    
    # Remove pattern
    manager.remove_pattern("custom")
    assert len(manager.patterns) == 1
    assert all(p.name != "custom" for p in manager.patterns)

if __name__ == "__main__":
    pytest.main([__file__])
