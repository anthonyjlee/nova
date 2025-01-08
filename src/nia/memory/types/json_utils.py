"""JSON utilities for memory types."""

from typing import Any, Dict
import json

def validate_json_structure(data: Any) -> bool:
    """Validate that data is JSON serializable."""
    try:
        # Try to serialize to JSON
        json.dumps(data)
        return True
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data is not JSON serializable: {str(e)}")

def validate_json_object(data: Dict) -> bool:
    """Validate that data is a valid JSON object."""
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
        
    try:
        # Try to serialize to JSON
        json.dumps(data)
        return True
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data is not a valid JSON object: {str(e)}")

def validate_json_array(data: list) -> bool:
    """Validate that data is a valid JSON array."""
    if not isinstance(data, list):
        raise ValueError("Data must be a list")
        
    try:
        # Try to serialize to JSON
        json.dumps(data)
        return True
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data is not a valid JSON array: {str(e)}")
