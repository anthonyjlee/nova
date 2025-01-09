"""Basic memory system integration tests."""

import pytest
from datetime import datetime, timezone

async def test_basic_concept_storage_and_retrieval(memory_system):
    """Test storing and retrieving a basic concept."""
    # Store a concept
    concept_name = "test_concept"
    concept_type = "entity"
    concept_description = "A test concept"
    
    stored_concept = await memory_system.semantic.store_concept(
        name=concept_name,
        type=concept_type,
        description=concept_description,
        validation={
            "domain": "professional",
            "access_domain": "professional",
            "confidence": 0.9,
            "source": "test",
            "approved": True,
            "cross_domain": {
                "approved": True,
                "requested": True,
                "source_domain": "professional",
                "target_domain": "professional",
                "justification": "Test justification"
            }
        }
    )
    
    assert stored_concept is not None
    assert stored_concept["n"]["name"] == concept_name
    assert stored_concept["n"]["type"] == concept_type
    assert stored_concept["n"]["description"] == concept_description
    
    # Retrieve the concept
    retrieved_concept = await memory_system.semantic.get_concept(concept_name)
    assert retrieved_concept is not None
    assert retrieved_concept["n"]["name"] == concept_name
    assert retrieved_concept["n"]["type"] == concept_type
    assert retrieved_concept["n"]["description"] == concept_description
    assert retrieved_concept["n"]["validation"]["domain"] == "professional"
    assert retrieved_concept["n"]["validation"]["approved"] is True
