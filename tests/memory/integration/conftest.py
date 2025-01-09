"""Shared fixtures for memory integration tests."""

import pytest
import uuid
import json
import re
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

from nia.core.types.memory_types import (
    Memory, MemoryType, EpisodicMemory, MockMemory,
    Concept, Relationship, DomainContext, BaseDomain, KnowledgeVertical,
    ValidationSchema, CrossDomainSchema
)
from nia.core.neo4j.concept_store import ConceptStore
from nia.memory.two_layer import TwoLayerMemorySystem, SemanticLayer
from nia.memory.consolidation import ConsolidationManager
from nia.world.environment import NIAWorld
from nia.nova.orchestrator import Nova
from .mock_vector_store import MockVectorStore

class MockRecord:
    """Mock Neo4j record that provides dictionary-like access."""
    
    def __init__(self, data: dict):
        """Initialize with record data."""
        self._data = data
        
    def __getitem__(self, key):
        """Support dictionary-style access."""
        return self._data[key]
        
    def get(self, key, default=None):
        """Support get with default."""
        return self._data.get(key, default)

class MockResult:
    """Mock Neo4j result that never does network IO."""
    
    def __init__(self, records=None):
        """Initialize with optional records."""
        self._records = [MockRecord(r) for r in (records or [])]
        logger.info(f"MockResult initialized with {len(self._records)} records")
        if self._records:
            logger.info(f"First record: {json.dumps(self._records[0]._data, indent=2)}")
        
    def __iter__(self):
        """Support iteration over records."""
        return iter(self._records)
        
    async def single(self, default=None):
        """Get single record."""
        if self._records:
            logger.info(f"Returning single record: {json.dumps(self._records[0]._data, indent=2)}")
            return self._records[0]
        logger.info(f"No records found, returning default: {default}")
        return default
        
    def single_record(self):
        """Get single record synchronously."""
        if self._records:
            logger.info(f"Returning single record: {json.dumps(self._records[0]._data, indent=2)}")
            return self._records[0]
        logger.info("No records found")
        return None
        
    async def consume(self):
        """No-op consume."""
        logger.info(f"Consuming {len(self._records)} records")
        return {"summary": {"counters": {"nodes-created": len(self._records)}}}
        
    def consume_sync(self):
        """No-op consume synchronously."""
        logger.info(f"Consuming {len(self._records)} records")
        return {"summary": {"counters": {"nodes-created": len(self._records)}}}
        
    def data(self):
        """Get raw record data."""
        data = [r._data for r in self._records]
        logger.info(f"Returning {len(data)} records: {json.dumps(data, indent=2)}")
        return data
        
    def validate_records(self):
        """Validate record structure."""
        for i, record in enumerate(self._records):
            if not isinstance(record._data, dict):
                logger.error(f"Record {i} is not a dictionary: {record._data}")
                return False
            if "n" not in record._data:
                logger.error(f"Record {i} missing 'n' key: {record._data}")
                return False
            if "relationships" not in record._data:
                logger.error(f"Record {i} missing 'relationships' key: {record._data}")
                return False
        logger.info("All records validated successfully")
        return True

