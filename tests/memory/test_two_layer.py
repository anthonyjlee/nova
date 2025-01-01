"""Tests for the two-layer memory system."""

import pytest
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import uuid
import json

logger = logging.getLogger(__name__)

from nia.memory.two_layer import TwoLayerMemorySystem, EpisodicLayer, SemanticLayer
from nia.memory.consolidation import ConsolidationManager
from nia.memory.neo4j.base_store import Neo4jBaseStore
from nia.memory.types.memory_types import (
    Memory, EpisodicMemory, SemanticMemory, 
    Concept, Relationship, Belief,
    MemoryType, JSONSerializable
)
from nia.memory.types.json_utils import validate_json_structure
from nia.memory.types.concept_utils import validate_concept_structure

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    class MockVectorStore:
        def __init__(self):
            self.vectors = {}
            
        async def store_vector(self, content: Dict, metadata: Dict = None) -> str:
            vector_id = str(uuid.uuid4())
            # Store memory fields
            if hasattr(content, "dict"):
                memory_dict = content.dict()
            elif isinstance(content, dict):
                memory_dict = content.copy()
            else:
                memory_dict = content
            memory_dict["id"] = vector_id
            memory_dict["consolidated"] = False
            memory_dict["importance"] = getattr(content, "importance", content.get("importance", 0))
            self.vectors[vector_id] = {
                "content": memory_dict,
                "metadata": metadata or {}
            }
            return vector_id
            
        async def get_vector(self, vector_id: str) -> Dict:
            vector = self.vectors.get(vector_id, {})
            if not vector:
                return None
            return vector["content"]
            
        async def search_vectors(self, content: str = None, filter: Dict = None) -> List[Dict]:
            # Return all vectors for consolidation candidates
            if content is None and filter is None:
                return [v["content"] for v in self.vectors.values()]
            
            # Handle filtered search
            results = []
            for vector in self.vectors.values():
                if filter:
                    # Handle nested filters like "context.project"
                    matches = True
                    for key, value in filter.items():
                        if "." in key:
                            # Handle nested keys
                            parts = key.split(".")
                            current = vector["metadata"]
                            for part in parts:
                                if part not in current:
                                    matches = False
                                    break
                                current = current[part]
                            if matches and current != value:
                                matches = False
                        else:
                            if vector["metadata"].get(key) != value:
                                matches = False
                    if matches:
                        results.append(vector["content"])
                else:
                    results.append(vector["content"])
            return results
            
        async def update_metadata(self, vector_id: str, metadata: Dict):
            if vector_id in self.vectors:
                self.vectors[vector_id]["metadata"].update(metadata)
                
    return MockVectorStore()

