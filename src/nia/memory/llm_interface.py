"""LLM interface for agent interactions."""

import logging
from typing import Dict, Any, Optional, Union
from .agents.parsing_agent import ParsingAgent

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(self):
        """Initialize LLM interface."""
        self.parser = None
        self.model = None
        self.embeddings = None
    
    def set_parser(self, parser: ParsingAgent) -> None:
        """Set parser for structured responses."""
        self.parser = parser
    
    async def get_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Union[str, Dict[str, Any]]:
        """Get completion from LLM."""
        try:
            # For testing, return a mock response that will be parsed
            mock_response = """
            {
                "response": "Analysis of the topic",
                "concepts": [
                    {
                        "name": "Test Concept",
                        "type": "pattern",
                        "description": "A test concept for validation",
                        "related": ["Testing"],
                        "validation": {
                            "confidence": 0.5,
                            "supported_by": [],
                            "contradicted_by": [],
                            "needs_verification": ["All aspects"]
                        }
                    }
                ],
                "key_points": [
                    "Test point 1",
                    "Test point 2"
                ],
                "implications": [
                    "Test implication 1",
                    "Test implication 2"
                ],
                "uncertainties": [
                    "Test uncertainty 1",
                    "Test uncertainty 2"
                ],
                "reasoning": [
                    "Test reasoning step 1",
                    "Test reasoning step 2"
                ]
            }
            """
            
            # Let the parser handle the response
            if self.parser:
                return await self.parser.parse_text(mock_response)
            return mock_response
            
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            if self.parser:
                return await self.parser.parse_text(str(e))
            return str(e)
    
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for texts."""
        try:
            # Mock embeddings for testing
            return [[0.1, 0.2, 0.3] for _ in texts]
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            return [[0.0, 0.0, 0.0] for _ in texts]
    
    async def get_chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get chat completion from LLM."""
        try:
            # For testing, return a mock response that will be parsed
            mock_response = """
            {
                "response": "This is a chat response",
                "concepts": [],
                "key_points": ["Chat response point"],
                "implications": [],
                "uncertainties": [],
                "reasoning": []
            }
            """
            
            # Let the parser handle the response
            if self.parser:
                result = await self.parser.parse_text(mock_response)
                return result.response
            return mock_response
            
        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            return str(e)
    
    async def extract_concepts(
        self,
        text: str,
        concept_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """Extract concepts from text."""
        try:
            # Let the parser handle concept extraction
            if self.parser:
                result = await self.parser.parse_text(text)
                if concept_type:
                    return [c for c in result.concepts if c.get("type") == concept_type]
                return result.concepts
            return []
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            return []
    
    async def validate_concept(
        self,
        concept: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate concept against context."""
        try:
            # Let the parser handle concept validation
            if self.parser:
                validation_text = f"""
                Concept: {concept}
                Context: {context or 'No context provided'}
                
                Validation:
                {{
                    "confidence": 0.8,
                    "supported_by": ["Test evidence"],
                    "contradicted_by": [],
                    "needs_verification": []
                }}
                """
                result = await self.parser.parse_text(validation_text)
                if result.concepts:
                    return result.concepts[0]
            return concept
            
        except Exception as e:
            logger.error(f"Error validating concept: {str(e)}")
            return concept
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text."""
        try:
            # Let the parser handle sentiment analysis
            if self.parser:
                sentiment_text = f"""
                Text: {text}
                
                Sentiment Analysis:
                {{
                    "response": "Sentiment analysis",
                    "concepts": [],
                    "key_points": [],
                    "implications": [],
                    "uncertainties": [],
                    "reasoning": [],
                    "sentiment": {{
                        "positive": 0.6,
                        "negative": 0.2,
                        "neutral": 0.2
                    }}
                }}
                """
                result = await self.parser.parse_text(sentiment_text)
                if isinstance(result, dict) and "sentiment" in result:
                    return result["sentiment"]
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0
            }
