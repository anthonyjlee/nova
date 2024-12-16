"""
Interface for LLM interactions.
"""

import logging
import json
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(self, api_url: str = "http://localhost:1234/v1/chat/completions"):
        """Initialize LLM interface."""
        self.api_url = api_url
        self.system_prompt = "You are a helpful AI assistant."
    
    def _format_messages(self, prompt: str) -> list:
        """Format messages for LLM API."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
    
    async def get_completion(self, prompt: str) -> str:
        """Get completion from LLM."""
        try:
            messages = self._format_messages(prompt)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json={
                        "model": "local",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"LLM API error: {error_text}")
                    
                    data = await response.json()
                    
                    if not data.get("choices"):
                        raise ValueError("No choices in LLM response")
                    
                    content = data["choices"][0]["message"]["content"]
                    return content
                    
        except Exception as e:
            logger.error(f"Error getting LLM completion: {str(e)}")
            raise
    
    async def get_json_completion(
        self,
        prompt: str,
        retries: int = 3,
        default_response: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get JSON completion from LLM with retries."""
        for attempt in range(retries):
            try:
                # Add explicit JSON formatting instruction
                json_prompt = f"{prompt}\n\nIMPORTANT: Respond with ONLY a JSON object. No other text."
                
                completion = await self.get_completion(json_prompt)
                
                # Try to extract JSON
                try:
                    # Find JSON start/end
                    json_start = completion.find('{')
                    json_end = completion.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = completion[json_start:json_end]
                        # Clean up common formatting issues
                        json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                        json_str = json_str.replace('```json', '').replace('```', '')
                        return json.loads(json_str)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON on attempt {attempt + 1}")
                    if attempt == retries - 1:  # Last attempt
                        logger.error(f"Failed to parse JSON after {retries} attempts")
                        if default_response is not None:
                            return default_response
                        raise
            
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt == retries - 1:  # Last attempt
                    if default_response is not None:
                        return default_response
                    raise
        
        # Should never reach here due to raises above
        return default_response if default_response is not None else {}
