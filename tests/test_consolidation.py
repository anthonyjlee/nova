"""Test memory consolidation functionality."""

import pytest
from src.nia.memory.neo4j_store import Neo4jMemoryStore

@pytest.fixture
async def store():
    """Create a Neo4j store for testing."""
    store = Neo4jMemoryStore()
    yield store
    await store.clear_concepts()
    await store.close()

@pytest.mark.asyncio
async def test_store_consolidated_concept(store):
    """Test storing a consolidated concept."""
    # Store a consolidated concept
    await store.store_concept(
        name="test_consolidated",
        type="test",
        description="A test consolidated concept",
        validation={"confidence": 0.8},
        is_consolidation=True
    )
    
    # Verify the concept was stored with consolidation flag
    concept = await store.get_concept("test_consolidated")
    assert concept is not None
    assert concept["is_consolidation"] is True
    assert concept["validation"]["confidence"] == 0.8

@pytest.mark.asyncio
async def test_store_regular_concept(store):
    """Test storing a regular (non-consolidated) concept."""
    # Store a regular concept
    await store.store_concept(
        name="test_regular",
        type="test",
        description="A test regular concept",
        validation={"confidence": 0.5}
    )
    
    # Verify the concept was stored without consolidation flag
    concept = await store.get_concept("test_regular")
    assert concept is not None
    assert concept["is_consolidation"] is False
    assert concept["validation"]["confidence"] == 0.5

@pytest.mark.asyncio
async def test_get_concepts_by_type_consolidation(store):
    """Test getting concepts by type includes consolidation status."""
    # Store both types of concepts
    await store.store_concept(
        name="consolidated_1",
        type="test_type",
        description="Consolidated concept 1",
        is_consolidation=True
    )
    await store.store_concept(
        name="regular_1",
        type="test_type",
        description="Regular concept 1",
        is_consolidation=False
    )
    
    # Get concepts by type
    concepts = await store.get_concepts_by_type("test_type")
    assert len(concepts) == 2
    
    # Verify consolidation status is correct
    consolidated = [c for c in concepts if c["is_consolidation"]]
    regular = [c for c in concepts if not c["is_consolidation"]]
    assert len(consolidated) == 1
    assert len(regular) == 1
    assert consolidated[0]["name"] == "consolidated_1"
    assert regular[0]["name"] == "regular_1"

@pytest.mark.asyncio
async def test_get_related_concepts_consolidation(store):
    """Test getting related concepts includes consolidation status."""
    # Store related concepts
    await store.store_concept(
        name="parent",
        type="test",
        description="Parent concept",
        related=["child_consolidated", "child_regular"]
    )
    await store.store_concept(
        name="child_consolidated",
        type="test",
        description="Consolidated child concept",
        is_consolidation=True
    )
    await store.store_concept(
        name="child_regular",
        type="test",
        description="Regular child concept",
        is_consolidation=False
    )
    
    # Get related concepts
    related = await store.get_related_concepts("parent")
    assert len(related) == 2
    
    # Verify consolidation status is correct
    consolidated = [c for c in related if c["is_consolidation"]]
    regular = [c for c in related if not c["is_consolidation"]]
    assert len(consolidated) == 1
    assert len(regular) == 1
    assert consolidated[0]["name"] == "child_consolidated"
    assert regular[0]["name"] == "child_regular"

@pytest.mark.asyncio
async def test_search_concepts_consolidation(store):
    """Test searching concepts includes consolidation status."""
    # Store concepts to search
    await store.store_concept(
        name="searchable_consolidated",
        type="test",
        description="A searchable consolidated concept",
        is_consolidation=True
    )
    await store.store_concept(
        name="searchable_regular",
        type="test",
        description="A searchable regular concept",
        is_consolidation=False
    )
    
    # Search for concepts
    results = await store.search_concepts("searchable")
    assert len(results) == 2
    
    # Verify consolidation status is correct
    consolidated = [c for c in results if c["is_consolidation"]]
    regular = [c for c in results if not c["is_consolidation"]]
    assert len(consolidated) == 1
    assert len(regular) == 1
    assert consolidated[0]["name"] == "searchable_consolidated"
    assert regular[0]["name"] == "searchable_regular"

