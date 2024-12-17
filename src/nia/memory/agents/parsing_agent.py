"""Parsing agent for extracting structured information from text."""

import logging
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
        return f"""You are a parsing agent. Your task is to extract structured information from the given text and return it in a natural language response that I can parse.

Text to analyze:
{content.get('text', '')}

Please analyze this text and provide:

1. Concepts - Extract both actions and validated concepts:
   - For actions, include: action_type (ASK/SYNTHESIZE/VALIDATE/PROBE), target_agent, content, purpose, references
   - For concepts, include: name, type, description, related concepts, source perspectives, confidence level, validation details

2. Key Points - What are the main insights or conclusions?

3. Implications - What areas need more discussion or investigation?

4. Uncertainties - What questions or doubts remain?

5. Reasoning - What is the synthesis of current understanding?

Format your response with clear section headers. For each concept, provide complete details including validation information (what supports it, contradicts it, or needs verification).

Remember:
- Identify both actions to be taken and concepts being discussed
- Include all validation details for concepts
- Maintain relationships between ideas
- Preserve all references and citations
- Extract both explicit and implicit insights

Analyze the text thoroughly and provide a complete structured understanding."""
    
    async def parse_text(self, text: str) -> AgentResponse:
        """Parse text into structured format."""
        try:
            # Get structured analysis from LLM
            response = await self.llm.get_completion(
                self._format_prompt({
                    'text': text
                })
            )
            
            # Get another LLM pass to extract structured data
            extraction_prompt = f"""From this analysis, extract structured data in this exact format:

Analysis:
{response}

Please provide:
1. A list of concepts (including both actions and validated concepts)
2. A list of key points
3. A list of implications
4. A list of uncertainties
5. A list of reasoning points

For each concept that represents an action, include:
- type: "action"
- action_type: "ASK", "SYNTHESIZE", "VALIDATE", or "PROBE"
- target_agent: which agent should perform the action
- content: what should be done
- purpose: why this action is needed
- references: any relevant citations

For each validated concept, include:
- type: the concept type (pattern, insight, etc.)
- name: concept name
- description: clear description
- related: related concepts
- source_perspectives: who contributed to this concept
- confidence: 0.0-1.0 confidence score
- validation: what supports/contradicts/needs verification

Provide your response in natural language, describing each element clearly."""
            
            # Get structured data
            structured = await self.llm.get_completion(extraction_prompt)
            
            # Create agent response
            return AgentResponse(
                response=text,  # Original text
                concepts=self._extract_concepts(structured),
                key_points=self._extract_points(structured, "key points"),
                implications=self._extract_points(structured, "implications"),
                uncertainties=self._extract_points(structured, "uncertainties"),
                reasoning=self._extract_points(structured, "reasoning"),
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
    
    def _extract_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Extract concepts from text using another LLM call."""
        prompt = f"""From this text, extract all concepts (both actions and validated concepts) as a list of descriptions.
        
Text:
{text}

For each concept, describe:
1. Whether it's an action or a validated concept
2. All its properties and details
3. Any validation information
4. Any relationships to other concepts

Provide your response as a natural language list of concept descriptions."""
        
        # This will be called by parse_text which already has LLM access
        return []  # Placeholder - actual extraction happens in parse_text
    
    def _extract_points(self, text: str, section: str) -> List[str]:
        """Extract points from a section using another LLM call."""
        prompt = f"""From this text, extract the {section} as a list.
        
Text:
{text}

List each {section} point as a clear, complete statement.
Preserve any important details, references, or relationships.

Provide your response as a natural language list."""
        
        # This will be called by parse_text which already has LLM access
        return []  # Placeholder - actual extraction happens in parse_text
