"""LLM interface and implementations for Nova."""

import aiohttp
import json
import asyncio
from typing import Dict, Any, Optional, Type, TypeVar, Union, AsyncGenerator, AsyncIterator
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
        chat_model: str = "llama-3.2-3b-instruct",
        embedding_model: str = "text-embedding-nomic-embed-text-v1.5@f16",
        api_base: str = "http://localhost:1234/v1",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream_chunk_size: int = 8,
        **kwargs
    ):
        """Initialize LM Studio LLM.
        
        Args:
            chat_model: Model to use for chat/completion (default: llama-3.2-3b-instruct)
            embedding_model: Model to use for embeddings (default: text-embedding-nomic-embed-text-v1.5@f16)
            api_base: Base URL for LM Studio API
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            stream_chunk_size: Number of tokens per streaming chunk
            **kwargs: Additional configuration options
        """
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.api_base = api_base.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream_chunk_size = stream_chunk_size
        self.config = LLMConfig(
            provider=LLMProvider.LMSTUDIO,
            model=LLMModel.CUSTOM,
            **kwargs
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """Make request to LM Studio API."""
        session = await self._ensure_session()
        try:
            # Add streaming parameter if needed
            if stream:
                payload["stream"] = True
                
            async with session.post(
                f"{self.api_base}/{endpoint}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise LLMError(
                        code="API_ERROR",
                        message=f"LM Studio API error: {error}"
                    )
                
                if stream:
                    return self._stream_chunks(response)
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise LLMError(
                code="CONNECTION_ERROR",
                message=f"Failed to connect to LM Studio API: {str(e)}"
            )

    async def _stream_chunks(
        self,
        response: aiohttp.ClientResponse
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream response chunks."""
        try:
            async for line in response.content:
                if line:
                    try:
                        chunk = json.loads(line.decode())
                        if chunk.get("choices") and chunk["choices"][0].get("delta"):
                            yield {
                                "type": "llm_chunk",
                                "data": {
                                    "content": chunk["choices"][0]["delta"].get("content", ""),
                                    "is_final": chunk.get("finish_reason") is not None
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
        except Exception as e:
            yield {
                "type": "error",
                "data": {
                    "code": "STREAM_ERROR",
                    "message": f"Error streaming response: {str(e)}"
                },
                "timestamp": datetime.now().isoformat()
            }

    async def _collect_stream(
        self,
        stream: AsyncIterator[Dict[str, Any]]
    ) -> str:
        """Collect streaming response into a single string."""
        chunks = []
        async for chunk in stream:
            if chunk["type"] == "error":
                raise LLMError(
                    code=chunk["data"]["code"],
                    message=chunk["data"]["message"]
                )
            chunks.append(chunk["data"]["content"])
        return "".join(chunks)

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
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """Analyze content using specified template."""
        try:
            messages = self._create_chat_messages(content, template)
            
            payload = {
                "model": self.chat_model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream_chunk_size": self.stream_chunk_size if stream else None,
                **kwargs
            }
            
            response = await self._make_request("chat/completions", payload, stream=stream)
            
            if isinstance(response, AsyncIterator):
                return response
            
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
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncIterator[Dict[str, Any]]]:
        """Generate text from prompt."""
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream_chunk_size": self.stream_chunk_size if stream else None,
            **kwargs
        }
        
        response = await self._make_request("chat/completions", payload, stream=stream)
        
        if isinstance(response, AsyncIterator):
            return response
            
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
        if isinstance(response, AsyncIterator):
            raise LLMError(
                code="INVALID_RESPONSE",
                message="Received streaming response for embeddings request"
            )
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
            if isinstance(response, AsyncIterator):
                content = await self._collect_stream(response)
            else:
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

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
