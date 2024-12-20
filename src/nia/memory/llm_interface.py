"""LLM interface for structured completions."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
from .memory_types import AgentResponse
from .agents.parsing_agent import ParsingAgent

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for LLM operations."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1234,
        max_retries: int = 3
    ):
        """Initialize LLM interface."""
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.parser = None  # Will be initialized after Neo4j and vector stores
    
    def initialize_parser(self, store, vector_store):
        """Initialize parsing agent."""
        self.parser = ParsingAgent(self, store, vector_store)
    
    async def get_completion(self, prompt: str) -> str:
        """Get completion from LLM."""
        try:
            # Format request
            request = {
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            }
            
            # Try to get completion with retries
            for attempt in range(self.max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"http://{self.host}:{self.port}/v1/completions",
                            json=request,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                if "choices" in result and result["choices"]:
                                    return result["choices"][0]["text"].strip()
                            else:
                                error_text = await response.text()
                                logger.error(f"LLM API error: {error_text}")
                                
                except aiohttp.ClientError as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Retrying after error: {str(e)}")
                    continue
            
            logger.error("Failed to get completion after retries")
            return ""
            
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            return ""
    
    async def get_structured_completion(
        self,
        prompt: str,
        expected_format: Optional[Dict] = None
    ) -> AgentResponse:
        """Get structured completion from LLM."""
        try:
            # Add format instructions if provided
            if expected_format:
                prompt = f"""
                {prompt}
                
                Return response in this exact format:
                {json.dumps(expected_format, indent=2)}
                
                Return ONLY the JSON object, no other text.
                """
            
            # Get completion
            completion = await self.get_completion(prompt)
            
            # Parse structured response
            if self.parser:
                return await self.parser.parse_text(completion)
            
            # Fallback if parser not initialized
            return AgentResponse(
                response=completion,
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="raw",
                confidence=0.5,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting structured completion: {str(e)}")
            return AgentResponse(
                response="Error getting structured completion",
                concepts=[],
                perspective="error",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        expected_format: Optional[Dict] = None
    ) -> AgentResponse:
        """Get chat completion from LLM."""
        try:
            # Format request
            request = {
                "messages": messages,
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            }
            
            # Add format instructions if provided
            if expected_format:
                request["messages"].append({
                    "role": "system",
                    "content": f"""
                    Return response in this exact format:
                    {json.dumps(expected_format, indent=2)}
                    
                    Return ONLY the JSON object, no other text.
                    """
                })
            
            # Try to get completion with retries
            for attempt in range(self.max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"http://{self.host}:{self.port}/v1/chat/completions",
                            json=request,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                if "choices" in result and result["choices"]:
                                    completion = result["choices"][0]["message"]["content"].strip()
                                    
                                    # Parse structured response
                                    if self.parser:
                                        return await self.parser.parse_text(completion)
                                    
                                    # Fallback if parser not initialized
                                    return AgentResponse(
                                        response=completion,
                                        concepts=[],
                                        key_points=[],
                                        implications=[],
                                        uncertainties=[],
                                        reasoning=[],
                                        perspective="raw",
                                        confidence=0.5,
                                        timestamp=datetime.now()
                                    )
                            else:
                                error_text = await response.text()
                                logger.error(f"LLM API error: {error_text}")
                                
                except aiohttp.ClientError as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Retrying after error: {str(e)}")
                    continue
            
            logger.error("Failed to get chat completion after retries")
            return AgentResponse(
                response="Failed to get chat completion",
                concepts=[],
                perspective="error",
                confidence=0.0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            return AgentResponse(
                response="Error getting chat completion",
                concepts=[],
                perspective="error",
                confidence=0.0,
                timestamp=datetime.now()
            )
