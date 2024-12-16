"""
LLM interface for structured completions.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class LLMResponse:
    """Structured LLM response."""
    
    def __init__(
        self,
        response: str,
        analysis: Dict[str, Any]
    ):
        """Initialize response."""
        self.response = response
        self.analysis = analysis
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "analysis": self.analysis
        }

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM interface."""
        self.api_key = api_key
    
    def _fix_json(self, text: str) -> str:
        """Fix common JSON formatting issues."""
        try:
            # Remove any text before the first {
            text = text[text.find("{"):]
            
            # Remove any text after the last }
            text = text[:text.rfind("}") + 1]
            
            # Fix missing quotes around property names
            text = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', text)
            
            # Fix missing quotes around string values
            text = re.sub(r':\s*([^{\[\d"\'\s][^,}\]\s]*)', r': "\1"', text)
            
            # Fix trailing commas
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            
            # Fix missing commas between elements
            text = re.sub(r'}\s*{', '},{', text)
            text = re.sub(r']\s*{', '],{', text)
            text = re.sub(r'}\s*\[', '},\[', text)
            text = re.sub(r']\s*\[', '],\[', text)
            
            # Validate the fixed JSON
            json.loads(text)
            logger.warning("Fixed JSON formatting")
            return text
            
        except Exception as e:
            logger.error(f"Failed to fix JSON: {str(e)}")
            raise
    
    def _validate_response(self, data: Dict[str, Any]) -> bool:
        """Validate response format."""
        try:
            # Check required fields
            if not isinstance(data.get("response"), str):
                logger.warning("Missing required response field")
                return False
            
            analysis = data.get("analysis")
            if not isinstance(analysis, dict):
                logger.warning("Missing required analysis field")
                return False
            
            # Check analysis fields
            if not isinstance(analysis.get("key_points"), list):
                logger.warning("Missing required key_points field")
                return False
            
            if not isinstance(analysis.get("confidence"), (int, float)):
                logger.warning("Missing required confidence field")
                return False
            
            if not isinstance(analysis.get("state_update"), str):
                logger.warning("Missing required state_update field")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}")
            return False
    
    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format response to standard structure."""
        try:
            # Ensure response is a string
            if isinstance(data.get("response"), dict):
                data["response"] = json.dumps(data["response"])
            elif not isinstance(data.get("response"), str):
                data["response"] = str(data.get("response", ""))
            
            # Ensure analysis exists
            if "analysis" not in data:
                data["analysis"] = {}
            
            # Ensure key_points is a list
            if "key_points" not in data["analysis"]:
                data["analysis"]["key_points"] = []
            elif isinstance(data["analysis"]["key_points"], str):
                data["analysis"]["key_points"] = [data["analysis"]["key_points"]]
            
            # Ensure confidence is a float
            if "confidence" not in data["analysis"]:
                data["analysis"]["confidence"] = 0.5
            else:
                data["analysis"]["confidence"] = float(data["analysis"]["confidence"])
            
            # Ensure state_update exists
            if "state_update" not in data["analysis"]:
                data["analysis"]["state_update"] = "No state update provided"
            elif not isinstance(data["analysis"]["state_update"], str):
                data["analysis"]["state_update"] = str(data["analysis"]["state_update"])
            
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
        for attempt in range(max_retries):
            try:
                # Simulate LLM call (replace with actual implementation)
                raw_response = {
                    "response": "Analyzing Nia's impact and technical roadmap",
                    "analysis": {
                        "key_points": [
                            "Nia represents a foundation of core capabilities including function calls, image generation, and computer vision",
                            "Technical focus should be on enhancing these capabilities and adding new ones",
                            "Integration between capabilities needs improvement",
                            "Memory system requires better semantic understanding"
                        ],
                        "confidence": 0.9,
                        "state_update": "Developing technical roadmap based on Nia's capabilities"
                    }
                }
                
                # Parse response
                if isinstance(raw_response, str):
                    try:
                        data = json.loads(raw_response)
                    except:
                        data = json.loads(self._fix_json(raw_response))
                else:
                    data = raw_response
                
                # Format response
                data = self._format_response(data)
                
                # Validate response
                if not self._validate_response(data):
                    raise ValueError("Invalid response format")
                
                logger.info(f"Raw LLM response: {json.dumps(data, indent=2)}")
                
                return LLMResponse(
                    response=data["response"],
                    analysis=data["analysis"]
                )
                
            except Exception as e:
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All LLM requests failed: " + str(e))
                    raise
