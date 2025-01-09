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
    Memory, TaskOutput, GraphNode, GraphEdge,
    MemoryType, OutputType, TaskStatus, Domain,
    EpisodicMemory, MockMemory, Concept, Relationship,
    ValidationSchema, CrossDomainSchema, DomainContext,
    BaseDomain, KnowledgeVertical
)
from nia.memory.types.json_utils import validate_json_structure
from nia.memory.types.concept_utils import validate_concept_structure

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    class MockVectorStore:
        def __init__(self):
            self.vectors = {}
            
        async def store_vector(self, content: Dict, metadata: Dict = None, layer: str = None) -> str:
            vector_id = str(uuid.uuid4())
            # Store memory fields
            if isinstance(content, dict) and "text" in content:
                # Handle content dict format from EpisodicLayer.store_memory
                memory_dict = {
                    "id": vector_id,
                    "content": content["text"],
                    "type": metadata.get("type", MemoryType.EPISODIC),
                    "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                    "context": metadata.get("context", {}),
                    "concepts": metadata.get("concepts", []),
                    "relationships": metadata.get("relationships", []),
                    "participants": metadata.get("participants", []),
                    "importance": metadata.get("importance", 0.0),
                    "metadata": metadata.get("metadata", {}),
                    "consolidated": False
                }
            elif isinstance(content, EpisodicMemory):
                memory_dict = content.dict()
                memory_dict["id"] = vector_id
                memory_dict["consolidated"] = False
            elif hasattr(content, "dict"):
                memory_dict = content.dict()
                memory_dict["id"] = vector_id
                memory_dict["consolidated"] = False
            else:
                memory_dict = dict(content)
                memory_dict["id"] = vector_id
                memory_dict["consolidated"] = False

            # Extract fields from metadata if they exist
            if metadata:
                for field in ["concepts", "relationships", "participants", "importance", "context"]:
                    if field in metadata:
                        memory_dict[field] = metadata[field]

            # Validate and ensure all required fields are present with proper types
            if "concepts" not in memory_dict:
                memory_dict["concepts"] = []
            elif not isinstance(memory_dict["concepts"], list):
                memory_dict["concepts"] = [memory_dict["concepts"]]
            elif isinstance(memory_dict["concepts"], list):
                # Convert and validate each concept
                validated_concepts = []
                for c in memory_dict["concepts"]:
                    if hasattr(c, "dict"):
                        concept_dict = c.dict()
                    else:
                        concept_dict = c
                    
                    # Validate concept type
                    if "type" in concept_dict and concept_dict["type"] not in [
                        "entity", "action", "property", "event", "abstract"
                    ]:
                        raise ValueError(f"Invalid concept type: {concept_dict['type']}")
                    
                    # Validate confidence
                    if "confidence" in concept_dict:
                        confidence = float(concept_dict["confidence"])
                        if not 0 <= confidence <= 1:
                            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
                    
                    validated_concepts.append(concept_dict)
                memory_dict["concepts"] = validated_concepts
            
            if "relationships" not in memory_dict:
                memory_dict["relationships"] = []
            elif not isinstance(memory_dict["relationships"], list):
                memory_dict["relationships"] = [memory_dict["relationships"]]
            elif isinstance(memory_dict["relationships"], list):
                # Convert and validate each relationship
                validated_relationships = []
                for r in memory_dict["relationships"]:
                    if hasattr(r, "dict"):
                        rel_dict = r.dict()
                    else:
                        rel_dict = r
                    
                    # Validate relationship type
                    if "type" in rel_dict and rel_dict["type"] not in [
                        "is_a", "has_a", "part_of", "related_to", 
                        "causes", "implies", "precedes", "similar_to"
                    ]:
                        raise ValueError(f"Invalid relationship type: {rel_dict['type']}")
                    
                    # Validate confidence
                    if "confidence" in rel_dict:
                        confidence = float(rel_dict["confidence"])
                        if not 0 <= confidence <= 1:
                            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
                    
                    # Ensure domains list
                    if "domains" not in rel_dict:
                        rel_dict["domains"] = ["professional"]
                    elif not isinstance(rel_dict["domains"], list):
                        rel_dict["domains"] = [rel_dict["domains"]]
                    
                    validated_relationships.append(rel_dict)
                memory_dict["relationships"] = validated_relationships
            
            if "participants" not in memory_dict:
                memory_dict["participants"] = []
            elif not isinstance(memory_dict["participants"], list):
                memory_dict["participants"] = [memory_dict["participants"]]
            
            if "importance" not in memory_dict:
                memory_dict["importance"] = 0.0
            elif not isinstance(memory_dict["importance"], (int, float)):
                memory_dict["importance"] = float(memory_dict["importance"])
            
            # Validate context structure
            if "context" not in memory_dict:
                memory_dict["context"] = {"domain": "professional", "source": "professional"}
            elif not isinstance(memory_dict["context"], dict):
                memory_dict["context"] = {"value": memory_dict["context"]}
            else:
                # Ensure required context fields
                if "domain" not in memory_dict["context"]:
                    memory_dict["context"]["domain"] = "professional"
                if "source" not in memory_dict["context"]:
                    memory_dict["context"]["source"] = "professional"
            
            if "metadata" not in memory_dict:
                memory_dict["metadata"] = {}
            elif not isinstance(memory_dict["metadata"], dict):
                memory_dict["metadata"] = {"value": memory_dict["metadata"]}

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
            
        async def search_vectors(self, content: str = None, filter: Dict = None, limit: int = None, score_threshold: float = None, layer: str = None) -> List[Dict]:
            # Return all vectors for consolidation candidates
            if content is None and filter is None:
                return [v["content"] for v in self.vectors.values()]
            
            # Handle filtered search
            results = []
            for vector in self.vectors.values():
                if filter:
                    # Handle nested filters
                    matches = True
                    for key, value in filter.items():
                        if isinstance(value, dict):
                            # Handle nested dictionary filters (e.g., {"context": {"project": "A"}})
                            if key not in vector["content"]:
                                matches = False
                                break
                            current = vector["content"][key]
                            for subkey, subvalue in value.items():
                                if not isinstance(current, dict) or subkey not in current or current[subkey] != subvalue:
                                    matches = False
                                    break
                        elif key == "type":
                            # Handle type filter directly from content
                            if vector["content"]["type"] != value:
                                matches = False
                        else:
                            # Handle direct metadata filters
                            if vector["metadata"].get(key) != value:
                                matches = False
                    if matches:
                        # Convert concepts and relationships back to their proper types
                        memory_data = dict(vector["content"])
                        if "concepts" in memory_data:
                            memory_data["concepts"] = [
                                Concept(**c) if isinstance(c, dict) else c
                                for c in memory_data["concepts"]
                            ]
                        if "relationships" in memory_data:
                            memory_data["relationships"] = [
                                Relationship(**r) if isinstance(r, dict) else r
                                for r in memory_data["relationships"]
                            ]
                        results.append(EpisodicMemory(**memory_data))
                else:
                    # Convert concepts and relationships back to their proper types
                    memory_data = dict(vector["content"])
                    if "concepts" in memory_data:
                        memory_data["concepts"] = [
                            Concept(**c) if isinstance(c, dict) else c
                            for c in memory_data["concepts"]
                        ]
                    if "relationships" in memory_data:
                        memory_data["relationships"] = [
                            Relationship(**r) if isinstance(r, dict) else r
                            for r in memory_data["relationships"]
                        ]
                    results.append(EpisodicMemory(**memory_data))
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

        async def consume(self):
            """Consume the result."""
            return self._data
            
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
                        if node["properties"]["name"] == params.get("name"):
                            source_node = node
                        if node["properties"]["name"] == params.get("related_name"):
                            target_node = node
                    
                    if not source_node:
                        node_id = str(uuid.uuid4())
                        source_node = {
                            "label": "Concept",
                            "properties": {
                                "name": params.get("name"),
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
                                "name": params.get("related_name"),
                                "type": params.get("type", "concept"),
                                "description": "",
                                "is_consolidation": False
                            }
                        }
                        self.store.nodes[node_id] = target_node
                    
                    # Create relationship with enhanced properties
                    relationship = {
                        "from": params.get("name"),
                        "to": params.get("related_name"),
                        "type": params.get("type", "RELATED_TO"),
                        "properties": {
                            "domains": params.get("domains", ["professional"]),
                            "confidence": params.get("confidence", 1.0),
                            "bidirectional": params.get("bidirectional", False),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "last_updated": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    self.store.relationships.append(relationship)
                    
                    # Create reverse relationship if bidirectional
                    if params.get("bidirectional", False):
                        reverse_relationship = {
                            "from": params.get("related_name"),
                            "to": params.get("name"),
                            "type": params.get("type", "RELATED_TO"),
                            "properties": {
                                "domains": params.get("domains", ["professional"]),
                                "confidence": params.get("confidence", 1.0),
                                "bidirectional": True,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "last_updated": datetime.now(timezone.utc).isoformat()
                            }
                        }
                        self.store.relationships.append(reverse_relationship)
                    
                    return MockAsyncResult([{
                        "c": source_node["properties"], 
                        "r": target_node["properties"],
                        "relationship": relationship["properties"]
                    }])
            elif "MATCH ()-[r:RELATED_TO]->() RETURN count" in query:
                # Handle relationship count query
                return MockAsyncResult([{"count": len(self.store.relationships)}])
            return MockAsyncResult([])

    class MockNeo4jStore(Neo4jBaseStore):
        def __init__(self):
            super().__init__("bolt://127.0.0.1:7687", user="neo4j", password="password")
            self.nodes = {}
            self.relationships = []  # List to store relationships
            self.beliefs = []
            self.driver = self
            print(f"\nInitialized MockNeo4jStore with empty relationships list (id: {id(self.relationships)})")
            
        def session(self, database=None, default_access_mode=None):
            """Create a mock session."""
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
            print(f"Relationships before: {self.store.relationships}")
            relationship = {
                "from": start_node,
                "to": end_node,
                "type": type,
                "properties": properties or {}
            }
            self.relationships.append(relationship)
            print(f"Added relationship: {relationship}")
            print(f"Relationships after: {self.relationships}")
            
        async def create_belief(
            self, 
            subject: str, 
            predicate: str, 
            object: str, 
            confidence: float = 1.0,
            domains: List[str] = None,
            context: Dict = None,
            source: str = "professional"
        ):
            """Create a belief with enhanced metadata."""
            # Validate confidence
            if not 0 <= confidence <= 1:
                raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
                
            # Ensure domains list
            if domains is None:
                domains = ["professional"]
                
            # Ensure context dict
            if context is None:
                context = {}
                
            self.beliefs.append({
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "confidence": confidence,
                "domains": domains,
                "context": context,
                "source": source,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
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
async def test_importance_based_consolidation(memory_system):
    """Test consolidation triggered by importance."""
    # Create important memory
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
        content="Critical system update",
        type=MemoryType.EPISODIC,
        importance=0.9,
        knowledge={
            "concepts": [
                {
                    "name": "System Update",
                    "type": "entity",
                    "description": "Critical system maintenance update",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.store_experience(memory)
    
    # Verify consolidation was triggered
    assert await memory_system.consolidation_manager.should_consolidate()

@pytest.mark.asyncio
async def test_memory_querying(memory_system):
    """Test memory querying capabilities."""
    # Store test memories
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
    memories = [
        MockMemory(
            content="Meeting about project A",
            type=MemoryType.EPISODIC,
            context={"project": "A"},
            participants=["Alice", "Bob"],
            knowledge={
                "concepts": [
                    {
                        "name": "Project A",
                        "type": "entity",
                        "description": "Project A meeting and discussion",
                        "validation": validation.dict(),
                        "domain_context": domain_context.dict()
                    }
                ]
            },
            validation=validation,
            domain_context=domain_context
        ),
        MockMemory(
            content="Meeting about project B",
            type=MemoryType.EPISODIC,
            context={"project": "B"},
            participants=["Charlie", "David"],
            knowledge={
                "concepts": [
                    {
                        "name": "Project B",
                        "type": "entity",
                        "description": "Project B meeting and discussion",
                        "validation": validation.dict(),
                        "domain_context": domain_context.dict()
                    }
                ]
            },
            validation=validation,
            domain_context=domain_context
        )
    ]
    
    for memory in memories:
        await memory_system.store_experience(memory)
    
    # Test querying by context
    results = await memory_system.query_episodic({
        "filter": {"context": {"project": "A"}}
    })
    
    assert len(results) == 1
    assert results[0].context["project"] == "A"
    assert "Alice" in results[0].participants

@pytest.mark.asyncio
async def test_validation_errors(memory_system):
    """Test validation error handling."""
    # Test invalid concept type
    with pytest.raises(ValueError, match="type"):
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
            content="Invalid concept",
            type=MemoryType.EPISODIC,
            importance=0.8,
            knowledge={
                "concepts": [
                    {
                        "name": "Test",
                        "type": "invalid_type",  # Should fail validation
                        "description": "Test concept",
                        "validation": validation.dict(),
                        "domain_context": domain_context.dict()
                    }
                ]
            },
            validation=validation,
            domain_context=domain_context
        )
        await memory_system.store_experience(memory)

    # Test invalid confidence value
    with pytest.raises(ValueError, match="confidence"):
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
            content="Invalid confidence",
            type=MemoryType.EPISODIC,
            importance=0.8,
            knowledge={
                "concepts": [
                    {
                        "name": "Test",
                        "type": "entity",
                        "description": "Test concept",
                        "validation": validation.dict(),
                        "domain_context": domain_context.dict(),
                        "confidence": 1.5  # Should fail validation
                    }
                ]
            },
            validation=validation,
            domain_context=domain_context
        )
        await memory_system.store_experience(memory)

    # Test missing required context fields
    with pytest.raises(ValueError, match="context"):
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
            content="Missing context",
            type=MemoryType.EPISODIC,
            importance=0.8,
            context={},  # Missing required fields
            knowledge={
                "concepts": [
                    {
                        "name": "Test",
                        "type": "entity",
                        "description": "Test concept",
                        "validation": validation.dict(),
                        "domain_context": domain_context.dict()
                    }
                ]
            },
            validation=validation,
            domain_context=domain_context
        )
        await memory_system.store_experience(memory)

@pytest.mark.asyncio
async def test_bidirectional_relationships(memory_system):
    """Test bidirectional relationship handling."""
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
        content="System architecture",
        type=MemoryType.EPISODIC,
        importance=0.8,
        knowledge={
            "concepts": [
                {
                    "name": "Frontend",
                    "type": "entity",
                    "description": "Frontend system",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                },
                {
                    "name": "Backend",
                    "type": "entity",
                    "description": "Backend system",
                    "validation": validation.dict(),
                    "domain_context": domain_context.dict()
                }
            ],
            "relationships": [
                {
                    "source": "Frontend",
                    "target": "Backend",
                    "type": "communicates_with",
                    "domain_context": domain_context.dict(),
                    "confidence": 0.9,
                    "bidirectional": True
                }
            ]
        },
        validation=validation,
        domain_context=domain_context
    )
    
    # Store memory
    await memory_system.store_experience(memory)
    
    # Trigger consolidation
    await memory_system.consolidate_memories()
    
    # Verify both relationships exist
    results = await memory_system.query_semantic({
        "type": "concept",
        "pattern": "Frontend|Backend"
    })
    
    assert len(results) > 0
    
    # Check relationships in both directions
    found_forward = False
    found_reverse = False
    for result in results:
        if "Frontend" in str(result) and "Backend" in str(result):
            found_forward = True
        if "Backend" in str(result) and "Frontend" in str(result):
            found_reverse = True
    
    assert found_forward and found_reverse, "Bidirectional relationship not properly established"

if __name__ == "__main__":
    pytest.main([__file__])