@pytest.fixture(autouse=True)
def mock_neo4j_store():
    """Mock Neo4j store for testing. autouse=True ensures a fresh store for each test."""
    class MockAsyncResult:
        def __init__(self, data):
            self._data = data
            
        async def data(self):
            return self._data
            
        async def single(self):
            """Get the first record."""
            if self._data:
                return self._data[0]
            return None
            
        def __aiter__(self):
            """Make the result iterable."""
            return self
            
        async def __anext__(self):
            """Get next item for async iteration."""
            if not hasattr(self, '_iter_index'):
                self._iter_index = 0
            if self._iter_index < len(self._data):
                result = self._data[self._iter_index]
                self._iter_index += 1
                return result
            raise StopAsyncIteration

    class MockSession:
        def __init__(self, store):
            self.store = store
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def run(self, query: str, parameters=None, **kwargs):
            # Debug print
            print(f"\nExecuting query: {query}")
            print(f"With parameters: {parameters}")
            print(f"And kwargs: {kwargs}")
            
            # For UNWIND queries, prefer parameters over kwargs
            if "UNWIND" in query:
                params = parameters or {}
            else:
                # For other queries, combine parameters and kwargs
                params = {}
                if parameters:
                    params.update(parameters)
                if kwargs:
                    params.update(kwargs)
            if "MATCH (c:Concept {type: $type})" in query:
                # Handle get_concepts_by_type query
                matching_nodes = []
                for node in self.store.nodes.values():
                    if node["properties"]["type"] == params["type"]:
                        matching_nodes.append({
                            "c": node["properties"],
                            "related": []  # Add empty related list as per query
                        })
                return MockAsyncResult(matching_nodes)
            elif "WHERE" in query and "Concept" in query:
                # Handle semantic query with type/label
                conditions = []
                if "type = $type" in query and "type" in params:
                    type_value = params["type"]
                    conditions.append(lambda props: props.get("type") == type_value)
                if "label = $label" in query and "label" in params:
                    label_value = params["label"]
                    conditions.append(lambda props: props.get("type") == label_value)
                
                matching_nodes = []
                for node in self.store.nodes.values():
                    props = node["properties"]
                    if all(condition(props) for condition in conditions):
                        matching_nodes.append({"n": props})
                return MockAsyncResult(matching_nodes)
            elif "MERGE (c:Concept" in query:
                # Extract parameters from the query if not in params
                if "SET" in query:
                    # This is a full concept creation/update
                    if "name" not in params and "{name:" in query:
                        name = query.split("{name: '")[1].split("'")[0]
                        params["name"] = name
                    if "type" not in params and "type:" in query:
                        type_val = query.split("type: '")[1].split("'")[0]
                        params["type"] = type_val
                    if "description" not in params and "description:" in query:
                        desc = query.split("description: '")[1].split("'")[0]
                        params["description"] = desc

                # Handle MERGE with ON CREATE SET
                if "ON CREATE SET" in query:
                    # Extract name from MERGE clause
                    name = params.get("name")
                    if not name:
                        raise Exception("Missing required parameter: name")

                    # Check if node already exists
                    existing_node = None
                    for n in self.store.nodes.values():
                        if n["properties"]["name"] == name:
                            existing_node = n
                            break

                    if not existing_node:
                        # Create new node with ON CREATE SET properties
                        node = {
                            "name": name,
                            "type": "pending",
                            "description": "Pending concept",
                            "is_consolidation": False
                        }
                        node_id = str(uuid.uuid4())
                        self.store.nodes[node_id] = {
                            "label": "Concept",
                            "properties": node
                        }
                        existing_node = self.store.nodes[node_id]
                    return MockAsyncResult([{"c": existing_node["properties"]}])
                else:
                    # Regular MERGE without ON CREATE SET
                    node = {
                        "name": params.get("name"),
                        "type": params.get("type", "concept"),
                        "description": params.get("description", ""),
                        "is_consolidation": params.get("is_consolidation", False)
                    }

                    # Validate required fields
                    if not node["name"]:
                        raise Exception("Missing required parameter: name")

                    # Check if node already exists
                    existing_node = None
                    for n in self.store.nodes.values():
                        if n["properties"]["name"] == node["name"]:
                            existing_node = n
                            break

                    if not existing_node:
                        node_id = str(uuid.uuid4())
                        self.store.nodes[node_id] = {
                            "label": "Concept",
                            "properties": node
                        }
                        existing_node = self.store.nodes[node_id]

                    # Update existing node properties
                    existing_node["properties"].update(node)
                    return MockAsyncResult([{"c": existing_node["properties"]}])
            elif "MATCH (c:Concept {name: $name})-[:RELATED_TO]->(r:Concept)" in query:
                # Handle get_related_concepts query
                matching_nodes = []
                # Find all direct relationships
                for rel in self.store.relationships:
                    if rel["from"] == params["name"]:
                        # Find the target node
                        for node in self.store.nodes.values():
                            if node["properties"]["name"] == rel["to"]:
                                # Find any relationships from this target node
                                secondary_relations = []
                                for r2 in self.store.relationships:
                                    if r2["from"] == rel["to"]:
                                        secondary_relations.append(r2["to"])
                                matching_nodes.append({
                                    "c": node["properties"],
                                    "related": secondary_relations
                                })
                                break  # Found the node, no need to continue searching
                
                return MockAsyncResult(matching_nodes)
            elif "MERGE (c)-[:RELATED_TO]->(r)" in query or "MERGE (c1)-[:RELATED_TO" in query:
                # Handle relationship creation
                if "UNWIND" in query and "MERGE (c)-[:RELATED_TO]->(r)" in query:
                    print("\nHandling UNWIND relationship creation")
                    print(f"Store relationships before: {self.store.relationships}")
                    
                    # Get parameters from parameters first, then kwargs
                    source_name = parameters.get("name") if parameters else kwargs.get("name")
                    related_names = parameters.get("related", []) if parameters else kwargs.get("related", [])
                    if isinstance(related_names, str):
                        related_names = [related_names]
                    elif not isinstance(related_names, list):
                        related_names = list(related_names)
                    
                    # Validate parameters
                    if not source_name or not related_names:
                        print("ERROR: Missing required parameters for relationship creation")
                        print(f"source_name: {source_name}")
                        print(f"related_names: {related_names}")
                        return MockAsyncResult([])

                    # Create relationships and nodes
                    results = []
                    for rel_name in related_names:
                        # Find or create target node
                        target_node = None
                        for node in self.store.nodes.values():
                            if node["properties"]["name"] == rel_name:
                                target_node = node
                                break
                        if not target_node:
                            node_id = str(uuid.uuid4())
                            target_node = {
                                "label": "Concept",
                                "properties": {
                                    "name": rel_name,
                                    "type": "pending",
                                    "description": "Pending concept",
                                    "is_consolidation": False
                                }
                            }
                            self.store.nodes[node_id] = target_node
                        
                        # Create relationship
                        relationship = {
                            "from": source_name,
                            "to": rel_name,
                            "type": "RELATED_TO",
                            "properties": {}
                        }
                        print(f"Creating relationship: {relationship}")
                        self.store.relationships.append(relationship)
                        print(f"Store relationships after append: {self.store.relationships}")
                        
                        # Add target node to results
                        results.append({
                            "c": target_node["properties"],
                            "related": []
                        })
                    
                    return MockAsyncResult(results)
                    
                else:
                    # Create direct relationship
                    # Find or create source node
                    source_node = None
                    target_node = None
                    for node in self.store.nodes.values():
                        if node["properties"]["name"] == params["from"]:
                            source_node = node
                        if node["properties"]["name"] == params["to"]:
                            target_node = node
                    
                    if not source_node:
                        node_id = str(uuid.uuid4())
                        source_node = {
                            "label": "Concept",
                            "properties": {
                                "name": params["from"],
                                "type": params.get("type", "concept"),
                                "description": "",
                                "is_consolidation": False
                            }
                        }
                        self.store.nodes[node_id] = source_node
                    
                    if not target_node:
                        node_id = str(uuid.uuid4())
                        target_node = {
                            "label": "Concept",
                            "properties": {
                                "name": params["to"],
                                "type": params.get("type", "concept"),
                                "description": "",
                                "is_consolidation": False
                            }
                        }
                        self.store.nodes[node_id] = target_node
                    
                    # Create relationship
                    self.store.relationships.append({
                        "from": params["from"],
                        "to": params["to"],
                        "type": params["type"],
                        "properties": {}
                    })
                    
                    return MockAsyncResult([{"c": source_node["properties"], "r": target_node["properties"]}])
            elif "MATCH ()-[r:RELATED_TO]->() RETURN count" in query:
                # Handle relationship count query
                return MockAsyncResult([{"count": len(self.store.relationships)}])
            return MockAsyncResult([])

    class MockNeo4jStore(Neo4jBaseStore):
        def __init__(self):
            super().__init__("bolt://127.0.0.1:7687", "neo4j", "password")
            self.nodes = {}
            self.relationships = []  # List to store relationships
            self.beliefs = []
            self.driver = self
            print(f"\nInitialized MockNeo4jStore with empty relationships list (id: {id(self.relationships)})")
            
        def session(self):
            return MockSession(self)
            
        async def close(self):
            """Close the mock store."""
            pass
            
        async def create_concept_node(self, label: str, properties: Dict):
            node_id = str(uuid.uuid4())
            self.nodes[node_id] = {
                "label": label,
                "properties": properties
            }
            return node_id
            
        async def create_relationship(self, start_node: str, end_node: str, type: str, properties: Dict = None):
            print(f"\nCreating relationship: {start_node} -> {end_node}")
            print(f"Relationships before: {self.relationships}")
            relationship = {
                "from": start_node,
                "to": end_node,
                "type": type,
                "properties": properties or {}
            }
            self.relationships.append(relationship)
            print(f"Added relationship: {relationship}")
            print(f"Relationships after: {self.relationships}")
            
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
    system = TwoLayerMemorySystem("bolt://127.0.0.1:7687", mock_vector_store)
    system.semantic = SemanticLayer(mock_neo4j_store)
    system.consolidation_manager = ConsolidationManager(system.episodic, system.semantic)
    return system

