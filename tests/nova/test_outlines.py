"""Test Outlines JSON generation and prompt templating."""

import pytest
import outlines
from openai import OpenAI
from nia.nova.core.models import LLMAnalysisResult, LLMAnalyticsResult

@outlines.prompt
def analysis_prompt(question: str) -> None:
    """You are a scientific analysis assistant.
    
    Analyze the following question and provide a structured response in JSON format with these fields:
    {
        "response": "A clear explanation",
        "concepts": [
            {
                "name": "Concept 1 Name",
                "type": "Physics/Chemistry/etc",
                "description": "Detailed description of the concept",
                "related": ["Related concept 1", "Related concept 2"]
            }
        ],
        "key_points": ["Important point 1", "Important point 2"],
        "implications": ["Implication 1", "Implication 2"],
        "uncertainties": ["Uncertainty 1", "Uncertainty 2"],
        "reasoning": ["Step 1", "Step 2"]
    }
    
    Make sure each concept in the concepts array has all required fields: name, type, description, and related.
    
    Question: {{ question }}
    """

@pytest.mark.asyncio
async def test_analysis_generation():
    """Test structured analysis generation with Outlines."""
    # Initialize OpenAI client for LMStudio
    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio"  # LMStudio accepts any non-empty string
    )
    
    # Generate prompt using template
    prompt = analysis_prompt("Why is the sky blue?")
    
    # Generate response
    response = client.chat.completions.create(
        model="llama-3.2-3b-instruct",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant that always responds in valid JSON format."
        }, {
            "role": "user",
            "content": str(prompt)
        }],
        max_tokens=1000,
        temperature=0.7,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "response": {"type": "string"},
                        "concepts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "related": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "key_points": {"type": "array", "items": {"type": "string"}},
                        "implications": {"type": "array", "items": {"type": "string"}},
                        "uncertainties": {"type": "array", "items": {"type": "string"}},
                        "reasoning": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["response", "concepts", "key_points", "implications", "uncertainties", "reasoning"]
                }
            }
        }
    )
    
    # Print response for debugging
    print(f"Raw response: {response.choices[0].message.content}")
    
    # Parse response into Pydantic model
    result = LLMAnalysisResult.model_validate_json(response.choices[0].message.content)
    
    # Verify result is a Pydantic model
    assert isinstance(result, LLMAnalysisResult)
    
    # Verify all required fields are present with expected types
    assert isinstance(result.response, str)
    assert isinstance(result.concepts, list)
    assert isinstance(result.key_points, list)
    assert isinstance(result.implications, list)
    assert isinstance(result.uncertainties, list)
    assert isinstance(result.reasoning, list)
    
    # Verify each concept has required fields
    for concept in result.concepts:
        assert isinstance(concept.name, str)
        assert isinstance(concept.type, str)
        assert isinstance(concept.description, str)
        assert isinstance(concept.related, list)

@outlines.prompt
def analytics_prompt(data: str) -> None:
    """You are a data analytics assistant.
    
    Analyze the following data and provide a structured response in JSON format with these fields:
    {
        "response": "A clear analysis of the data",
        "confidence": 0.95  # A confidence score between 0 and 1
    }
    
    Data: {{ data }}
    """

@pytest.mark.asyncio
async def test_analytics_generation():
    """Test structured analytics generation with Outlines."""
    # Initialize OpenAI client for LMStudio
    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio"  # LMStudio accepts any non-empty string
    )
    
    # Generate prompt using template
    prompt = analytics_prompt("User engagement increased by 25% in Q4 2024")
    
    # Generate response
    response = client.chat.completions.create(
        model="llama-3.2-3b-instruct",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant that always responds in valid JSON format."
        }, {
            "role": "user",
            "content": str(prompt)
        }],
        max_tokens=1000,
        temperature=0.7,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "response": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["response", "confidence"]
                }
            }
        }
    )
    
    # Parse response into Pydantic model
    result = LLMAnalyticsResult.model_validate_json(response.choices[0].message.content)
    
    # Verify result is a Pydantic model
    assert isinstance(result, LLMAnalyticsResult)
    
    # Verify all required fields are present with expected types
    assert isinstance(result.response, str)
    assert isinstance(result.confidence, float)
    
    # Verify confidence is between 0 and 1
    assert 0.0 <= result.confidence <= 1.0
