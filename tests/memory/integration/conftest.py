"""Shared fixtures for memory integration tests."""

import pytest
import uuid
import json
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

from nia.memory.types.memory_types import (
    Memory, MemoryType, EpisodicMemory,
    Concept, Relationship
)
from nia.memory.neo4j.base_store import Neo4jBaseStore
from nia.memory.two_layer import TwoLayerMemorySystem, SemanticLayer
from nia.core.neo4j.concept_store import ConceptStore
from nia.memory.consolidation import ConsolidationManager
from nia.world.environment import NIAWorld
from nia.nova.orchestrator import Nova

def format_timestamp():
    """Helper to format timestamp consistently."""
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    class MockVectorStore:
        def __init__(self):
            self.vectors = {}
            
        async def store_vector(self, content: Dict, metadata: Dict = None, layer: str = None) -> str:
            # Convert content to EpisodicMemory if needed
            if isinstance(content, dict):
                # Handle text content format
                if "text" in content:
                    memory_dict = {
                        "content": content["text"],
                        "type": MemoryType.EPISODIC.value,
                        "timestamp": metadata.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "context": metadata.get("context", {}),
                        "concepts": metadata.get("concepts", []),
                        "relationships": metadata.get("relationships", []),
                        "participants": metadata.get("participants", []),
                        "importance": metadata.get("importance", 0.0),
                        "metadata": metadata.get("metadata", {}),
                        "consolidated": False
                    }
                else:
                    # Handle direct memory dict format
                    memory_dict = dict(content)
                    if not memory_dict.get("content"):
                        raise ValueError("Memory must have content")
                    if not memory_dict.get("type"):
                        memory_dict["type"] = MemoryType.EPISODIC.value
                    if not memory_dict.get("timestamp"):
                        memory_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
                    memory_dict.setdefault("context", {})
                    memory_dict.setdefault("concepts", [])
                    memory_dict.setdefault("relationships", [])
                    memory_dict.setdefault("participants", [])
                    memory_dict.setdefault("importance", 0.0)
                    memory_dict.setdefault("metadata", {})
                    memory_dict.setdefault("consolidated", False)
                
                # Create EpisodicMemory instance
                memory = EpisodicMemory(**memory_dict)
                content = memory.dict()

            vector_id = str(uuid.uuid4())
            # Store memory fields
            if isinstance(content, dict):
                if "text" in content:
                    # Handle content dict format from EpisodicLayer.store_memory
                    memory_dict = {
                        "id": vector_id,
                        "content": content["text"],
                        "type": metadata.get("type", MemoryType.EPISODIC.value),
                        "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                        "context": metadata.get("context", {}),
                        "concepts": [],
                        "relationships": [],
                        "participants": metadata.get("participants", []) if metadata else [],
                        "importance": metadata.get("importance", 0.0),
                        "metadata": metadata.get("metadata", {}),
                        "consolidated": False
                    }
                else:
                    # Handle direct memory dict format
                    memory_dict = dict(content)
                    memory_dict["id"] = vector_id
                    memory_dict["consolidated"] = False
                    memory_dict.setdefault("concepts", [])
                    memory_dict.setdefault("relationships", [])
                    memory_dict.setdefault("participants", [])
            elif isinstance(content, EpisodicMemory):
                memory_dict = dict(content.dict())
                if isinstance(memory_dict.get("type"), MemoryType):
                    memory_dict["type"] = memory_dict["type"].value
                memory_dict["id"] = vector_id
                memory_dict["consolidated"] = False
            else:
                memory_dict = dict(content)
                if isinstance(memory_dict.get("type"), MemoryType):
                    memory_dict["type"] = memory_dict["type"].value
                memory_dict["id"] = vector_id
                memory_dict["consolidated"] = False
                memory_dict.setdefault("concepts", [])
                memory_dict.setdefault("relationships", [])
                memory_dict.setdefault("participants", [])

            # Extract fields from metadata if they exist
            if metadata:
                for field in ["concepts", "relationships", "participants", "importance", "context"]:
                    if field in metadata:
                        memory_dict[field] = metadata[field]

            # Ensure all required fields are present with proper types
            if "concepts" not in memory_dict:
                memory_dict["concepts"] = []
            elif not isinstance(memory_dict["concepts"], list):
                memory_dict["concepts"] = [memory_dict["concepts"]]
            elif isinstance(memory_dict["concepts"], list):
                # Convert each concept to a dict if it's not already
                memory_dict["concepts"] = [
                    c.dict() if hasattr(c, "dict") else c 
                    for c in memory_dict["concepts"]
                ]
            
            if "relationships" not in memory_dict:
                memory_dict["relationships"] = []
            elif not isinstance(memory_dict["relationships"], list):
                memory_dict["relationships"] = [memory_dict["relationships"]]
            elif isinstance(memory_dict["relationships"], list):
                # Convert each relationship to a dict if it's not already
                memory_dict["relationships"] = [
                    r.dict() if hasattr(r, "dict") else r 
                    for r in memory_dict["relationships"]
                ]
            
            if "participants" not in memory_dict:
                memory_dict["participants"] = []
            elif not isinstance(memory_dict["participants"], list):
                memory_dict["participants"] = [memory_dict["participants"]]
            
            if "importance" not in memory_dict:
                memory_dict["importance"] = 0.0
            elif not isinstance(memory_dict["importance"], (int, float)):
                memory_dict["importance"] = float(memory_dict["importance"])
            
            if "context" not in memory_dict:
                memory_dict["context"] = {}
            elif not isinstance(memory_dict["context"], dict):
                memory_dict["context"] = {"value": memory_dict["context"]}
            
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
            
        async def search_vectors(self, content: Dict = None, filter: Dict = None, limit: int = None, score_threshold: float = None, layer: str = None) -> List[Dict]:
            # Return all vectors for consolidation candidates
            if content is None and filter is None:
                return [v["content"] for v in self.vectors.values()]
            
            # Handle filtered search
            results = []
            for vector in self.vectors.values():
                matches = True
                
                # Check content match if provided
                if content:
                    if isinstance(content, dict) and "text" in content:
                        if content["text"] not in str(vector["content"].get("content", "")):
                            matches = False
                    elif isinstance(content, str):
                        if content not in str(vector["content"].get("content", "")):
                            matches = False
                
                # Check filter match if provided
                if matches and filter:
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
                    # Get the stored memory data
                    memory_data = vector["content"]
                    if isinstance(memory_data, dict):
                        # Create EpisodicMemory instance
                        try:
                            # Ensure participants is a list of strings
                            participants = memory_data.get("participants", [])
                            if not isinstance(participants, list):
                                participants = [str(participants)]
                            else:
                                participants = [str(p) for p in participants if p is not None]

                            # Get content from memory_data
                            content = memory_data.get("content", "")
                            if isinstance(content, dict):
                                content = content.get("text", "")

                            memory = EpisodicMemory(
                                id=memory_data.get("id"),
                                content=content,
                                type=memory_data.get("type", MemoryType.EPISODIC.value),
                                importance=memory_data.get("importance", 0.5),
                                timestamp=memory_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                                context=memory_data.get("context", {}),
                                consolidated=memory_data.get("consolidated", False),
                                participants=participants,
                                concepts=memory_data.get("concepts", []),
                                relationships=memory_data.get("relationships", []),
                                emotions=memory_data.get("emotions", {}),
                                related_memories=memory_data.get("related_memories", [])
                            )
                            results.append(memory)
                        except Exception as e:
                            logger.error(f"Failed to create EpisodicMemory: {str(e)}")
            
            # Apply limit if provided
            if limit is not None and len(results) > limit:
                results = results[:limit]
                
            return results
            
        async def update_metadata(self, vector_id: str, metadata: Dict):
            if vector_id in self.vectors:
                # Update consolidated flag in both content and metadata
                if "consolidated" in metadata:
                    self.vectors[vector_id]["content"]["consolidated"] = metadata["consolidated"]
                    self.vectors[vector_id]["metadata"]["consolidated"] = metadata["consolidated"]
                    
                # Update other metadata
                for key, value in metadata.items():
                    if key != "consolidated":
                        self.vectors[vector_id]["metadata"][key] = value
                        
        async def delete_vector(self, vector_id: str):
            """Delete a vector from storage."""
            if vector_id in self.vectors:
                del self.vectors[vector_id]
                return True
            return False
                
    return MockVectorStore()

