"""LLM interface and implementations for Nova."""

import aiohttp
import json
from typing import Dict, Any, Optional, Type, TypeVar, Union
from datetime import datetime
from .llm_types import (
    LLMProvider,
    LLMModel,
    LLMMessage,
    LLMConfig,
    LLMRequest,
    LLMResponse,
    LLMError,
    LLMErrorResponse,
    LLMConcept,
    LLMAnalysisResult,
    LLMAnalyticsResult
)

T = TypeVar('T')

class LLMInterface:
    """Base LLM interface."""
    
    async def analyze(
        self,
        content: Dict[str, Any],
        template: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content using specified template."""
        raise NotImplementedError

    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text from prompt."""
        raise NotImplementedError

    async def embed(
        self,
        text: str,
        **kwargs
    ) -> list[float]:
        """Generate embeddings for text."""
        raise NotImplementedError

    async def get_structured_completion(
        self,
        prompt: str,
        response_model: Type[T],
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> T:
        """Get structured completion from prompt."""
        raise NotImplementedError

class LMStudioLLM(LLMInterface):
    """LM Studio LLM implementation."""

    def __init__(
        self,
        chat_model: str,
        embedding_model: str,
        api_base: str = "http://localhost:1234/v1",
        **kwargs
    ):
        """Initialize LM Studio LLM."""
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.api_base = api_base.rstrip("/")
        self.config = LLMConfig(
            provider=LLMProvider.LMSTUDIO,
            model=LLMModel.CUSTOM,
            **kwargs
        )

    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make request to LM Studio API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/{endpoint}",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise LLMError(
                            code="API_ERROR",
                            message=f"LM Studio API error: {error}"
                        )
                    return await response.json()
            except aiohttp.ClientError as e:
                raise LLMError(
                    code="CONNECTION_ERROR",
                    message=f"Failed to connect to LM Studio API: {str(e)}"
                )

    def _get_agent_prompt(self, agent_type: str) -> str:
        """Get agent prompt from config."""
        from nia.config.agent_config import get_agent_prompt
        
        try:
            # Get agent-specific prompt
            module_path = f"nia.config.prompts.{agent_type}_agent"
            prompt_module = __import__(module_path, fromlist=[f"{agent_type.upper()}_AGENT_PROMPT"])
            agent_prompt = getattr(prompt_module, f"{agent_type.upper()}_AGENT_PROMPT")
            
            # Get base template with agent's responsibilities
            base_template = get_agent_prompt(
                agent_type=agent_type,
                domain="professional",  # Default to professional domain
                skills=None  # No specific skills needed for now
            )
            
            # Combine them
            return f"{base_template}\n\n{agent_prompt}"
        except (ImportError, AttributeError) as e:
            raise ValueError(f"No prompt found for agent type '{agent_type}': {str(e)}")

    def _create_chat_messages(
        self,
        content: Dict[str, Any],
        template: str
    ) -> list[Dict[str, str]]:
        """Create chat messages from content and template."""
        # Get agent type from template name
        agent_type = template.split("_")[0]  # e.g., "parsing" from "parsing_analysis"
        
        try:
            # Get combined prompt
            prompt = self._get_agent_prompt(agent_type)
            
            # Add content
            full_prompt = f"{prompt}\n\nContent to analyze: {json.dumps(content)}"
            
            return [
                {"role": "system", "content": full_prompt}
            ]
        except Exception as e:
            raise ValueError(f"Failed to create prompt for agent type '{agent_type}': {str(e)}")

    def _parse_chat_response(
        self,
        response: Dict[str, Any],
        template: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse chat completion response."""
        try:
            content_text = response["choices"][0]["message"]["content"]
            metadata = content.get("metadata", {})
            
            # Try to parse the response as JSON
            try:
                # Find the first { and last }
                start = content_text.find('{')
                end = content_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content_text[start:end]
                    parsed = json.loads(json_str)
                    
                    # Add metadata
                    if metadata:
                        parsed["metadata"] = {**parsed.get("metadata", {}), **metadata}
                    
                    # Convert to standard format
                    concepts = []
                    if "parsing" in parsed and "understanding" in parsed["parsing"]:
                        concepts = [
                            LLMConcept(
                                name=c,
                                type="concept",
                                description="",
                                related=[],
                                confidence=parsed["metadata"].get("confidence", 1.0)
                            )
                            for c in parsed["parsing"]["understanding"].get("concepts", [])
                        ]
                    
                    return LLMAnalysisResult(
                        response=content_text,
                        concepts=concepts,
                        key_points=parsed.get("evaluation", {}).get("key_points", []),
                        implications=[],
                        uncertainties=parsed.get("evaluation", {}).get("uncertainties", []),
                        reasoning=[],
                        confidence=parsed.get("metadata", {}).get("confidence", 1.0),
                        metadata=metadata
                    ).dict()
                else:
                    raise ValueError("No JSON object found in response")
            except (json.JSONDecodeError, ValueError) as e:
                raise LLMError(
                    code="PARSING_ERROR",
                    message=f"Failed to parse structured response: {str(e)}",
                    details={"response": content_text}
                )
                
        except Exception as e:
            # Return error response
            error_concept = LLMConcept(
                name="error",
                type="error",
                description=str(e),
                confidence=0.0
            )
            
            return LLMAnalysisResult(
                response="Error analyzing content",
                concepts=[error_concept],
                key_points=["Error occurred during analysis"],
                implications=[],
                uncertainties=[],
                reasoning=[str(e)],
                confidence=0.0,
                metadata=content.get("metadata", {})
            ).dict()

    async def analyze(
        self,
        content: Dict[str, Any],
        template: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content using specified template."""
        try:
            messages = self._create_chat_messages(content, template)
            
            payload = {
                "model": self.chat_model,
                "messages": messages,
                **kwargs
            }
            
            response = await self._make_request("chat/completions", payload)
            return self._parse_chat_response(response, template, content)
        except Exception as e:
            # Return error response
            error_concept = LLMConcept(
                name="error",
                type="error",
                description=str(e),
                confidence=0.0
            )
            
            return LLMAnalysisResult(
                response="Error analyzing content",
                concepts=[error_concept],
                key_points=["Error occurred during analysis"],
                implications=[],
                uncertainties=[],
                reasoning=[str(e)],
                confidence=0.0,
                metadata=content.get("metadata", {})
            ).dict()

    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text from prompt."""
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        response = await self._make_request("chat/completions", payload)
        return response["choices"][0]["message"]["content"]

    async def embed(
        self,
        text: str,
        **kwargs
    ) -> list[float]:
        """Generate embeddings for text."""
        payload = {
            "model": self.embedding_model,
            "input": text,
            **kwargs
        }
        
        response = await self._make_request("embeddings", payload)
        return response["data"][0]["embedding"]

    async def get_structured_completion(
        self,
        prompt: str,
        response_model: Type[T],
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> T:
        """Get structured completion from prompt."""
        system_prompt = (
            "You are an AI assistant that provides responses in a specific structured format. "
            "Follow the response format exactly as specified."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": self.chat_model,
            "messages": messages,
            **kwargs
        }
        
        try:
            response = await self._make_request("chat/completions", payload)
            content = response["choices"][0]["message"]["content"]
            
            # Try to parse the response as JSON
            structured_response = json.loads(content)
            
            # Add metadata if provided
            if metadata:
                structured_response["metadata"] = metadata
            
            # Convert to response model
            return response_model(**structured_response)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return error response
            raise LLMError(
                code="PARSING_ERROR",
                message="Failed to parse response as JSON",
                details={"response": content}
            )
        except Exception as e:
            raise LLMError(
                code="COMPLETION_ERROR",
                message=f"Error getting structured completion: {str(e)}"
            )
