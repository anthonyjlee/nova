"""
Enhanced desire agent implementation using LLMs for all operations.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAgent
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class DesireAgent(BaseAgent):
    """Agent for analyzing goals, motivations, and aspirations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize desire agent."""
        super().__init__(*args, agent_type="desire", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for goal context
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
        prompt = f"""Analyze the following content from a motivational and goal-oriented perspective.
        Consider desires, aspirations, objectives, and underlying motivations.
        
        Content:
        {text}
        
        Goal Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide a structured analysis with:

        1. Concepts in this exact format:
        [
          {{
            "name": "Concept name",
            "type": "goal|motivation|aspiration|desire",
            "description": "Clear description of the motivational concept",
            "related": ["Related concept names"]
          }}
        ]

        2. Key points about goals and motivations (as list of strings)
        3. Implications for goal pursuit (as list of strings)
        4. Uncertainties in motivation analysis (as list of strings)
        5. Reasoning steps in desire analysis (as list of strings)
        
        Focus on:
        - Short and long-term goals
        - Underlying motivations
        - Goal relationships and dependencies
        - Progress indicators
        - Potential obstacles
        - Growth aspirations
        
        Ensure all outputs are properly formatted as lists and JSON objects.
        Avoid nesting beyond one level in JSON structures."""
        
        return prompt

    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response with desire-specific perspective."""
        try:
            # Analyze goal patterns using LLM
            goal_prompt = f"""Analyze goal patterns in:
            Response: {llm_response.response}
            Key Points: {llm_response.key_points}
            
            Identify goal relationships, motivation patterns, and aspiration themes.
            Provide analysis in JSON format."""
            
            goal_analysis = await self.llm.get_completion(goal_prompt)
            
            # Analyze progress and obstacles using LLM
            progress_prompt = f"""Analyze goal progress and obstacles from:
            Current Content: {llm_response.response}
            Historical Context: {content.get('similar_memories', [])}
            
            Identify progress indicators, potential obstacles, and growth opportunities.
            Provide analysis in JSON format."""
            
            progress_analysis = await self.llm.get_completion(progress_prompt)
            
            # Analyze future implications using LLM
            future_prompt = f"""Analyze future implications of:
            Goals: {llm_response.concepts}
            Implications: {llm_response.implications}
            
            Identify potential outcomes, development paths, and future considerations.
            Provide analysis in JSON format."""
            
            future_analysis = await self.llm.get_completion(future_prompt)
            
            # Create enhanced response
            response = AgentResponse(
                # Core response synthesizing desire analysis
                response=llm_response.response,
                concepts=llm_response.concepts,
                
                # Desire-specific analysis
                key_points=llm_response.key_points,
                implications=llm_response.implications,
                uncertainties=llm_response.uncertainties,
                reasoning=llm_response.reasoning,
                
                # Desire agent perspective
                perspective="Motivational and goal-oriented analysis",
                
                # Confidence based on goal clarity
                confidence=await self._calculate_confidence(
                    llm_response,
                    goal_analysis,
                    progress_analysis,
                    future_analysis
                ),
                
                # Additional metadata
                metadata={
                    "goals_identified": sum(1 for c in llm_response.concepts if c.get("type") == "goal"),
                    "motivations_found": sum(1 for c in llm_response.concepts if c.get("type") == "motivation"),
                    "aspirations_noted": sum(1 for c in llm_response.concepts if c.get("type") == "aspiration"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing desire response: {str(e)}")
            return AgentResponse(
                response="Error processing desire analysis",
                concepts=[],
                perspective="desire",
                confidence=0.0
            )
    
    async def _calculate_confidence(
        self,
        llm_response: Any,
        goal_analysis: str,
        progress_analysis: str,
        future_analysis: str
    ) -> float:
        """Calculate confidence using LLM analysis."""
        try:
            # Use LLM to analyze confidence
            confidence_prompt = f"""Analyze the quality and confidence of this goal analysis:
            
            Response: {llm_response.response}
            Goal Analysis: {goal_analysis}
            Progress Analysis: {progress_analysis}
            Future Analysis: {future_analysis}
            
            Provide confidence assessment in this format:
            {{
                "confidence": 0.0 to 1.0 score,
                "explanation": "Detailed explanation of score",
                "factors": ["List of contributing factors"]
            }}
            
            Consider:
            - Goal clarity
            - Motivation understanding
            - Progress assessment
            - Future planning depth
            
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
            logger.error(f"Error calculating desire confidence: {str(e)}")
            return 0.5