@pytest.fixture(autouse=True)
def mock_neo4j_store():
    """Mock Neo4j store for testing. autouse=True ensures a fresh store for each test."""
    class MockAsyncResult:
        def __init__(self, data):
            self._data = data
            logger.info(f"Created MockAsyncResult with data: {data}")
            
        async def data(self):
            logger.info(f"Returning data: {self._data}")
            return self._data
            
        async def single(self):
            """Get the first record."""
            if self._data:
                logger.info(f"Returning first record: {self._data[0]}")
                return self._data[0]
            logger.info("No records found")
            return None

        async def consume(self):
            """Consume the result."""
            logger.info(f"Consuming data: {self._data}")
            return self._data
            
        def __aiter__(self):
            """Make the result iterable."""
            logger.info("Creating async iterator")
            return self
            
        async def __anext__(self):
            """Get next item for async iteration."""
            if not hasattr(self, '_iter_index'):
                self._iter_index = 0
            if self._iter_index < len(self._data):
                result = self._data[self._iter_index]
                self._iter_index += 1
                logger.info(f"Yielding next item: {result}")
                return result
            logger.info("No more items")
            raise StopAsyncIteration

    class MockSession:
        def __init__(self, store):
            self.store = store
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def run(self, query: str, parameters=None, **kwargs):
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
                # Handle semantic query with pattern matching
                matching_nodes = []
                logger.info(f"Searching nodes with params: {params}")
                logger.info(f"Current store nodes dict: {self.store.nodes}")
                logger.info(f"Available nodes: {[n['properties'] for n in self.store.nodes.values()]}")
                
                # Parse names from query if present
                names = None
                if "names" in params:
                    names = params["names"]
                    if not isinstance(names, list):
                        names = [names]
                    names = [str(name) for name in names]
                    logger.info(f"Searching for names: {names}")
                elif "n.name IN" in query:
                    # Extract names from the query string
                    names_str = query.split("n.name IN [")[1].split("]")[0]
                    names = [name.strip("'") for name in names_str.split(",")]
                    logger.info(f"Extracted names from query: {names}")
                
                for node in self.store.nodes.values():
                    props = node["properties"]
                    matches = True
                    logger.info(f"Checking node: {props}")
                    
                    # Check type if specified
                    if "type" in params:
                        if params["type"] == "concept":
                            # Allow both "concept" and "entity" types since consolidation uses "entity"
                            if props.get("type") not in ["concept", "entity"]:
                                matches = False
                                continue
                        elif params["type"] == "entity":
                            # Allow both "concept" and "entity" types since consolidation uses "entity"
                            if props.get("type") not in ["concept", "entity"]:
                                matches = False
                                continue
                        elif props.get("type") != params["type"]:
                            matches = False
                            continue
                    
                    # Check names list if present
                    if names is not None:
                        node_name = str(props.get("name", ""))
                        logger.info(f"Checking if node name '{node_name}' is in {names}")
                        if node_name not in names:
                            logger.info(f"Node name '{node_name}' not found in {names}, skipping")
                            matches = False
                            continue
                        else:
                            logger.info(f"Node name '{node_name}' found in {names}, including in results")
                    
                    # Check text or pattern if specified
                    elif "text" in params:
                        text = params["text"]
                        if text not in props.get("description", "") and text not in props.get("name", ""):
                            matches = False
                            continue
                    elif "pattern" in params:
                        pattern = params["pattern"]
                        if pattern not in props.get("description", "") and pattern not in props.get("name", ""):
                            matches = False
                            continue
                                
                    # Check context if specified
                    if "context" in params:
                        context = params["context"]
                        for key, value in context.items():
                            if key == "access_domain":
                                validation = props.get("validation", {})
                                if isinstance(validation, str):
                                    try:
                                        validation = json.loads(validation)
                                    except json.JSONDecodeError:
                                        validation = {}
                                if validation.get("access_domain") == value:
                                    continue
                                else:
                                    matches = False
                                    break
                            else:
                                if props.get(key) != value:
                                    matches = False
                                    break
                    
                    if matches:
                        # Process the node through ConceptStore's _process_concept_record
                        processed_node = {
                            "name": props["name"],
                            "type": props["type"],
                            "description": props.get("description", ""),
                            "is_consolidation": props.get("is_consolidation", False)
                        }
                        # Add validation if present
                        validation = props.get("validation")
                        if validation:
                            if isinstance(validation, str):
                                try:
                                    validation = json.loads(validation)
                                except json.JSONDecodeError:
                                    validation = {}
                            processed_node["validation"] = validation
                        matching_nodes.append({"n": processed_node})
                logger.info(f"Query returned nodes: {matching_nodes}")
                return MockAsyncResult(matching_nodes)
            elif "MERGE (c:Concept" in query:
                logger.info(f"Processing MERGE query with params: {params}")
                logger.info(f"Current store nodes dict before merge: {self.store.nodes}")
                
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
                logger.info(f"Extracted params: {params}")

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
                        logger.info(f"Created new node with ON CREATE SET: {existing_node}")
                    return MockAsyncResult([{"c": existing_node["properties"]}])
                else:
                    # Regular MERGE without ON CREATE SET
                    node = {
                        "name": params.get("name"),
                        "type": params.get("type", "concept"),
                        "description": params.get("description", ""),
                        "is_consolidation": params.get("is_consolidation", False),
                        "validation": params.get("validation", {})
                    }
                    
                    # Parse validation if it's a string
                    if isinstance(node["validation"], str):
                        try:
                            node["validation"] = json.loads(node["validation"])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse validation JSON: {node['validation']}")

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
                        logger.info(f"Created new node: {existing_node}")

                    # Update existing node properties
                    existing_node["properties"].update(node)
                    logger.info(f"Updated node properties: {existing_node['properties']}")
                    
                    # Add to store's nodes if not already there
                    if not any(n["properties"]["name"] == node["name"] for n in self.store.nodes.values()):
                        node_id = str(uuid.uuid4())
                        self.store.nodes[node_id] = {
                            "label": "Concept",
                            "properties": dict(node)
                        }
                        logger.info(f"Added new node to store with ID {node_id}: {self.store.nodes[node_id]}")
                    
                    logger.info(f"Final store nodes dict: {self.store.nodes}")
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
                    # Get parameters from parameters first, then kwargs
                    source_name = parameters.get("name") if parameters else kwargs.get("name")
                    related_names = parameters.get("related", []) if parameters else kwargs.get("related", [])
                    if isinstance(related_names, str):
                        related_names = [related_names]
                    elif not isinstance(related_names, list):
                        related_names = list(related_names)
                    
                    # Validate parameters
                    if not source_name or not related_names:
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
                        self.store.relationships.append(relationship)
                        
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
                    
                    # Create relationship
                    self.store.relationships.append({
                        "from": params.get("name"),
                        "to": params.get("related_name"),
                        "type": "RELATED_TO",
                        "properties": {}
                    })
                    
                    return MockAsyncResult([{"c": source_node["properties"], "r": target_node["properties"]}])
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
            logger.info("Initialized MockNeo4jStore with empty nodes dict")
            
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
            relationship = {
                "from": start_node,
                "to": end_node,
                "type": type,
                "properties": properties or {}
            }
            self.relationships.append(relationship)
            
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
    system = TwoLayerMemorySystem(neo4j_uri="bolt://127.0.0.1:7687", vector_store=mock_vector_store)
    system.semantic = SemanticLayer(mock_neo4j_store)
    system.consolidation_manager = ConsolidationManager(system.episodic, system.semantic)
    
    # Set up stores
    system.episodic.store = mock_vector_store
    system.semantic.driver = mock_neo4j_store
    
    # Add logging for semantic layer ID
    logger.info(f"Created memory system with semantic layer ID: {id(system.semantic)}")
    
    # Patch store_concept to add logging
    original_store_concept = system.semantic.store_concept
    async def logged_store_concept(*args, **kwargs):
        logger.info(f"Storing concept with args: {args}, kwargs: {kwargs}")
        result = await original_store_concept(*args, **kwargs)
        logger.info(f"Stored concept result: {result}")
        return result
    system.semantic.store_concept = logged_store_concept

    # Patch store_knowledge to add logging and implementation
    async def logged_store_knowledge(knowledge):
        logger.info(f"Storing knowledge with args: ({knowledge},) kwargs: {{}}")
        
        # Store concepts
        for concept in knowledge.get("concepts", []):
            logger.info(f"Storing concept: {concept}")
            await system.semantic.store_concept(
                name=concept["name"],
                type=concept["type"],
                description=concept["description"],
                validation=concept["validation"],
                is_consolidation=True
            )
            
        # Store relationships
        for rel in knowledge.get("relationships", []):
            logger.info(f"Storing relationship: {rel}")
            await system.semantic.run_query(
                """
                MERGE (c1:Concept {name: $from})
                MERGE (c2:Concept {name: $to})
                MERGE (c1)-[:RELATED_TO]->(c2)
                """,
                {"from": rel["from"], "to": rel["to"]}
            )
            
        logger.info(f"Stored knowledge result: None")
        return None
        
    system.semantic.store_knowledge = logged_store_knowledge
    
    return system

