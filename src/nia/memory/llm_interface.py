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
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            return ""
    
    async def get_structured_completion(self, prompt: str) -> AgentResponse:
        """Get structured completion using parsing agent."""
        try:
            # Get raw completion
            completion = await self.get_completion(prompt)
            
            # Parse response using agent
            response = await self.parser.parse_text(completion)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting structured completion: {str(e)}")
            return AgentResponse(
                response="Error getting completion",
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
                    return result["data"][0]["embedding"]
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
                    return [data["embedding"] for data in result["data"]]
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
