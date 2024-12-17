"""
Enhanced emotion agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAgent
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class EmotionAgent(BaseAgent):
    """Agent for emotional processing and analysis."""
    
    def __init__(self, *args, **kwargs):
        """Initialize emotion agent."""
        super().__init__(*args, agent_type="emotion", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for emotional context
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
        prompt = f"""Analyze the following content from an emotional intelligence perspective.
        Consider emotional states, affective patterns, and emotional implications.
        
        Content:
        {text}
        
        Emotional Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide a structured analysis with:

        1. Concepts in this exact format:
        [
          {{
            "name": "Concept name",
            "type": "emotion|affect|pattern|response",
            "description": "Clear description of the emotional concept",
            "related": ["Related concept names"]
          }}
        ]

        2. Key points about emotional content (as list of strings)
        3. Implications for emotional understanding (as list of strings)
        4. Uncertainties in emotional interpretation (as list of strings)
        5. Reasoning steps in emotional analysis (as list of strings)
        
        Focus on:
        - Emotional states and patterns
        - Affective responses and triggers
        - Emotional context and history
        - Relationship dynamics
        - Emotional intelligence insights
        
        Ensure all outputs are properly formatted as lists and JSON objects.
        Avoid nesting beyond one level in JSON structures."""
        
        return prompt

    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response with emotion-specific perspective."""
        try:
            # Analyze emotional patterns using LLM
            pattern_prompt = f"""Analyze emotional patterns in:
            Response: {llm_response.response}
            Key Points: {llm_response.key_points}
            
            Identify recurring emotional themes, affective patterns, and emotional triggers.
            Provide analysis in JSON format."""
            
            pattern_analysis = await self.llm.get_completion(pattern_prompt)
            
            # Analyze emotional context using LLM
            context_prompt = f"""Analyze emotional context from:
            Current Content: {llm_response.response}
            Historical Context: {content.get('similar_memories', [])}
            
            Identify emotional history, relationship patterns, and contextual factors.
            Provide analysis in JSON format."""
            
            context_analysis = await self.llm.get_completion(context_prompt)
            
            # Analyze emotional implications using LLM
            implications_prompt = f"""Analyze emotional implications of:
            Concepts: {llm_response.concepts}
            Implications: {llm_response.implications}
            
            Identify potential emotional impacts, responses, and future considerations.
            Provide analysis in JSON format."""
            
            implications_analysis = await self.llm.get_completion(implications_prompt)
            
            # Create enhanced response
            response = AgentResponse(
                # Core response synthesizing emotional analysis
                response=llm_response.response,
                concepts=llm_response.concepts,
                
                # Emotion-specific analysis
                key_points=llm_response.key_points,
                implications=llm_response.implications,
                uncertainties=llm_response.uncertainties,
                reasoning=llm_response.reasoning,
                
                # Emotion agent perspective
                perspective="Emotional intelligence and affective pattern analysis",
                
                # Confidence based on emotional clarity
                confidence=await self._calculate_confidence(
                    llm_response,
                    pattern_analysis,
                    context_analysis,
                    implications_analysis
                ),
                
                # Additional metadata
                metadata={
                    "emotional_states": sum(1 for c in llm_response.concepts if c.get("type") == "emotion"),
                    "affective_patterns": sum(1 for c in llm_response.concepts if c.get("type") == "pattern"),
                    "response_types": sum(1 for c in llm_response.concepts if c.get("type") == "response"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing emotional response: {str(e)}")
            return AgentResponse(
                response="Error processing emotional analysis",
                concepts=[],
                perspective="emotion",
                confidence=0.0
            )
    
    async def _calculate_confidence(
        self,
        llm_response: Any,
        pattern_analysis: str,
        context_analysis: str,
        implications_analysis: str
    ) -> float:
        """Calculate confidence using LLM analysis."""
        try:
            # Use LLM to analyze confidence
            confidence_prompt = f"""Analyze the quality and confidence of this emotional analysis:
            
            Response: {llm_response.response}
            Pattern Analysis: {pattern_analysis}
            Context Analysis: {context_analysis}
            Implications Analysis: {implications_analysis}
            
            Provide confidence assessment in this format:
            {{
                "confidence": 0.0 to 1.0 score,
                "explanation": "Detailed explanation of score",
                "factors": ["List of contributing factors"]
            }}
            
            Consider:
            - Emotional clarity
            - Pattern recognition quality
            - Context understanding
            - Implication insight depth
            
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
            logger.error(f"Error calculating emotional confidence: {str(e)}")
            return 0.5
