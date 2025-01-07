"""Schema definitions for structured LLM output."""

import outlines
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, constr

class Concept(BaseModel):
    """A concept extracted from content."""
    name: str = Field(..., description="Name or title of the concept")
    type: str = Field(..., description="Type of concept")
    description: str = Field(..., description="Description of the concept")
    related: List[str] = Field(..., description="List of related concepts")

class Response(BaseModel):
    """Structured response from LLM."""
    response: str = Field(..., description="The main response text")
    concepts: List[Concept] = Field(..., description="List of concepts extracted from the content")
    key_points: List[str] = Field(..., description="List of key points from the content")
    implications: List[str] = Field(..., description="List of implications")
    uncertainties: List[str] = Field(..., description="List of uncertainties")
    reasoning: List[str] = Field(..., description="List of reasoning steps")

# Legacy JSON schema for backward compatibility
response_schema = {
    "type": "object",
    "properties": {
        "response": {
            "type": "string",
            "description": "The main response text"
        },
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name or title of the concept"
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of concept"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the concept"
                    },
                    "related": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Related concept"
                        },
                        "description": "List of related concepts"
                    }
                },
                "required": ["name", "type", "description", "related"]
            },
            "description": "List of concepts extracted from the content"
        },
        "key_points": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "Key point"
            },
            "description": "List of key points from the content"
        },
        "implications": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "Implication"
            },
            "description": "List of implications"
        },
        "uncertainties": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "Uncertainty"
            },
            "description": "List of uncertainties"
        },
        "reasoning": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "Reasoning step"
            },
            "description": "List of reasoning steps"
        }
    },
    "required": ["response", "concepts", "key_points", "implications", "uncertainties", "reasoning"]
}