class MockSession:
    """Mock Neo4j session that never does network IO."""
    
    def __init__(self, store):
        """Initialize mock session."""
        self.store = store
        logger.info("MockSession initialized")
        
    async def __aenter__(self):
        """Context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
        
    async def run(self, query: str, parameters: dict = None):
        """Mock query execution that returns results from store."""
        logger.info(f"MockSession.run() called with query: {query}")
        results = await self.store._query(query, parameters or {})
        return MockResult(results)
        
    def close(self):
        """No-op close."""
        pass

class MockDriver:
    """Mock Neo4j driver that never does network IO."""
    
    def __init__(self, store):
        """Initialize with store reference."""
        self.store = store
        logger.info("MockDriver initialized")
        
    def session(self, database=None, default_access_mode=None):
        """Create a mock session with store reference."""
        logger.info(f"MockDriver.session() called with database={database}")
        return MockSession(self.store)
        
    async def close(self):
        """No-op close."""
        logger.info("MockDriver.close() called")
        pass
        
    async def verify_connectivity(self):
        """No-op connectivity check."""
        logger.info("MockDriver.verify_connectivity() called")
        return True

def finalize_validation(validation: Any) -> dict:
    """Convert validation schema to dictionary with consistent structure."""
    # If already a dict, ensure required fields
    if isinstance(validation, dict):
        return {
            "domain": validation.get("domain", "professional"),
            "access_domain": validation.get("access_domain", "professional"),
            "confidence": validation.get("confidence", 0.9),
            "source": validation.get("source", "test"),
            "approved": validation.get("approved", True),
            "cross_domain": validation.get("cross_domain", {
                "approved": True,
                "requested": True,
                "source_domain": "professional",
                "target_domain": "professional",
                "justification": "Test justification"
            })
        }
    
    # If string, try to parse as JSON
    if isinstance(validation, str):
        try:
            return finalize_validation(json.loads(validation))
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse validation JSON: {validation}")
            return finalize_validation({})
    
    # If ValidationSchema, convert to dict and ensure all nested schemas are also converted
    if isinstance(validation, ValidationSchema):
        validation_dict = validation.dict()
        # Convert any nested schemas to dicts
        for key, value in validation_dict.items():
            if isinstance(value, (ValidationSchema, CrossDomainSchema)):
                validation_dict[key] = value.dict()
            elif isinstance(value, list):
                validation_dict[key] = [
                    item.dict() if isinstance(item, (ValidationSchema, CrossDomainSchema)) else item
                    for item in value
                ]
        # Add required fields that might be missing
        validation_dict.update({
            "approved": validation_dict.get("approved", True),
            "requested": validation_dict.get("requested", True),
            "source_domain": validation_dict.get("source_domain", "professional"),
            "target_domain": validation_dict.get("target_domain", "professional"),
            "justification": validation_dict.get("justification", "Test justification")
        })
        return validation_dict
    
    # Default validation
    return finalize_validation({})

class MockNeo4jStore(ConceptStore):
    """Mock Neo4j store for testing."""
    
    def __init__(self, uri="bolt://localhost:7687", *args, **kwargs):
        """Initialize mock store."""
        super().__init__(uri=uri)  # Initialize parent first
        self.nodes = {}  # In-memory storage
        self.relationships = []  # In-memory relationships
        self._driver = None  # Initialize driver as None
        self._uri = uri  # Store URI as protected attribute
        logger.info(f"Initialized MockNeo4jStore with URI: {uri}")

    @property
    def uri(self):
        """Get the Neo4j URI."""
        return self._uri

    @uri.setter
    def uri(self, value):
        """Set the Neo4j URI."""
        self._uri = value

    @property
    def driver(self):
        """Get the Neo4j driver instance."""
        if self._driver is None:
            self._driver = MockDriver(self)
        return self._driver

    @driver.setter
    def driver(self, value):
        """Set the Neo4j driver instance."""
        self._driver = value
        
    async def connect(self):
        """Override connect to prevent real connection attempts."""
        logger.info("MockNeo4jStore.connect() called - no real connection needed")
        return True
        
    async def close(self):
        """Override close to prevent real connection cleanup."""
        logger.info("MockNeo4jStore.close() called - no real connection to close")
        return True
        
    async def disconnect(self):
        """Alias for close() to maintain compatibility."""
        return await self.close()
        
    async def _ensure_indexes(self):
        """No-op for mock."""
        return True
        
    async def store_concept(self, *args, **kwargs) -> dict | None:
        """Store a concept with validation."""
        # Extract parameters
        name = kwargs.get("name")
        type = kwargs.get("type")
        description = kwargs.get("description", "")
        validation = kwargs.get("validation", {})
        
        # Convert validation to consistent dictionary
        validation_dict = finalize_validation(validation)
            
        # Store validation both as individual fields and complete JSON
        node = {
            # Core fields
            "name": name,
            "type": type,
            "description": description,
            
            # Required top-level fields
            "domain": validation_dict["domain"],
            "domains": [validation_dict["domain"]],  # Required for pattern matching
            "from": name,  # Required for relationship pattern matching
            "to": name,    # Required for relationship pattern matching
            
            # Validation data
            "validation": validation_dict,  # Complete JSON
            "validation_json": json.dumps(validation_dict),  # Backup JSON string
            
            # Individual validation fields at top level for direct access
            "access_domain": validation_dict["access_domain"],
            "confidence": validation_dict["confidence"],
            "source": validation_dict["source"],
            "approved": validation_dict["approved"],
            "cross_domain": validation_dict["cross_domain"],
            
            # Additional required fields
            "is_consolidation": kwargs.get("is_consolidation", False),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Storing concept node: {json.dumps(node, indent=2)}")
        
        try:
            # Store node
            self.nodes[name] = node
            logger.info(f"Successfully stored concept: {name}")
            logger.info(f"Concept validation data: {json.dumps(node['validation'], indent=2)}")
            
            # Ensure validation is a dictionary
            if isinstance(node["validation"], ValidationSchema):
                node["validation"] = node["validation"].dict()
            elif isinstance(node["validation"], str):
                node["validation"] = json.loads(node["validation"])
                
            return {"n": node, "relationships": []}
        except Exception as e:
            logger.error(f"Failed to store concept {name}: {str(e)}")
            raise
        
    async def store_relationship(self, source: str, target: str, rel_type: str = "RELATED_TO", bidirectional: bool = True) -> None:
        """Store a relationship between concepts."""
        try:
            # Create validation data
            validation_dict = finalize_validation({
                "domain": "professional",
                "approved": True,
                "cross_domain": {
                    "approved": True,
                    "requested": True,
                    "source_domain": "professional",
                    "target_domain": "professional",
                    "justification": "Test justification"
                }
            })
            
            # Create relationship with all required fields
            rel = {
                # Core fields
                "type": rel_type,
                
                # Required source/target fields (both naming conventions)
                "source": source,  # For episodic layer
                "target": target,
                "from": source,    # For semantic layer
                "to": target,
                
                # Required domain fields
                "domain": validation_dict["domain"],
                "domains": ["professional"],  # Required field
                
                # Validation data
                "validation": validation_dict,  # Complete JSON
                "validation_json": json.dumps(validation_dict),  # Backup JSON string
                
                # Individual validation fields at top level
                "access_domain": validation_dict["access_domain"],
                "confidence": validation_dict["confidence"],
                "source": validation_dict["source"],
                "approved": validation_dict["approved"],
                "cross_domain": validation_dict["cross_domain"],
                
                # Additional required fields
                "bidirectional": bidirectional,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_consolidation": True  # Mark as consolidated relationship
            }
            
            # Ensure validation is a dictionary
            if isinstance(rel["validation"], ValidationSchema):
                rel["validation"] = rel["validation"].dict()
            elif isinstance(rel["validation"], str):
                rel["validation"] = json.loads(rel["validation"])
            logger.info(f"Creating relationship: {json.dumps(rel, indent=2)}")
            logger.info(f"Relationship validation data: {json.dumps(rel['validation'], indent=2)}")
            self.relationships.append(rel)
        
            # Create reverse relationship if bidirectional
            if bidirectional:
                reverse_rel = {
                    "source": target,  # Keep source/target for episodic layer
                    "target": source,
                    "from": target,    # Add from/to for semantic layer
                    "to": source,
                    "type": rel_type,
                    "domains": ["professional"],  # Required field
                    "validation": validation_dict,  # Complete JSON
                    "validation_json": json.dumps(validation_dict),  # Backup JSON string
                    "domain": validation_dict["domain"],  # Individual fields
                    "access_domain": validation_dict["access_domain"],
                    "confidence": validation_dict["confidence"],
                    "approved": validation_dict["approved"]
                }
                logger.info(f"Creating reverse relationship: {json.dumps(reverse_rel, indent=2)}")
                self.relationships.append(reverse_rel)
                
            logger.info(f"Successfully created relationship from {source} to {target}")
        except Exception as e:
            logger.error(f"Failed to create relationship from {source} to {target}: {str(e)}")
            raise
            
    async def _query(self, query: str, params: dict = None) -> List[Dict]:
        """Execute query and return results."""
        logger.info(f"Query: {query}, params: {params}")
        params = params or {}
        
        try:
            # Handle concept search by name
            if "WHERE c.name = $query" in query or "WHERE n.name = $query" in query:
                name = params.get("query")
                if name in self.nodes:
                    node = self.nodes[name]
                    relationships = self._get_relationships_for_node(name)
                    logger.info(f"Found concept by name: {name}")
                    key = "c" if "WHERE c.name" in query else "n"
                    # Match Neo4j record structure expected by SemanticLayer
                    processed_node = {
                        "name": node["name"],
                        "type": node["type"],
                        "description": node.get("description", ""),
                        "validation": node["validation"],
                        "validation_json": node.get("validation_json", json.dumps(node["validation"])),
                        "is_consolidation": node.get("is_consolidation", False),
                        "relationships": relationships
                    }
                    return [processed_node]
                return []
            
            # Handle concept search by pattern
            elif "MATCH (n:Concept)" in query or "MATCH (c:Concept)" in query:
                results = []
                pattern = params.get("pattern", ".*")
                logger.info(f"Searching for concepts matching pattern: {pattern}")
                
                for name, node in self.nodes.items():
                    if re.match(pattern, node.get("name", "")):  # Match against node's name property
                        logger.info(f"Found matching node: {name}")
                        relationships = self._get_relationships_for_node(name)
                        key = "c" if "MATCH (c:Concept)" in query else "n"
                        
                        # Ensure validation is a dictionary
                        if isinstance(node.get("validation"), ValidationSchema):
                            node["validation"] = node["validation"].dict()
                        elif isinstance(node.get("validation"), str):
                            node["validation"] = json.loads(node["validation"])
                        
                        # Ensure validation in relationships
                        for rel in relationships:
                            if isinstance(rel.get("validation"), ValidationSchema):
                                rel["validation"] = rel["validation"].dict()
                            elif isinstance(rel.get("validation"), str):
                                rel["validation"] = json.loads(rel["validation"])
                        
                        # Match Neo4j record structure expected by SemanticLayer
                        processed_node = {
                            "name": node["name"],
                            "type": node["type"],
                            "description": node.get("description", ""),
                            "validation": node["validation"],
                            "validation_json": node.get("validation_json", json.dumps(node["validation"])),
                            "is_consolidation": node.get("is_consolidation", False),
                            "relationships": relationships
                        }
                        logger.info(f"Created result record: {json.dumps(processed_node, indent=2)}")
                        results.append(processed_node)
                
                logger.info(f"Returning {len(results)} results")
                return results
            
            # Handle relationship creation
            elif "MERGE (c1:Concept" in query or "CREATE (c1:Concept" in query:
                # Just return empty result for relationship creation
                return []
            
            # Handle get concepts by type
            elif "WHERE n.type = $type" in query or "WHERE c.type = $type" in query:
                results = []
                type_value = params.get("type")
                for node in self.nodes.values():
                    if node.get("type") == type_value:
                        relationships = self._get_relationships_for_node(node["name"])
                        key = "c" if "WHERE c.type" in query else "n"
                        # Match Neo4j record structure expected by SemanticLayer
                        processed_node = {
                            "name": node["name"],
                            "type": node["type"],
                            "description": node.get("description", ""),
                            "validation": node["validation"],
                            "validation_json": node.get("validation_json", json.dumps(node["validation"])),
                            "is_consolidation": node.get("is_consolidation", False),
                            "relationships": relationships
                        }
                        results.append(processed_node)
                return results
            
            # Default case
            logger.info("Query did not match any known patterns")
            return []
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
            
    def _get_relationships_for_node(self, node_name: str) -> List[Dict]:
        """Get relationships for a node."""
        relationships = []
        for rel in self.relationships:
            if rel["source"] == node_name or rel["from"] == node_name:
                logger.info(f"Found outgoing relationship: {rel['type']} -> {rel['to']}")
                # Ensure validation is a dictionary
                validation = rel["validation"]
                if isinstance(validation, ValidationSchema):
                    validation = validation.dict()
                elif isinstance(validation, str):
                    validation = json.loads(validation)
                    
                relationships.append({
                    "name": rel["to"],
                    "type": rel["type"],
                    "domains": rel["domains"],
                    "validation": validation,
                    "domain_context": {
                        "primary_domain": validation["domain"],
                        "knowledge_vertical": "general"
                    },
                    "is_consolidation": True
                })
            elif (rel["target"] == node_name or rel["to"] == node_name) and rel.get("bidirectional", True):
                logger.info(f"Found incoming relationship: {rel['from']} -> {rel['type']}")
                # Ensure validation is a dictionary
                validation = rel["validation"]
                if isinstance(validation, ValidationSchema):
                    validation = validation.dict()
                elif isinstance(validation, str):
                    validation = json.loads(validation)
                    
                relationships.append({
                    "name": rel["from"],
                    "type": rel["type"],
                    "domains": rel["domains"],
                    "validation": validation,
                    "domain_context": {
                        "primary_domain": validation["domain"],
                        "knowledge_vertical": "general"
                    },
                    "is_consolidation": True
                })
        return relationships

@pytest.fixture(scope="function")
def mock_vector_store():
    """Mock vector store for testing."""
    return MockVectorStore()

@pytest.fixture(scope="function")
def mock_neo4j_store():
    """Mock Neo4j store fixture."""
    return MockNeo4jStore()

@pytest.fixture(scope="function", autouse=True)
async def memory_system(mock_vector_store, mock_neo4j_store, event_loop):
    """Create memory system with mock stores."""
    # Use mock store's URI property
    system = TwoLayerMemorySystem(neo4j_uri=mock_neo4j_store.uri, vector_store=mock_vector_store)
    system.semantic = SemanticLayer(mock_neo4j_store)
    system.consolidation_manager = ConsolidationManager(system.episodic, system.semantic)
    
    # Set up stores
    system.episodic.store = mock_vector_store
    system.semantic.driver = mock_neo4j_store
    
    # Initialize system
    await system.initialize()
    
    logger.info(f"Created memory system with mock stores. Neo4j URI: {mock_neo4j_store.uri}")
    yield system
    
    # Cleanup
    await system.cleanup()

@pytest.fixture(scope="function", autouse=True)
async def world(memory_system, event_loop):
    """Create world environment for testing."""
    world = NIAWorld(memory_system=memory_system)
    yield world

@pytest.fixture(scope="function", autouse=True)
async def nova(memory_system, world, event_loop):
    """Create Nova orchestrator for testing."""
    nova = Nova(memory_system=memory_system, world=world)
    
    # Set up mock memory behaviors
    def create_memory_mock(content, memory_type="episodic", context=None, metadata=None, concepts=None, relationships=None):
        """Create a mock memory using MockMemory class."""
        # Create validation with consistent structure
        validation_dict = finalize_validation({
            "domain": "professional",
            "access_domain": "professional",
            "confidence": 0.9,
            "source": "professional",
            "supported_by": [],
            "contradicted_by": [],
            "needs_verification": [],
            "cross_domain": {
                "approved": True,
                "requested": True,
                "source_domain": "professional",
                "target_domain": "professional",
                "justification": "Test justification"
            },
            "approved": True
        })

        # Create validation schema from dict
        validation = ValidationSchema(**validation_dict)

        # Create domain context
        domain_context = DomainContext(
            primary_domain="professional",
            knowledge_vertical="general",
            validation=validation
        )

        # Create memory instance
        memory = MockMemory(
            content=content,
            type=memory_type,
            timestamp=datetime.now(timezone.utc),
            context=context or {},
            metadata=metadata or {},
            concepts=concepts or [],
            relationships=relationships or [],
            consolidated=False,
            domain_context=domain_context,
            validation=validation,
            validation_data=validation_dict  # Use finalized validation dict
        )

        memory.id = f"memory_{datetime.now(timezone.utc).isoformat()}"
        return memory
    
    nova.create_memory_mock = create_memory_mock
    return nova