@pytest.fixture
def world(memory_system):
    """Create world environment for testing."""
    return NIAWorld(memory_system=memory_system)

@pytest.fixture
def nova(memory_system, world):
    """Create Nova orchestrator for testing."""
    nova = Nova(memory_system=memory_system, world=world)
    
    # Set up mock memory behaviors
    def create_memory_mock(content, memory_type="episodic", context=None, metadata=None, concepts=None, relationships=None):
        timestamp = format_timestamp()
        memory_dict = {
            "content": content,
            "type": memory_type,
            "timestamp": timestamp,
            "context": context or {},
            "metadata": metadata or {},
            "concepts": concepts or [],
            "relationships": relationships or [],
            "consolidated": False,
            "archived": False
        }
        
        memory = Mock(spec=EpisodicMemory)
        memory.content = content
        memory.type = memory_type
        memory.timestamp = timestamp
        memory.context = memory_dict["context"]
        memory.metadata = memory_dict["metadata"]
        memory.concepts = memory_dict["concepts"]
        memory.relationships = memory_dict["relationships"]
        memory.consolidated = False
        memory.archived = False
        memory.id = f"memory_{timestamp}"
        
        # Set up dictionary-like behavior
        memory.get = Mock(side_effect=memory_dict.get)
        memory.keys = Mock(return_value=list(memory_dict.keys()))
        memory.__getitem__ = lambda s, key: memory_dict[key]
        memory.__iter__ = lambda s: iter(memory_dict.items())
        memory.__contains__ = lambda s, key: key in memory_dict
        memory.__len__ = lambda s: len(memory_dict)
        memory.items = lambda: memory_dict.items()
        
        # Set up async behavior
        memory.__aiter__ = AsyncMock(return_value=memory_dict.items())
        memory.__await__ = AsyncMock(return_value=memory_dict)
        
        return memory
    
    nova.create_memory_mock = create_memory_mock
    
    return nova
