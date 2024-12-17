"""
Enhanced belief agent implementation using LLMs for all operations.
"""

import logging
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
        
        # Get relevant concepts
        concepts = content.get('relevant_concepts', [])
        concept_text = '\n'.join([
            f"Concept {i+1}: {c.get('name')} ({c.get('type')}) - {c.get('description')}"
            for i, c in enumerate(concepts)
        ])
        
        # Format prompt
        prompt = f"""Analyze the following content from an epistemological and belief system perspective.
        Consider belief structures, knowledge frameworks, and underlying assumptions.
        
        Content:
        {text}
        
        Belief Context:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide a structured analysis with:

        1. Concepts in this exact format:
        [
          {{
            "name": "Concept name",
            "type": "belief|framework|assumption|principle",
            "description": "Clear description of the belief concept",
            "related": ["Related concept names"]
          }}
        ]

        2. Key points about belief structures (as list of strings)
        3. Implications for knowledge framework (as list of strings)
        4. Uncertainties in current understanding (as list of strings)
        5. Reasoning steps in belief analysis (as list of strings)
        
        Focus on:
        - Epistemological frameworks
        - Belief structures and patterns
        - Knowledge relationships
        - Assumption analysis
        - Principle identification
        
        Ensure all outputs are properly formatted as lists and JSON objects.
        Avoid nesting beyond one level in JSON structures."""
        
        return prompt

    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response with belief-specific perspective."""
        try:
            # Analyze belief patterns using LLM
            belief_prompt = f"""Analyze belief patterns in:
            Response: {llm_response.response}
            Key Points: {llm_response.key_points}
            
            Identify belief structures, epistemological frameworks, and knowledge patterns.
            Provide analysis in JSON format."""
            
            belief_analysis = await self.llm.get_completion(belief_prompt)
            
            # Analyze assumptions using LLM
            assumption_prompt = f"""Analyze underlying assumptions in:
            Current Content: {llm_response.response}
            Historical Context: {content.get('similar_memories', [])}
            
            Identify core assumptions, principles, and belief foundations.
            Provide analysis in JSON format."""
            
            assumption_analysis = await self.llm.get_completion(assumption_prompt)
            
            # Analyze knowledge implications using LLM
            knowledge_prompt = f"""Analyze knowledge implications of:
            Concepts: {llm_response.concepts}
            Implications: {llm_response.implications}
            
            Identify epistemological impacts, knowledge relationships, and framework evolution.
            Provide analysis in JSON format."""
            
            knowledge_analysis = await self.llm.get_completion(knowledge_prompt)
            
            # Create enhanced response
            response = AgentResponse(
                # Core response synthesizing belief analysis
                response=llm_response.response,
                concepts=llm_response.concepts,
                
                # Belief-specific analysis
                key_points=llm_response.key_points,
                implications=llm_response.implications,
                uncertainties=llm_response.uncertainties,
                reasoning=llm_response.reasoning,
                
                # Belief agent perspective
                perspective="Epistemological and belief system analysis",
                
                # Confidence based on belief clarity
                confidence=await self._calculate_confidence(
                    llm_response,
                    belief_analysis,
                    assumption_analysis,
                    knowledge_analysis
                ),
                
                # Additional metadata
                metadata={
                    "beliefs_identified": sum(1 for c in llm_response.concepts if c.get("type") == "belief"),
                    "frameworks_found": sum(1 for c in llm_response.concepts if c.get("type") == "framework"),
                    "assumptions_noted": sum(1 for c in llm_response.concepts if c.get("type") == "assumption"),
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
        llm_response: Any,
        belief_analysis: str,
        assumption_analysis: str,
        knowledge_analysis: str
    ) -> float:
        """Calculate confidence using LLM analysis."""
        try:
            # Use LLM to analyze confidence
            confidence_prompt = f"""Analyze the quality and confidence of this belief analysis:
            
            Response: {llm_response.response}
            Belief Analysis: {belief_analysis}
            Assumption Analysis: {assumption_analysis}
            Knowledge Analysis: {knowledge_analysis}
            
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
            logger.error(f"Error calculating belief confidence: {str(e)}")
            return 0.5
