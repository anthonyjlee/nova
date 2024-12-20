"""
Enhanced belief agent implementation using LLMs for all operations.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAgent
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class BeliefAgent(BaseAgent):
    """Agent for managing belief system."""
    
    def __init__(self, *args, **kwargs):
        """Initialize belief agent."""
        super().__init__(*args, agent_type="belief", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for belief context
        memories = content.get('similar_memories', [])
        memory_text = '\n'.join([
            f"Memory {i+1}: {m.get('content', {}).get('content', '')}"
            for i, m in enumerate(memories)
        ])
        
        # Get context analysis
        context = content.get('context_analysis', {})
        context_text = json.dumps(context, indent=2) if context else "No context available"
        
        # Format prompt
        prompt = f"""Analyze the following content from an epistemological and belief system perspective.
        Consider belief structures, knowledge frameworks, and underlying assumptions.
        
        Content:
        {text}
        
        Belief Context:
        {memory_text}
        
        Context Analysis:
        {context_text}
        
        Provide analysis in this exact format:
        {{
            "response": "Detailed analysis from belief perspective",
            "concepts": [
                {{
                    "name": "Concept name",
                    "type": "belief|framework|assumption|principle",
                    "description": "Clear description of the belief concept",
                    "related": ["Related concept names"],
                    "validation": {{
                        "confidence": 0.8,
                        "supported_by": ["evidence"],
                        "contradicted_by": [],
                        "needs_verification": []
                    }}
                }}
            ],
            "key_points": [
                "Key point about belief structures"
            ],
            "implications": [
                "Implication for knowledge framework"
            ],
            "uncertainties": [
                "Uncertainty in current understanding"
            ],
            "reasoning": [
                "Step in belief analysis"
            ]
        }}
        
        Focus on:
        - Epistemological frameworks
        - Belief structures and patterns
        - Knowledge relationships
        - Assumption analysis
        - Principle identification
        
        Return ONLY the JSON object, no other text."""
        
        return prompt

    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response with belief-specific perspective."""
        try:
            # Use parsing agent to structure the response
            parsed = await self.llm.parser.parse_text(llm_response.response)
            
            # Create enhanced response
            response = AgentResponse(
                # Core response synthesizing belief analysis
                response=parsed.response,
                concepts=parsed.concepts,
                
                # Belief-specific analysis
                key_points=parsed.key_points,
                implications=parsed.implications,
                uncertainties=parsed.uncertainties,
                reasoning=parsed.reasoning,
                
                # Belief agent perspective
                perspective="Epistemological and belief system analysis",
                
                # Confidence based on belief clarity
                confidence=await self._calculate_confidence(parsed),
                
                # Additional metadata
                metadata={
                    "beliefs_identified": sum(1 for c in parsed.concepts if c.get("type") == "belief"),
                    "frameworks_found": sum(1 for c in parsed.concepts if c.get("type") == "framework"),
                    "assumptions_noted": sum(1 for c in parsed.concepts if c.get("type") == "assumption"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing belief response: {str(e)}")
            return AgentResponse(
                response="Error processing belief analysis",
                concepts=[],
                perspective="belief",
                confidence=0.0
            )
    
    async def _calculate_confidence(
        self,
        parsed_response: AgentResponse
    ) -> float:
        """Calculate confidence based on response quality."""
        try:
            # Use LLM to analyze confidence
            confidence_prompt = f"""Analyze the quality and confidence of this belief analysis:
            
            Response: {parsed_response.response}
            Concepts: {json.dumps(parsed_response.concepts)}
            Key Points: {json.dumps(parsed_response.key_points)}
            
            Provide confidence assessment in this format:
            {{
                "confidence": 0.0 to 1.0 score,
                "explanation": "Detailed explanation of score",
                "factors": ["List of contributing factors"]
            }}
            
            Consider:
            - Belief clarity
            - Framework coherence
            - Assumption identification
            - Knowledge integration
            
            Return ONLY the JSON object, no other text."""
            
            # Get confidence analysis through parsing agent
            analysis = await self.llm.parser.parse_text(
                await self.llm.get_completion(confidence_prompt)
            )
            
            # Extract confidence score
            if hasattr(analysis, 'confidence'):
                return float(analysis.confidence)
            
            # Default confidence based on response quality
            if parsed_response.concepts and parsed_response.key_points:
                return 0.8
            elif parsed_response.concepts or parsed_response.key_points:
                return 0.6
            return 0.4
                
        except Exception as e:
            logger.error(f"Error calculating belief confidence: {str(e)}")
            return 0.5