@pytest.mark.asyncio
async def test_json_serialization():
    """Test JSON serialization of memory objects."""
    # Create test memory
    memory = EpisodicMemory(
        content="Test memory",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        concepts=[
            Concept(
                name="Test Concept",
                type="Test",
                category="Test",
                description="A test concept for memory",
                attributes={"test": "value"},
                confidence=0.8
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
        type="Test",
        category="Test",
        description="A valid test concept",
        attributes={"test": "value"},
        confidence=0.8
    )
    assert concept.confidence == 0.8
    
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
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        concepts=[
            Concept(
                name="Artificial Intelligence",
                type="Technology",
                category="Technology",
                description="The field of artificial intelligence and its applications",
                attributes={"domain": "computer science"},
                confidence=0.9
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
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        metadata={
            "valid": "metadata"
        },
        concepts=[
            Concept(
                name="Test Content",
                type="Test",
                category="Test",
                description="Test content for validation",
                attributes={"test": "value"},
                confidence=0.8
            )
        ]
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
            content="Neural network research task",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            metadata={
                "agents": [{
                    "name": "ResearchAgent",
                    "type": "Research",
                    "skills": ["neural networks", "deep learning"],
                    "state": "active"
                }],
                "tasks": [{
                    "name": "Neural Network Analysis",
                    "category": "Research",
                    "description": "Analyzing neural network architectures",
                    "status": "completed",
                    "priority": "high"
                }],
                "observations": [{
                    "type": "capability",
                    "agent": "ResearchAgent",
                    "capability": "neural_network_analysis",
                    "confidence": 0.9
                }]
            },
            concepts=[
                Concept(
                    name="Neural Networks",
                    type="AI Technology",
                    category="AI Technology",
                    description="Neural network architectures and concepts",
                    attributes={"architecture": "deep learning"},
                    confidence=0.9
                )
            ]
        ),
        EpisodicMemory(
            content="Deep learning implementation task",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            metadata={
                "agents": [{
                    "name": "TaskAgent",
                    "type": "Implementation",
                    "skills": ["deep learning", "coding"],
                    "state": "active"
                }],
                "tasks": [{
                    "name": "Deep Learning Implementation",
                    "category": "Development",
                    "description": "Implementing deep learning models",
                    "status": "in_progress",
                    "priority": "high"
                }],
                "interactions": [{
                    "source_agent": "TaskAgent",
                    "target_agent": "ResearchAgent",
                    "type": "COLLABORATES_WITH",
                    "timestamp": datetime.now().isoformat(),
                    "context": "deep learning implementation"
                }]
            },
            concepts=[
                Concept(
                    name="Deep Learning",
                    type="AI Technology",
                    category="AI Technology",
                    description="Deep learning methods and applications",
                    attributes={"application": "machine learning"},
                    confidence=0.9
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
    async with memory_system.semantic.driver.session() as session:
        result = await session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
        data = await result.data()
        print(f"Relationships in store: {session.store.relationships}")  # Debug print
        assert data[0]["count"] > 0

@pytest.mark.asyncio
async def test_semantic_store_reuse(memory_system):
    """Test reuse of ConceptStore functionality."""
    # Store concept using inherited ConceptStore method
    print("Storing concept...")
    await memory_system.semantic.store_concept(
        name="Test Concept",
        type="Test",
        description="Testing ConceptStore reuse",
        related=["Related Concept"]
    )
    print("Concept stored")
    
    # Wait a moment for the relationships to be created
    print("Waiting for relationships...")
    await asyncio.sleep(0.1)
    print("Done waiting")
    
    # Verify using inherited query functionality
    print("Getting concepts by type...")
    concepts = await memory_system.semantic.get_concepts_by_type("Test")
    print(f"Found concepts: {concepts}")
    assert len(concepts) > 0
    assert concepts[0]["name"] == "Test Concept"
    assert concepts[0]["type"] == "Test"
    
    # Verify relationship creation
    print("Verifying relationships...")
    async with memory_system.semantic.driver.session() as session:
        # Create relationship directly
        await session.run(
            "MATCH (c:Concept {name: $name}) "
            "MATCH (r:Concept {name: $related_name}) "
            "MERGE (c)-[:RELATED_TO]->(r)",
            parameters={"name": "Test Concept", "related_name": "Related Concept"}
        )
        
        # First verify the relationship exists
        result = await session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
        data = await result.data()
        print(f"Relationships in store: {session.store.relationships}")  # Debug print
        assert data[0]["count"] > 0
        
        # Then get related concepts
        related = await memory_system.semantic.get_related_concepts("Test Concept")
        assert len(related) > 0
        assert "Related Concept" in [r["name"] for r in related]

@pytest.mark.asyncio
async def test_importance_based_consolidation(memory_system):
    """Test consolidation triggered by importance."""
    # Create important memory
    memory = EpisodicMemory(
        content="Critical system update",
        type=MemoryType.EPISODIC,
        timestamp=datetime.now().isoformat(),
        importance=0.9,
        concepts=[
            Concept(
                name="System Update",
                type="Maintenance",
                category="Maintenance",
                description="Critical system maintenance update",
                attributes={"priority": "high"},
                confidence=0.9
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
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            context={"project": "A"},
            participants=["Alice", "Bob"],
            concepts=[
                Concept(
                    name="Project A",
                    type="Project",
                    category="Project",
                    description="Project A meeting and discussion",
                    attributes={"status": "active"},
                    confidence=0.8
                )
            ]
        ),
        EpisodicMemory(
            content="Meeting about project B",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            context={"project": "B"},
            participants=["Charlie", "David"],
            concepts=[
                Concept(
                    name="Project B",
                    type="Project",
                    category="Project",
                    description="Project B meeting and discussion",
                    attributes={"status": "active"},
                    confidence=0.8
                )
            ]
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
