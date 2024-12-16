"""
LLM interface for structured completions.
"""

import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMResponse:
    """Structured LLM response."""
    
    def __init__(
        self,
        response: str,
        concepts: List[Dict[str, Any]],
        confidence: float = 0.8,
        state_update: str = ""
    ):
        """Initialize response."""
        self.response = response
        self.concepts = concepts
        self.confidence = confidence
        self.state_update = state_update
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "concepts": self.concepts,
            "confidence": self.confidence,
            "state_update": self.state_update
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
    
    def _parse_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Parse concepts from text using a line-based approach."""
        concepts = []
        current_concept = None
        
        # Split text into lines and process each line
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for new concept
            if line.startswith('CONCEPT:'):
                # Save previous concept if exists
                if current_concept:
                    concepts.append(current_concept)
                # Start new concept
                current_concept = {
                    'name': line.replace('CONCEPT:', '').strip(),
                    'type': '',
                    'description': '',
                    'related_concepts': []
                }
            elif line.startswith('TYPE:') and current_concept:
                current_concept['type'] = line.replace('TYPE:', '').strip()
            elif line.startswith('DESC:') and current_concept:
                current_concept['description'] = line.replace('DESC:', '').strip()
            elif line.startswith('RELATED:') and current_concept:
                related = line.replace('RELATED:', '').strip()
                if related:
                    current_concept['related_concepts'] = [
                        name.strip() for name in related.split(',')
                    ]
        
        # Add last concept if exists
        if current_concept:
            concepts.append(current_concept)
        
        return concepts
    
    async def get_structured_completion(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> LLMResponse:
        """Get structured completion from LLM."""
        system_prompt = """You are Nova, an AI assistant focused on self-discovery and growth.
        Analyze the input and extract key concepts using this format:

        First, provide a brief response summarizing the key points.
        Then, list each concept using this exact format:

        CONCEPT: [Concept Name]
        TYPE: [Concept Type e.g., idea, capability, emotion]
        DESC: [Clear description of the concept]
        RELATED: [Related concept names, comma-separated]

        For example:
        Your understanding of meta-cognition and multi-modal learning is fascinating.

        CONCEPT: Meta Cognition
        TYPE: cognitive capability
        DESC: The ability to think about and understand one's own thought processes
        RELATED: Self Awareness, Learning, Reflection

        CONCEPT: Multi-Modal Learning
        TYPE: learning approach
        DESC: Learning through multiple forms of input like text, images, and video
        RELATED: Meta Cognition, Sensory Processing

        Be natural while maintaining analytical depth."""

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
                        
                        # Split into response and concepts
                        parts = content.split('\n\n', 1)
                        response_text = parts[0].strip()
                        concepts_text = parts[1] if len(parts) > 1 else ""
                        
                        # Parse concepts using line-based approach
                        concepts = self._parse_concepts(concepts_text)
                        logger.debug(f"Parsed concepts: {json.dumps(concepts, indent=2)}")
                        
                        return LLMResponse(
                            response=response_text,
                            concepts=concepts,
                            confidence=0.8,
                            state_update="Processed content and extracted concepts"
                        )
                
            except Exception as e:
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All LLM requests failed")
                    raise
