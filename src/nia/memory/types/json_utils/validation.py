"""JSON validation utilities."""

import logging
from typing import Dict, List, Union
from .extraction import extract_json_from_lmstudio

logger = logging.getLogger(__name__)

def validate_json_structure(data: Union[str, Dict]) -> Union[Dict, List[Dict]]:
    """Validate and normalize JSON data structure."""
    if isinstance(data, str):
        data = extract_json_from_lmstudio(data)
    
    if not isinstance(data, (dict, list)):
        raise ValueError("Data must be a dictionary or list")

    def validate_value(value):
        """Validate a single value is JSON serializable."""
        if isinstance(value, (dict, list)):
            return validate_json_structure(value)
        elif isinstance(value, (str, int, float, bool, type(None))):
            return value
        else:
            raise ValueError(f"Value of type {type(value)} is not JSON serializable")

    if isinstance(data, dict):
        return {k: validate_value(v) for k, v in data.items()}
    else:  # list
        return [validate_value(item) for item in data]
