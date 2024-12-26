"""JSON validation utilities."""

import logging
from typing import Dict, List, Union
from .extraction import extract_json_from_lmstudio

logger = logging.getLogger(__name__)

def validate_json_structure(data: Union[str, Dict]) -> Union[Dict, List[Dict]]:
    """Validate and normalize JSON data structure."""
    if isinstance(data, str):
        data = extract_json_from_lmstudio(data)
    
    # Handle direct concept data
    if all(key in data for key in ["name", "type", "description"]):
        from ..concept_utils.validation import validate_concept_structure
        return validate_concept_structure(data)
    
    # Handle array of concepts
    if "concepts" in data and isinstance(data["concepts"], list):
        from ..concept_utils.validation import validate_concept_structure
        concepts = []
        for concept in data["concepts"]:
            concepts.append(validate_concept_structure(concept))
        return concepts
    
    # Try extracting concepts from response
    from ..concept_utils.extraction import extract_concepts_from_response
    concepts = extract_concepts_from_response(data)
    
    if not concepts:
        raise ValueError("No valid concepts found in response")
    
    return concepts[0] if len(concepts) == 1 else concepts
