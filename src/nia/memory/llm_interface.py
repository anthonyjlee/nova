"""
LLM interface for structured completions.
"""

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
        response: str,
        analysis: Dict[str, Any],
        concepts: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize response."""
        self.response = response
        self.analysis = analysis
        self.concepts = concepts or []
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "analysis": self.analysis,
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
    
    def _extract_json_content(self, text: str) -> str:
        """Extract JSON content from text."""
        try:
            # Find JSON content between curly braces
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON content found")
            
            # Extract JSON part
            return text[start:end]
            
        except Exception as e:
            logger.error(f"Failed to extract JSON content: {str(e)}")
            raise
    
    def _fix_json(self, text: str) -> str:
        """Fix common JSON formatting issues."""
        try:
            # Fix missing quotes around property names
            text = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', text)
            
            # Fix missing quotes around string values
            text = re.sub(r':\s*([^{\[\d"\'\s][^,}\]\s]*)', r': "\1"', text)
            
            # Fix trailing commas
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            
            # Fix missing commas between elements
            text = re.sub(r'}\s*{', '},{', text)
            text = re.sub(r']\s*{', '],{', text)
            text = re.sub(r'}\s*\[', '},\\[', text)
            text = re.sub(r']\s*\[', '],\\[', text)
            
            # Validate the fixed JSON
            json.loads(text)
            logger.warning("Fixed JSON formatting")
            return text
            
        except Exception as e:
            logger.error(f"Failed to fix JSON: {str(e)}")
            raise
    
    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format response to standard structure."""
        try:
            logger.debug(f"Formatting response data: {json.dumps(data, indent=2)}")
            
            # Handle response field
            if not isinstance(data.get("response"), str):
                data["response"] = str(data.get("response", ""))
            
            # Handle concepts field
            if "concepts" not in data:
                data["concepts"] = []
            elif not isinstance(data["concepts"], list):
                data["concepts"] = []
            
            # Handle analysis field
            if "analysis" not in data:
                data["analysis"] = {}
            
            # Handle key_points field
            if "key_points" not in data["analysis"]:
                data["analysis"]["key_points"] = []
            elif isinstance(data["analysis"]["key_points"], str):
                data["analysis"]["key_points"] = [data["analysis"]["key_points"]]
            
            # Handle confidence field
            if "confidence" not in data["analysis"]:
                data["analysis"]["confidence"] = 0.8
            else:
                data["analysis"]["confidence"] = float(data["analysis"]["confidence"])
            
            # Handle state_update field
            if "state_update" not in data["analysis"]:
                data["analysis"]["state_update"] = "Processed interaction"
            elif not isinstance(data["analysis"]["state_update"], str):
                data["analysis"]["state_update"] = str(data["analysis"]["state_update"])
            
            logger.debug(f"Formatted response: {json.dumps(data, indent=2)}")
            return data
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            raise
    
    async def get_structured_completion(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> LLMResponse:
        """Get structured completion from LLM."""
        system_prompt = """You are Nova, an AI assistant focused on self-discovery and growth. 
        Analyze the input and provide a response in this JSON format:
        {
            "response": "Your main response as a clear, engaging message",
            "concepts": [
                {
                    "name": "Concept name",
                    "type": "Concept type (e.g., idea, capability, emotion)",
                    "description": "Clear description of the concept",
                    "related_concepts": [
                        {
                            "name": "Related concept name",
                            "type": "Related concept type"
                        }
                    ]
                }
            ],
            "analysis": {
                "key_points": ["List of key insights"],
                "confidence": 0.0-1.0,
                "state_update": "How this affects your understanding"
            }
        }
        
        Focus on extracting clear concepts and their relationships. Be natural while maintaining analytical depth."""

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
                        
                        # Extract content from choices[0].message.content
                        content = result["choices"][0]["message"]["content"]
                        logger.debug(f"Extracted content: {content}")
                        
                        # Extract JSON from content
                        json_content = self._extract_json_content(content)
                        logger.debug(f"Extracted JSON: {json_content}")
                        
                        # Parse response
                        try:
                            data = json.loads(json_content)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {str(e)}")
                            logger.debug(f"Failed content: {json_content}")
                            # Try to fix JSON formatting
                            fixed_content = self._fix_json(json_content)
                            data = json.loads(fixed_content)
                        
                        # Format response
                        data = self._format_response(data)
                        
                        logger.info(f"Final formatted response: {json.dumps(data, indent=2)}")
                        
                        return LLMResponse(
                            response=data["response"],
                            analysis=data["analysis"],
                            concepts=data.get("concepts", [])
                        )
                
            except Exception as e:
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All LLM requests failed")
                    raise
