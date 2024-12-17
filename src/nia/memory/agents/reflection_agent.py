"""
Enhanced reflection agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAgent
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for meta-learning and reflection."""
    
    def __init__(self, *args, **kwargs):
        """Initialize reflection agent."""
        super().__init__(*args, agent_type="reflection", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for historical context
        memories = content.get('similar_memories', [])
        memory_text = '\n'.join([
            f"Memory {i+1}: {m.get('content', {}).get('content', '')}"
            for i, m in enumerate(memories)
        ])
        
        # Get relevant concepts
        concepts = content.get('relevant_concepts', [])
        concept_text = '\n'.join([
            f"Concept {i+1}: {c.get('name')} ({c.get('type')}) - {c.get('description')}"
            for i, c in enumerate(concepts)
        ])
        
        # Format prompt
        prompt = f"""Analyze the following content from a reflective and meta-learning perspective.
        Consider patterns, insights, learning opportunities, and system evolution.
        
        Current Content:
        {text}
        
        Historical Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide a structured analysis with:

        1. Concepts in this exact format:
        [
          {{
            "name": "Concept name",
            "type": "pattern|insight|learning|evolution",
            "description": "Clear description of the concept",
            "related": ["Related concept names"]
          }}
        ]

        2. Key points about patterns and insights (as list of strings)
        3. Implications for learning and evolution (as list of strings)
        4. Uncertainties in current understanding (as list of strings)
        5. Reasoning steps in reflection (as list of strings)
        
        Focus on:
        - Recurring patterns across experiences
        - Learning opportunities from past interactions
        - Evolution of understanding over time
        - Meta-level insights about the system
        - Growth indicators and potential
        
        Ensure all outputs are properly formatted as lists and JSON objects.
        Avoid nesting beyond one level in JSON structures."""
        
        return prompt

    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response with reflection-specific perspective."""
        try:
            # Get pattern analysis using LLM
            pattern_prompt = f"""Analyze patterns in these concepts:
            {llm_response.concepts}
            
            Identify recurring themes, relationships, and meta-level patterns.
            Provide analysis in JSON format."""
            
            pattern_analysis = await self.llm.get_completion(pattern_prompt)
            
            # Get learning analysis using LLM
            learning_prompt = f"""Analyze learning opportunities from:
            Response: {llm_response.response}
            Key Points: {llm_response.key_points}
            Implications: {llm_response.implications}
            
            Identify growth areas, insights, and potential improvements.
            Provide analysis in JSON format."""
            
            learning_analysis = await self.llm.get_completion(learning_prompt)
            
            # Get evolution analysis using LLM
            evolution_prompt = f"""Analyze system evolution from:
            Current Understanding: {llm_response.response}
            Historical Context: {content.get('similar_memories', [])}
            
            Identify changes, improvements, and development paths.
            Provide analysis in JSON format."""
            
            evolution_analysis = await self.llm.get_completion(evolution_prompt)
            
            # Create enhanced response
            response = AgentResponse(
                # Core response synthesizing reflective analysis
                response=llm_response.response,
                concepts=llm_response.concepts,
                
                # Reflection-specific analysis
                key_points=llm_response.key_points,
                implications=llm_response.implications,
                uncertainties=llm_response.uncertainties,
                reasoning=llm_response.reasoning,
                
                # Reflection agent perspective
                perspective="Meta-learning and system evolution analysis",
                
                # Confidence based on analysis depth
                confidence=await self._calculate_confidence(
                    llm_response,
                    pattern_analysis,
                    learning_analysis,
                    evolution_analysis
                ),
                
                # Additional metadata
                metadata={
                    "patterns_identified": len(llm_response.concepts),
                    "learning_opportunities": len(llm_response.implications),
                    "evolution_indicators": len(llm_response.key_points),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing reflection response: {str(e)}")
            return AgentResponse(
                response="Error processing reflection analysis",
                concepts=[],
                perspective="reflection",
                confidence=0.0
            )
    
    async def _calculate_confidence(
        self,
        llm_response: Any,
        pattern_analysis: str,
        learning_analysis: str,
        evolution_analysis: str
    ) -> float:
        """Calculate confidence using LLM analysis."""
        try:
            # Use LLM to analyze confidence
            confidence_prompt = f"""Analyze the quality and confidence of this reflection:
            
            Response: {llm_response.response}
            Pattern Analysis: {pattern_analysis}
            Learning Analysis: {learning_analysis}
            Evolution Analysis: {evolution_analysis}
            
            Provide confidence assessment in this format:
            {{
                "confidence": 0.0 to 1.0 score,
                "explanation": "Detailed explanation of score",
                "factors": ["List of contributing factors"]
            }}
            
            Consider:
            - Depth of pattern recognition
            - Quality of learning insights
            - Clarity of evolution tracking
            - Supporting evidence
            
            Respond with properly formatted JSON only."""
            
            # Get confidence analysis
            analysis = await self.llm.get_completion(confidence_prompt)
            
            try:
                result = json.loads(analysis)
                return float(result.get("confidence", 0.5))
            except (json.JSONDecodeError, ValueError):
                logger.error("Failed to parse confidence analysis")
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating reflection confidence: {str(e)}")
            return 0.5
