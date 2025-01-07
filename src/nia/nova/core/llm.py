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
        """Analyze content using LM Studio and outlines."""
        try:
            from openai import OpenAI
            import outlines
            from pydantic import BaseModel, Field
            from typing import List
            
            # Extract text from content
            text = content.get("text", "")
            if isinstance(text, dict):
                text = str(text)
            
            from .models import LLMAnalyticsResult, LLMAnalysisResult
            
            # Select response model based on template
            response_model = LLMAnalyticsResult if template == "analytics_processing" else LLMAnalysisResult
            
            # Create OpenAI client for LMStudio
            client = OpenAI(
                base_url=self.api_base,
                api_key="lm-studio"  # LMStudio accepts any non-empty string
            )
            
            # Create generator with response model
            generator = outlines.generate.json(client, response_model)
            
            # Prepare prompt based on template
            prompt = self._prepare_prompt({"text": text, "metadata": content.get("metadata", {})}, template)
            
            # Generate structured response
            result = generator(prompt)
            
            # Add metadata if provided
            if content.get("metadata"):
                result_dict = result.model_dump()
                result_dict["metadata"] = content["metadata"]
                return result_dict
                
            return result.model_dump()
            
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
    "confidence": confidence_score
}}

Content to analyze:
{content.get("text", str(content))}

Domain: {content["metadata"].get("domain", "general")}
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
