"""
LLM interface implementation.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
from .memory_types import AgentResponse

logger = logging.getLogger(__name__)

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

def extract_json_from_response(text: str) -> str:
    """Extract JSON content from response, handling code blocks."""
    # Remove code block markers if present
    text = text.replace("```json", "").replace("```", "").strip()
    
    # Find start of JSON array
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array found in response")
    
    # Find end of JSON array
    end = text.rfind("]")
    if end == -1:
        raise ValueError("Unclosed JSON array in response")
    
    return text[start:end+1]

class LLMInterface:
    """Interface to LLM API."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:1234",
        model: str = "text-embedding-nomic-embed-text-v1.5@q8_0"
    ):
        """Initialize LLM interface."""
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.session = None
    
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
        """Get structured completion with concepts."""
        try:
            # Get raw completion
            completion = await self.get_completion(prompt)
            
            # Extract concepts list from completion
            try:
                # Extract and parse JSON content
                concepts_json = extract_json_from_response(completion)
                concepts = json.loads(concepts_json)
                
                # Convert concepts to standard format
                formatted_concepts = []
                for concept in concepts:
                    # Handle both name/CONCEPT formats
                    name = concept.get("name", concept.get("CONCEPT", ""))
                    type_str = concept.get("type", concept.get("TYPE", ""))
                    desc = concept.get("description", concept.get("DESC", ""))
                    related = concept.get("related_concepts", concept.get("RELATED", "").split())
                    
                    # Ensure related is a list
                    if isinstance(related, str):
                        related = related.split()
                    
                    formatted_concepts.append({
                        "name": name,
                        "type": type_str,
                        "description": desc,
                        "related": related
                    })
                
                # Create response
                return AgentResponse(
                    response=completion,
                    concepts=formatted_concepts,
                    timestamp=datetime.now()
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing concepts JSON: {str(e)}")
                logger.error(f"Raw JSON content: {concepts_json}")
                # Return empty concepts on parse error
                return AgentResponse(
                    response=completion,
                    concepts=[],
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error getting structured completion: {str(e)}")
            return AgentResponse(
                response="Error getting completion",
                concepts=[],
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
            # Return zero vector on error
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
            # Return zero vectors on error
            return [[0.0] * 384 for _ in texts]  # Default embedding size
    
    async def extract_concepts(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract concepts from text."""
        try:
            # Format prompt
            prompt = """Extract key concepts from the text.
            Include:
            1. Name of concept
            2. Type (technology, capability, system, idea)
            3. Description
            4. Related concepts
            
            Text: {text}
            
            Respond in JSON format with a list of concepts.
            """.format(text=text)
            
            if context:
                prompt += "\nContext: " + json.dumps(context)
            
            # Get structured completion
            response = await self.get_structured_completion(prompt)
            
            # Return concepts
            return response.concepts
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            return []
    
    def close(self) -> None:
        """Close LLM interface."""
        if self.session:
            self.session.close()
