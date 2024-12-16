"""LLM interface for structured completions."""

import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class LLMResponse:
    """Structured LLM response."""
    
    def __init__(
        self,
        concepts: List[Dict[str, str]]
    ):
        """Initialize response."""
        self.concepts = concepts
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "concepts": self.concepts
        }

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:1234/v1/chat/completions",
        api_key: Optional[str] = None
    ):
        """Initialize LLM interface."""
        self.api_url = api_url
        self.api_key = api_key
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON content from text."""
        try:
            # Remove code block markers and any text before/after JSON array
            text = text.replace("```", "").strip()
            
            # Find JSON array between [ and ]
            matches = re.findall(r'\[(.*?)\]', text, re.DOTALL)
            if not matches:
                raise ValueError("No JSON array found")
            
            # Take the longest match (most likely the concepts array)
            json_str = max(matches, key=len)
            
            # Wrap in array brackets
            json_str = f"[{json_str}]"
            
            # Fix missing commas between objects
            json_str = re.sub(r'}\s*{', '},{', json_str)
            
            # Fix missing quotes around property names
            json_str = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', json_str)
            
            # Fix missing commas after values
            json_str = re.sub(r'"\s*{', '",{', json_str)
            json_str = re.sub(r'}\s*"', '},"', json_str)
            
            # Parse JSON
            data = json.loads(json_str)
            logger.debug(f"Parsed JSON array: {json.dumps(data, indent=2)}")
            return {"concepts": data}
            
        except Exception as e:
            logger.error(f"Failed to extract JSON: {str(e)}")
            logger.debug(f"Failed text: {text}")
            return {"concepts": []}
    
    def _format_concepts(self, concepts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format concepts into standard structure."""
        formatted = []
        for concept in concepts:
            # Handle both CONCEPT/TYPE and name/type formats
            name = concept.get("CONCEPT") or concept.get("name", "")
            type_str = concept.get("TYPE") or concept.get("type", "Unknown")
            desc = concept.get("DESC") or concept.get("description", "")
            related = concept.get("RELATED") or concept.get("related", "")
            
            # Convert related to list if it's a string
            if isinstance(related, str):
                related = [r.strip() for r in related.split(",")]
            
            formatted.append({
                "name": name,
                "type": type_str,
                "description": desc,
                "related": related
            })
        return formatted
    
    async def get_structured_completion(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> LLMResponse:
        """Get structured completion from LLM."""
        system_prompt = """You are Nova, an AI assistant focused on self-discovery and growth. 
        Extract key concepts from the input using this exact format:
        [
          {
            "CONCEPT": "Concept name",
            "TYPE": "Concept type",
            "DESC": "Clear description",
            "RELATED": "Space separated list of related concepts"
          }
        ]
        
        Focus on extracting clear concepts and their relationships.
        IMPORTANT: Ensure the response starts with the JSON array and contains proper JSON formatting with commas between objects."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        json={
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "stream": False
                        }
                    ) as response:
                        if response.status != 200:
                            raise ValueError(f"API request failed: {response.status}")
                        
                        result = await response.json()
                        logger.debug(f"Raw API response: {json.dumps(result, indent=2)}")
                        
                        if not result.get("choices"):
                            raise ValueError("No choices in response")
                        
                        # Get content from response
                        content = result["choices"][0]["message"]["content"]
                        logger.debug(f"Raw content: {content}")
                        
                        # Extract and parse JSON
                        data = self._extract_json(content)
                        
                        # Format concepts
                        concepts = self._format_concepts(data.get("concepts", []))
                        logger.debug(f"Formatted concepts: {json.dumps(concepts, indent=2)}")
                        
                        return LLMResponse(concepts=concepts)
                
            except Exception as e:
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All LLM requests failed")
                    raise
