"""Utilities for working with concepts."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ConceptValidationError(Exception):
    """Error raised when concept validation fails."""
    pass

class ConceptAttributes(BaseModel):
    """Model for concept attributes."""
    domain: Optional[str] = None
    category: Optional[str] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

def validate_concept_structure(concept: Dict[str, Any]) -> bool:
    """Validate concept structure."""
    required_fields = ["name", "type"]
    for field in required_fields:
        if field not in concept:
            raise ConceptValidationError(f"Missing required field: {field}")
            
    # Validate name
    if not isinstance(concept["name"], str):
        raise ConceptValidationError("Name must be a string")
    if not concept["name"].strip():
        raise ConceptValidationError("Name cannot be empty")
        
    # Validate type
    if not isinstance(concept["type"], str):
        raise ConceptValidationError("Type must be a string")
    if not concept["type"].strip():
        raise ConceptValidationError("Type cannot be empty")
        
    # Validate attributes if present
    if "attributes" in concept:
        if not isinstance(concept["attributes"], dict):
            raise ConceptValidationError("Attributes must be a dictionary")
        try:
            ConceptAttributes(**concept["attributes"])
        except Exception as e:
            raise ConceptValidationError(f"Invalid attributes: {str(e)}")
            
    # Validate relationships if present
    if "relationships" in concept:
        if not isinstance(concept["relationships"], list):
            raise ConceptValidationError("Relationships must be a list")
        for rel in concept["relationships"]:
            if not isinstance(rel, dict):
                raise ConceptValidationError("Each relationship must be a dictionary")
            if "type" not in rel:
                raise ConceptValidationError("Each relationship must have a type")
            if "target" not in rel:
                raise ConceptValidationError("Each relationship must have a target")
                
    return True

def merge_concepts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two concept dictionaries."""
    result = base.copy()
    
    # Update basic fields
    for field in ["type", "description"]:
        if field in update:
            result[field] = update[field]
            
    # Merge attributes
    if "attributes" in update:
        if "attributes" not in result:
            result["attributes"] = {}
        result["attributes"].update(update["attributes"])
        
    # Merge relationships
    if "relationships" in update:
        if "relationships" not in result:
            result["relationships"] = []
        # Add only new relationships
        existing_rels = {(r["type"], r["target"]) for r in result["relationships"]}
        for rel in update["relationships"]:
            if (rel["type"], rel["target"]) not in existing_rels:
                result["relationships"].append(rel)
                
    # Update timestamp
    result["updated_at"] = datetime.now().isoformat()
    
    return result