@pytest.mark.asyncio
async def test_store_concept_from_json_consolidation(store):
    """Test storing concepts from JSON with consolidation."""
    # Test JSON data
    json_data = {
        "concepts": [
            {
                "name": "json_consolidated",
                "type": "test",
                "description": "A consolidated concept from JSON",
                "is_consolidation": True,
                "validation": {"confidence": 0.8}
            },
            {
                "name": "json_regular",
                "type": "test",
                "description": "A regular concept from JSON",
                "validation": {"confidence": 0.5}
            }
        ]
    }
    
    # Store concepts from JSON
    await store.store_concept_from_json(json_data)
    
    # Verify consolidated concept
    consolidated = await store.get_concept("json_consolidated")
    assert consolidated is not None
    assert consolidated["is_consolidation"] is True
    assert consolidated["validation"]["confidence"] == 0.8
    
    # Verify regular concept
    regular = await store.get_concept("json_regular")
    assert regular is not None
    assert regular["is_consolidation"] is False
    assert regular["validation"]["confidence"] == 0.5

@pytest.mark.asyncio
async def test_consolidation_with_validation(store):
    """Test consolidated concepts with full validation data."""
    validation_data = {
        "confidence": 0.9,
        "uncertainties": ["uncertainty1", "uncertainty2"],
        "supported_by": ["evidence1", "evidence2"],
        "contradicted_by": ["counter1"],
        "needs_verification": ["verify1"]
    }
    
    # Store concept with validation
    await store.store_concept(
        name="validated_consolidated",
        type="test",
        description="A consolidated concept with validation",
        validation=validation_data,
        is_consolidation=True
    )
    
    # Verify concept and validation data
    concept = await store.get_concept("validated_consolidated")
    assert concept is not None
    assert concept["is_consolidation"] is True
    assert concept["validation"]["confidence"] == 0.9
    assert len(concept["validation"]["uncertainties"]) == 2
    assert len(concept["validation"]["supported_by"]) == 2
    assert len(concept["validation"]["contradicted_by"]) == 1
    assert len(concept["validation"]["needs_verification"]) == 1

@pytest.mark.asyncio
async def test_consolidation_edge_cases(store):
    """Test edge cases and error handling for consolidation."""
    # Test updating consolidation status
    await store.store_concept(
        name="update_test",
        type="test",
        description="Test concept",
        is_consolidation=False
    )
    
    # Update to consolidated
    await store.store_concept(
        name="update_test",
        type="test",
        description="Test concept",
        is_consolidation=True,
        validation={"confidence": 0.8}
    )
    
    # Verify update
    concept = await store.get_concept("update_test")
    assert concept is not None
    assert concept["is_consolidation"] is True
    assert concept["validation"]["confidence"] == 0.8
    
    # Test invalid confidence values
    with pytest.raises(Exception):
        await store.store_concept(
            name="invalid_confidence",
            type="test",
            description="Test concept",
            is_consolidation=True,
            validation={"confidence": 1.5}  # Invalid confidence > 1.0
        )
    
    # Test empty validation with consolidation
    await store.store_concept(
        name="empty_validation",
        type="test",
        description="Test concept",
        is_consolidation=True
    )
    
    concept = await store.get_concept("empty_validation")
    assert concept is not None
    assert concept["is_consolidation"] is True
    assert "validation" not in concept  # No validation data

@pytest.mark.asyncio
async def test_batch_consolidation(store):
    """Test batch operations with consolidation."""
    # Create test data
    concepts = [
        {
            "name": f"batch_concept_{i}",
            "type": "test",
            "description": f"Batch concept {i}",
            "is_consolidation": i % 2 == 0,  # Alternate between consolidated/regular
            "validation": {"confidence": 0.8 if i % 2 == 0 else 0.5}
        }
        for i in range(10)
    ]
    
    # Store concepts in batch
    for concept in concepts:
        await store.store_concept(
            name=concept["name"],
            type=concept["type"],
            description=concept["description"],
            is_consolidation=concept["is_consolidation"],
            validation=concept["validation"]
        )
    
    # Verify all concepts
    for concept in concepts:
        stored = await store.get_concept(concept["name"])
        assert stored is not None
        assert stored["is_consolidation"] == concept["is_consolidation"]
        assert stored["validation"]["confidence"] == concept["validation"]["confidence"]
    
    # Search and verify batch results
    results = await store.search_concepts("batch_concept")
    assert len(results) == 10
    
    # Verify consolidation distribution
    consolidated = [r for r in results if r["is_consolidation"]]
    regular = [r for r in results if not r["is_consolidation"]]
    assert len(consolidated) == 5  # Half should be consolidated
    assert len(regular) == 5  # Half should be regular
    
    # Verify confidence levels
    for concept in consolidated:
        assert concept["validation"]["confidence"] == 0.8
    for concept in regular:
        assert concept["validation"]["confidence"] == 0.5
