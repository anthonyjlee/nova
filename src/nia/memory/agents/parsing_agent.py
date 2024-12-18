"""Parsing agent for extracting structured information from text."""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ParsingAgent(BaseAgent):
    """Agent for parsing and structuring text."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize parsing agent."""
        super().__init__(llm, store, vector_store, agent_type="parsing")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for parsing."""
        return f"""You are a parsing agent. Your task is to extract structured information from the given text and return it in JSON format.

Text to analyze:
{content.get('text', '')}

IMPORTANT: You must respond with ONLY valid JSON, no other text. Here is an example of the exact format required:

{{
    "concepts": [
        {{
            "name": "Emotional Processing",
            "type": "capability",
            "description": "AI systems process emotions differently from humans",
            "confidence": 0.8,
            "validation": {{
                "supported_by": ["observed patterns", "expert analysis"],
                "contradicted_by": [],
                "needs_verification": ["long-term stability"]
            }}
        }}
    ],
    "key_points": [
        "AI emotional processing shows unique patterns",
        "Self-reflection capabilities are emerging"
    ],
    "implications": [
        "Need to explore emotional intelligence in AI systems",
        "Further research needed on self-reflection mechanisms"
    ],
    "uncertainties": [
        "How do AI systems develop emotional awareness?",
        "What are the limits of machine consciousness?"
    ],
    "reasoning": [
        "AI systems show distinct patterns in emotional processing",
        "Self-reflection appears to be an emerging capability"
    ]
}}

Extract:
- Concepts from "Validated Concepts" sections
- Key points from "Key Insights" sections
- Implications from "Areas Needing Discussion" sections
- Uncertainties from questions raised
- Reasoning from "Synthesis" sections

For concepts, include:
- Name from bold text or bullet points
- Type based on context (capability, pattern, insight)
- Description from the explanation
- Supporting evidence from context
- Related concepts from nearby mentions

Your response must be ONLY the JSON object shown above, with no markdown, no text, no explanation - just the JSON."""
    
    async def parse_text(self, text: str) -> AgentResponse:
        """Parse text into structured format."""
        try:
            # Get structured analysis from LLM
            response = await self.llm.get_completion(
                self._format_prompt({
                    'text': text
                })
            )
            
            # Try to parse JSON response
            try:
                structured = json.loads(response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from markdown
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    try:
                        structured = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # If still not valid, ask LLM to fix it
                        fix_prompt = f"""The previous response was not valid JSON. Format the following text as JSON matching this example exactly:

{{
    "concepts": [
        {{
            "name": "Emotional Processing",
            "type": "capability",
            "description": "AI systems process emotions differently from humans",
            "confidence": 0.8,
            "validation": {{
                "supported_by": ["observed patterns"],
                "contradicted_by": [],
                "needs_verification": ["long-term stability"]
            }}
        }}
    ],
    "key_points": ["AI emotional processing shows unique patterns"],
    "implications": ["Need to explore emotional intelligence in AI"],
    "uncertainties": ["How do AI systems develop awareness?"],
    "reasoning": ["AI systems show distinct emotional patterns"]
}}

Text to format:
{response}

Return ONLY the JSON object, no other text."""
                        
                        fixed_response = await self.llm.get_completion(fix_prompt)
                        structured = json.loads(fixed_response)
                else:
                    # If no JSON found, ask LLM to fix it
                    fix_prompt = f"""The previous response was not valid JSON. Format the following text as JSON matching this example exactly:

{{
    "concepts": [
        {{
            "name": "Emotional Processing",
            "type": "capability",
            "description": "AI systems process emotions differently from humans",
            "confidence": 0.8,
            "validation": {{
                "supported_by": ["observed patterns"],
                "contradicted_by": [],
                "needs_verification": ["long-term stability"]
            }}
        }}
    ],
    "key_points": ["AI emotional processing shows unique patterns"],
    "implications": ["Need to explore emotional intelligence in AI"],
    "uncertainties": ["How do AI systems develop awareness?"],
    "reasoning": ["AI systems show distinct emotional patterns"]
}}

Text to format:
{response}

Return ONLY the JSON object, no other text."""
                    
                    fixed_response = await self.llm.get_completion(fix_prompt)
                    structured = json.loads(fixed_response)
            
            # Create agent response
            return AgentResponse(
                response=text,  # Original text
                concepts=structured.get('concepts', []),
                key_points=structured.get('key_points', []),
                implications=structured.get('implications', []),
                uncertainties=structured.get('uncertainties', []),
                reasoning=structured.get('reasoning', []),
                perspective="parsing",
                confidence=0.9,  # High confidence for structured data
                timestamp=datetime.now()
            )
                
        except Exception as e:
            logger.error(f"Error parsing text: {str(e)}")
            return AgentResponse(
                response=text,
                concepts=[],
                perspective="parsing",
                confidence=0.0,
                timestamp=datetime.now()
            )
