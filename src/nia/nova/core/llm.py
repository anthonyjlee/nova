"""LM Studio integration for Nova."""

import aiohttp
import json
from typing import Dict, Any, Optional, Union
from .models import AnalysisResponse, AnalyticsResponse, LLMErrorResponse

class LMStudioLLM:
    """LM Studio integration for language model capabilities."""
    
    def __init__(
        self,
        chat_model: str,
        embedding_model: str,
        api_base: str = "http://localhost:1234/v1"
    ):
        """Initialize LM Studio integration."""
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.api_base = api_base
        
    async def get_structured_completion(
        self,
        prompt: str,
        response_model: Any,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
        max_tokens: int = 1000
    ) -> Union[AnalysisResponse, AnalyticsResponse, LLMErrorResponse]:
        """Get structured completion from LM Studio using outlines."""
        try:
            from openai import OpenAI
            import outlines
            
            # Create OpenAI client for LMStudio
            client = OpenAI(
                base_url=self.api_base,
                api_key="lm-studio"  # LMStudio accepts any non-empty string
            )
            
            # Create generator with response model
            generator = outlines.generate.json(client, response_model)
            
            # Generate structured response
            result = generator(prompt)
            
            # Add metadata if provided
            if metadata and isinstance(result, dict):
                result["metadata"] = metadata
                
            return result
        except Exception as e:
            raise Exception(f"LM Studio error: {str(e)}")

    async def analyze(
        self,
        content: Dict[str, Any],
        template: str = "parsing_analysis",
        max_tokens: int = 1000
    ) -> Union[AnalysisResponse, AnalyticsResponse, LLMErrorResponse]:
        """Analyze content using LM Studio."""
        try:
            from openai import OpenAI
            
            # Extract text from content
            text = content.get("text", "")
            if isinstance(text, dict):
                text = str(text)
            
            # Create OpenAI client for LMStudio
            client = OpenAI(
                base_url=self.api_base,
                api_key="lm-studio"  # LMStudio accepts any non-empty string
            )
            
            # Prepare prompt based on template
            prompt = self._prepare_prompt({"text": text, "metadata": content.get("metadata", {})}, template)
            
            # Get completion from LM Studio
            response = client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # If response is not valid JSON, return error
                return {
                    "response": "Error: Invalid JSON response",
                    "concepts": [{
                        "name": "Error",
                        "type": "error",
                        "description": "Failed to parse JSON response",
                        "confidence": 0.0
                    }],
                    "key_points": ["Error parsing response"],
                    "implications": ["Analysis failed"],
                    "uncertainties": ["Response format"],
                    "reasoning": ["Invalid JSON"]
                }
            
            # Add metadata if provided
            if content.get("metadata"):
                result["metadata"] = content["metadata"]
                
            return result
            
        except Exception as e:
            # Return error response
            return {
                "response": "Error analyzing content",
                "concepts": [{
                    "name": "Error",
                    "type": "error",
                    "description": str(e),
                    "confidence": 0.0
                }],
                "key_points": ["Error occurred during analysis"],
                "implications": ["Analysis failed"],
                "uncertainties": ["Error cause"],
                "reasoning": ["Error handling"]
            }
            
    def _prepare_prompt(self, content: Dict[str, Any], template: str) -> str:
        """Prepare prompt based on template."""
        if template == "analytics_processing":
            return f"""Analyze the following content and generate analytics insights. Return the result as a JSON object with the following structure:
{{
    "response": "Your analysis here",
    "confidence": 0.95
}}

Content to analyze:
{content.get("text", str(content))}

Domain: {content["metadata"].get("domain", "general")}

Important: Your response must be a complete, well-formed JSON object following exactly this structure. The confidence value should be a number between 0 and 1.
"""
        elif template == "parsing_analysis":
            return f"""Analyze the following text and extract structured information. Return the result as a JSON object with the following structure:
{{
    "response": "Your analysis here",
    "concepts": [
        {{
            "name": "concept name",
            "type": "concept type",
            "description": "concept description",
            "related": ["related concept 1", "related concept 2"]
        }}
    ],
    "key_points": ["key point 1", "key point 2"],
    "implications": ["implication 1", "implication 2"],
    "uncertainties": ["uncertainty 1", "uncertainty 2"],
    "reasoning": ["reasoning step 1", "reasoning step 2"]
}}

Text to analyze:
{content["text"]}

Domain: {content["metadata"].get("domain", "general")}

Important: Your response must be a complete, well-formed JSON object following exactly this structure.
"""
        else:
            raise ValueError(f"Unknown template: {template}")
