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
    if not concept["type"]:
        raise ValueError("Type must be a non-empty string")
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
    
    if "validation" in data and isinstance(data["validation"], dict):
        if "confidence" in data["validation"]:
            confidence = float(data["validation"]["confidence"])
            if not 0 <= confidence <= 1:
                raise Exception("Confidence must be between 0 and 1")
            validation["confidence"] = confidence
        
        for field in ["supported_by", "contradicted_by", "needs_verification"]:
            if field in data["validation"]:
                if isinstance(data["validation"][field], list):
                    validation[field] = [
                        str(item).strip() 
                        for item in data["validation"][field]
                        if isinstance(item, (str, int, float)) and str(item).strip()
                    ]
    
    if "uncertainties" in data:
        if isinstance(data["uncertainties"], list):
            validation["uncertainties"] = [
                str(item).strip() 
                for item in data["uncertainties"]
                if isinstance(item, (str, int, float)) and str(item).strip()
            ]
        elif isinstance(data["uncertainties"], str):
            validation["uncertainties"] = [str(data["uncertainties"]).strip()]
    
    if validation:
        concept["validation"] = validation
    
    return concept
