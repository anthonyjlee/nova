"""Tests for the two-layer memory system."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List
import uuid
import json

from nia.memory.two_layer import TwoLayerMemorySystem, EpisodicLayer, SemanticLayer
from nia.memory.consolidation import ConsolidationManager
from nia.memory.memory_types import (
    Memory, EpisodicMemory, SemanticMemory, 
    Concept, Relationship, Belief,
    MemoryType, JSONSerializable
)
from nia.memory.json_utils import validate_json_structure
from nia.memory.concept_utils import validate_concept_structure

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    class MockVectorStore:
        def __init__(self):
            self.vectors = {}
            
        async def store_vector(self, content: Dict, metadata: Dict = None) -> str:
            vector_id = str(uuid.uuid4())
            self.vectors[vector_id] = {
                "content": content,
                "metadata": metadata or {}
            }
            return vector_id
            
        async def get_vector(self, vector_id: str) -> Dict:
            return self.vectors.get(vector_id, {}).get("content")
            
        async def search_vectors(self, content: str, filter: Dict = None) -> List[Dict]:
            # Simple mock search - return all vectors matching filter
            results = []
            for vector in self.vectors.values():
                if filter:
                    if all(vector["metadata"].get(k) == v for k, v in filter.items()):
                        results.append(vector["content"])
                else:
                    results.append(vector["content"])
            return results
            
        async def update_metadata(self, vector_id: str, metadata: Dict):
            if vector_id in self.vectors:
                self.vectors[vector_id]["metadata"].update(metadata)
                
    return MockVectorStore()

@pytest.fixture
def mock_neo4j_store():
    """Mock Neo4j store for testing."""
    class MockNeo4jStore:
        def __init__(self):
            self.nodes = {}
            self.relationships = []
            self.beliefs = []
            
        async def create_concept_node(self, label: str, properties: Dict):
            node_id = str(uuid.uuid4())
            self.nodes[node_id] = {
                "label": label,
                "properties": properties
            }
            return node_id
            
        async def create_relationship(self, start_node: str, end_node: str, type: str, properties: Dict = None):
            self.relationships.append({
                "from": start_node,
                "to": end_node,
                "type": type,
                "properties": properties or {}
            })
            
        async def create_belief(self, subject: str, predicate: str, object: str, confidence: float = 1.0):
            self.beliefs.append({
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "confidence": confidence
            })
            
        async def run_query(self, query: str) -> List[Dict]:
            # Mock query execution - return all nodes for now
            return [{"n": node} for node in self.nodes.values()]
            
    return MockNeo4jStore()

@pytest.fixture
def memory_system(mock_vector_store, mock_neo4j_store):
    """Create memory system with mock stores."""
    system = TwoLayerMemorySystem(mock_neo4j_store, mock_vector_store)
    system.consolidation_manager = ConsolidationManager(system.episodic, system.semantic)
    return system

@pytest.mark.asyncio
async def test_json_serialization():
    """Test JSON serialization of memory objects."""
    # Create test memory
    memory = EpisodicMemory(
        content="Test memory",
        concepts=[
            Concept(
                name="Test Concept",
                category="Test"
            )
        ]
    )
    
    # Serialize to JSON
    json_str = memory.json()
    
    # Deserialize and verify
    data = json.loads(json_str)
    assert data["content"] == "Test memory"
    assert data["type"] == MemoryType.EPISODIC
    assert isinstance(data["timestamp"], str)  # Should be ISO format
    assert len(data["concepts"]) == 1
    assert data["concepts"][0]["name"] == "Test Concept"

@pytest.mark.asyncio
async def test_concept_validation():
    """Test concept validation."""
    # Should pass validation
    concept = Concept(
        name="Valid Concept",
        category="Test",
        attributes={
            "valid": "attribute",
            "nested": {
                "data": "valid"
            }
        }
    )
    assert concept.attributes["valid"] == "attribute"
    
    # Should fail validation
    with pytest.raises(Exception):
        Concept(
            name="Invalid Concept",
            attributes={
                "invalid": lambda x: x  # Functions aren't JSON serializable
            }
        )

@pytest.mark.asyncio
async def test_store_episodic_memory(memory_system):
    """Test storing episodic memory."""
    # Create test memory
    memory = EpisodicMemory(
        content="Test conversation about AI",
        concepts=[
            Concept(
                name="Artificial Intelligence",
                category="Technology"
            )
        ],
        relationships=[
            Relationship(
                from_concept="Artificial Intelligence",
                to_concept="Machine Learning",
                type="INCLUDES"
            )
        ],
        context={"location": "office"}
    )
    
    # Store memory
    await memory_system.store_experience(memory)
    
    # Verify storage
    memories = await memory_system.query_episodic({"type": MemoryType.EPISODIC})
    assert len(memories) == 1
    assert memories[0].content == "Test conversation about AI"
    assert len(memories[0].concepts) == 1
    assert memories[0].concepts[0].name == "Artificial Intelligence"

@pytest.mark.asyncio
async def test_memory_validation(memory_system):
    """Test memory content and metadata validation."""
    # Valid memory
    memory = EpisodicMemory(
        content={
            "valid": "content",
            "nested": {"data": True}
        },
        metadata={
            "valid": "metadata"
        }
    )
    await memory_system.store_experience(memory)
    
    # Invalid content should raise validation error
    with pytest.raises(Exception):
        invalid_memory = EpisodicMemory(
            content={
                "invalid": lambda x: x  # Functions aren't JSON serializable
            }
        )
        
    # Invalid metadata should raise validation error
    with pytest.raises(Exception):
        invalid_memory = EpisodicMemory(
            content="valid",
            metadata={
                "invalid": lambda x: x  # Functions aren't JSON serializable
            }
        )

@pytest.mark.asyncio
async def test_memory_consolidation(memory_system):
    """Test memory consolidation process."""
    # Create multiple related memories
    memories = [
        EpisodicMemory(
            content="Discussion about neural networks",
            concepts=[
                Concept(
                    name="Neural Networks",
                    category="AI Technology"
                )
            ]
        ),
        EpisodicMemory(
            content="Deep learning applications",
            concepts=[
                Concept(
                    name="Deep Learning",
                    category="AI Technology"
                )
            ],
            relationships=[
                Relationship(
                    from_concept="Deep Learning",
                    to_concept="Neural Networks",
                    type="USES"
                )
            ]
        )
    ]
    
    # Store memories
    for memory in memories:
        await memory_system.store_experience(memory)
    
    # Force consolidation
    await memory_system.consolidate_memories()
    
    # Verify semantic knowledge
    semantic_results = await memory_system.query_semantic({
        "type": "concept",
        "label": "AI Technology"
    })
    
    assert len(semantic_results) > 0
    # Verify relationships were created
    assert len(memory_system.semantic.store.relationships) > 0

@pytest.mark.asyncio
async def test_semantic_store_reuse(memory_system):
    """Test reuse of ConceptStore functionality."""
    # Store concept using inherited ConceptStore method
    await memory_system.semantic.store_concept(
        name="Test Concept",
        type="Test",
        description="Testing ConceptStore reuse",
        related=["Related Concept"]
    )
    
    # Verify using inherited query functionality
    concepts = await memory_system.semantic.get_concepts_by_type("Test")
    assert len(concepts) > 0
    assert concepts[0]["name"] == "Test Concept"
    assert concepts[0]["type"] == "Test"
    
    # Test relationship creation
    related = await memory_system.semantic.get_related_concepts("Test Concept")
    assert len(related) > 0
    assert "Related Concept" in [r["name"] for r in related]

@pytest.mark.asyncio
async def test_importance_based_consolidation(memory_system):
    """Test consolidation triggered by importance."""
    # Create important memory
    memory = EpisodicMemory(
        content="Critical system update",
        importance=0.9,
        concepts=[
            Concept(
                name="System Update",
                category="Maintenance"
            )
        ]
    )
    
    # Store memory
    await memory_system.store_experience(memory)
    
    # Verify consolidation was triggered
    assert await memory_system.consolidation_manager.should_consolidate()

@pytest.mark.asyncio
async def test_memory_querying(memory_system):
    """Test memory querying capabilities."""
    # Store test memories
    memories = [
        EpisodicMemory(
            content="Meeting about project A",
            context={"project": "A"},
            participants=["Alice", "Bob"]
        ),
        EpisodicMemory(
            content="Meeting about project B",
            context={"project": "B"},
            participants=["Charlie", "David"]
        )
    ]
    
    for memory in memories:
        await memory_system.store_experience(memory)
    
    # Test querying by context
    results = await memory_system.query_episodic({
        "filter": {"context.project": "A"}
    })
    
    assert len(results) == 1
    assert results[0].context["project"] == "A"
    assert "Alice" in results[0].participants

if __name__ == "__main__":
    pytest.main([__file__])
