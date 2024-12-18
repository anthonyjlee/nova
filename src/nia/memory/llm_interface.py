"""Enhanced LLM interface implementation with agent-based parsing."""

import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from .memory_types import AgentResponse
from .interfaces import LLMInterfaceBase

logger = logging.getLogger(__name__)

class LLMInterface(LLMInterfaceBase):
    """Interface to LLM API with agent-based parsing."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:1234",
        model: str = "text-embedding-nomic-embed-text-v1.5@q8_0"
    ):
        """Initialize LLM interface."""
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.session = None
        # Parser will be initialized when needed
        self._parser = None
    
    @property
    def parser(self) -> Any:
        """Get or create parsing agent."""
        if self._parser is None:
            # Import here to avoid circular imports
            from .neo4j_store import Neo4jMemoryStore
            from .vector_store import VectorStore
            from .agents.parsing_agent import ParsingAgent
            
            # Create parser with same LLM interface
            self._parser = ParsingAgent(
                llm=self,
                store=Neo4jMemoryStore(),  # Could be passed in if needed
                vector_store=VectorStore(None)  # Could be passed in if needed
            )
        return self._parser
    
    async def get_completion(self, prompt: str) -> str:
        """Get raw text completion."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/chat/completions",
                    json={
                        "messages": [
                            {"role": "system", "content": "You are a helpful AI assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    }
                ) as response:
                    result = await response.json()
                    
                    # Handle different response formats
                    if "choices" in result and result["choices"]:
                        if "message" in result["choices"][0]:
                            return result["choices"][0]["message"]["content"]
                        elif "text" in result["choices"][0]:
                            return result["choices"][0]["text"]
                    
                    # If we can't find the expected format, log the response and return empty
                    logger.error(f"Unexpected response format: {result}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            return ""
    
    async def get_structured_completion(self, prompt: str) -> AgentResponse:
        """Get structured completion using parsing agent."""
        try:
            # Get raw completion
            completion = await self.get_completion(prompt)
            
            # If completion is empty, return error response
            if not completion:
                return AgentResponse(
                    response="Error: No completion received from LLM",
                    concepts=[],
                    key_points=[],
                    implications=[],
                    uncertainties=[],
                    reasoning=[],
                    timestamp=datetime.now()
                )
            
            # Parse response using agent
            response = await self.parser.parse_text(completion)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting structured completion: {str(e)}")
            return AgentResponse(
                response=f"Error getting completion: {str(e)}",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                timestamp=datetime.now()
            )
    
    async def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for text."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/embeddings",
                    json={
                        "model": self.model,
                        "input": text
                    }
                ) as response:
                    result = await response.json()
                    
                    # Handle different response formats
                    if "data" in result and result["data"]:
                        if "embedding" in result["data"][0]:
                            return result["data"][0]["embedding"]
                    
                    # If we can't find embeddings, log and return default
                    logger.error(f"Unexpected embeddings response format: {result}")
                    return [0.0] * 384  # Default embedding size
                    
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            return [0.0] * 384  # Default embedding size
    
    async def get_batch_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/embeddings",
                    json={
                        "model": self.model,
                        "input": texts
                    }
                ) as response:
                    result = await response.json()
                    
                    # Handle different response formats
                    if "data" in result:
                        return [data.get("embedding", [0.0] * 384) for data in result["data"]]
                    
                    # If we can't find embeddings, log and return defaults
                    logger.error(f"Unexpected batch embeddings response format: {result}")
                    return [[0.0] * 384 for _ in texts]
                    
        except Exception as e:
            logger.error(f"Error getting batch embeddings: {str(e)}")
            return [[0.0] * 384 for _ in texts]  # Default embedding size
    
    async def extract_concepts(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract concepts from text using parsing agent."""
        try:
            # Format prompt
            prompt = """Extract key concepts from the text.
            Provide concepts in this exact format:
            [
              {
                "name": "Concept name",
                "type": "Concept type",
                "description": "Clear description",
                "related": ["Related concept names"]
              }
            ]
            
            Text: {text}
            """.format(text=text)
            
            if context:
                prompt += "\nContext: " + json.dumps(context)
            
            # Get concepts through parsing agent
            response = await self.parser.parse_text(
                await self.get_completion(prompt)
            )
            
            return response.concepts
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            return []
    
    def close(self) -> None:
        """Close LLM interface."""
        if self.session:
            self.session.close()

async def extract_structured_content(text: str) -> Dict[str, Any]:
    """Extract structured content from text using parsing agent.
    
    This function is maintained for backwards compatibility.
    New code should use ParsingAgent directly.
    """
    try:
        # Create LLM interface
        llm = LLMInterface()
        
        # Use parsing agent to extract content
        response = await llm.parser.parse_text(text)
        
        # Convert to expected format
        return {
            "concepts": response.concepts,
            "key_points": response.key_points,
            "implications": response.implications,
            "uncertainties": response.uncertainties,
            "reasoning": response.reasoning
        }
    except Exception as e:
        logger.error(f"Error extracting structured content: {str(e)}")
        return {
            "concepts": [],
            "key_points": [],
            "implications": [],
            "uncertainties": [],
            "reasoning": []
        }
