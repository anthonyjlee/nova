"""Concept validation utilities."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def validate_concept_structure(data: Dict) -> Dict:
    """Validate and normalize a single concept structure."""
    if not isinstance(data, dict):
        raise ValueError("Concept data must be a dictionary")
    
    required_fields = ["name", "type", "description"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields in concept: {', '.join(missing_fields)}")
    
    concept = {
        "name": str(data["name"]).strip(),
        "type": str(data["type"]).strip(),
        "description": str(data["description"]).strip()
    }
    
    if not concept["name"]:
        raise ValueError("Name must be a non-empty string")
    # Validate concept type
    valid_types = ["entity", "action", "property", "event", "abstract"]
    if not concept["type"]:
        raise ValueError("Type must be a non-empty string")
    if concept["type"] not in valid_types:
        raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
    if not concept["description"]:
        raise ValueError("Description must be a non-empty string")
    
    if "related" in data:
        if not isinstance(data["related"], list):
            raise ValueError("Related must be a list")
        concept["related"] = [
            str(r).strip() for r in data["related"]
            if isinstance(r, (str, int, float)) and str(r).strip()
        ]
    
    validation = {}
    
    if "validation" in data:
        if not isinstance(data["validation"], dict):
            raise ValueError("Validation must be a dictionary")
            
        validation_data = data["validation"]
        
        # Validate confidence
        if "confidence" in validation_data:
            try:
                confidence = float(validation_data["confidence"])
                if not 0 <= confidence <= 1:
                    raise ValueError("Confidence must be between 0 and 1")
                validation["confidence"] = confidence
            except (TypeError, ValueError):
                raise ValueError("Confidence must be between 0 and 1")
        else:
            validation["confidence"] = 0.9  # Default confidence
        
        # Validate source and domain fields
        validation["source"] = str(validation_data.get("source", "professional"))
        validation["access_domain"] = str(validation_data.get("access_domain", "professional"))
        validation["domain"] = str(validation_data.get("domain", "professional"))
            
        # Validate cross_domain data
        cross_domain = validation_data.get("cross_domain", {})
        if not isinstance(cross_domain, dict):
            cross_domain = {}
            
        validation["cross_domain"] = {
            "approved": bool(cross_domain.get("approved", True)),
            "requested": bool(cross_domain.get("requested", True)),
            "source_domain": str(cross_domain.get("source_domain", "professional")),
            "target_domain": str(cross_domain.get("target_domain", "general")),
            "justification": str(cross_domain.get("justification", "Test justification"))
        }
        
        # Validate list fields with defaults
        for field in ["supported_by", "contradicted_by", "needs_verification"]:
            if field in validation_data:
                if not isinstance(validation_data[field], list):
                    raise ValueError(f"{field} must be a list")
                validation[field] = [
                    str(item).strip() 
                    for item in validation_data[field]
                    if isinstance(item, (str, int, float)) and str(item).strip()
                ]
            else:
                validation[field] = []  # Default empty list
    else:
        # Set default validation data
        validation = {
            "confidence": 0.9,
            "source": "professional",
            "access_domain": "professional",
            "domain": "professional",
            "supported_by": [],
            "contradicted_by": [],
            "needs_verification": [],
            "cross_domain": {
                "approved": True,
                "requested": True,
                "source_domain": "professional",
                "target_domain": "general",
                "justification": "Test justification"
            }
        }
    
    if "uncertainties" in data:
        if isinstance(data["uncertainties"], list):
            validation["uncertainties"] = [
                str(item).strip() 
                for item in data["uncertainties"]
                if isinstance(item, (str, int, float)) and str(item).strip()
            ]
        elif isinstance(data["uncertainties"], str):
            validation["uncertainties"] = [str(data["uncertainties"]).strip()]
    
    concept["validation"] = validation
    
    return concept
