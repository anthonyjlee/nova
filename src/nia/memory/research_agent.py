"""
Enhanced research agent implementation using LLMs for all operations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .agents.base import BaseAgent
from .memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for research and knowledge integration."""
    
    def __init__(self, *args, **kwargs):
        """Initialize research agent."""
        super().__init__(*args, agent_type="research", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content text
        text = content.get('content', '')
        
        # Get similar memories for knowledge context
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
        prompt = f"""Analyze the following content from a research and knowledge integration perspective.
        Consider information sources, knowledge gaps, and integration opportunities.
        
        Content to Research:
        {text}
        
        Existing Knowledge:
        {memory_text}
        
        Known Concepts:
        {concept_text}
        
        Provide a structured analysis with:

        1. Concepts in this exact format:
        [
          {{
            "name": "Concept name",
            "type": "knowledge|source|connection|gap",
            "description": "Clear description of the concept",
            "related": ["Related concept names"]
          }}
        ]

        2. Key points about information gathered (as list of strings)
        3. Implications for knowledge integration (as list of strings)
        4. Uncertainties requiring further research (as list of strings)
        5. Reasoning steps in research process (as list of strings)
        
        Focus on:
        - Knowledge gaps and research needs
        - Information sources and reliability
        - Integration opportunities with existing knowledge
        - Verification requirements
        - Research priorities
        
        Ensure all outputs are properly formatted as lists and JSON objects.
        Avoid nesting beyond one level in JSON structures."""
        
        return prompt

    async def _process_llm_response(
        self,
        llm_response: Any,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Process LLM response with research-specific perspective."""
        try:
            # Analyze knowledge gaps using LLM
            gaps_prompt = f"""Analyze knowledge gaps in:
            Response: {llm_response.response}
            Key Points: {llm_response.key_points}
            Uncertainties: {llm_response.uncertainties}
            
            Identify areas needing further research, missing information, and verification needs.
            Provide analysis in JSON format."""
            
            gaps_analysis = await self.llm.get_completion(gaps_prompt)
            
            # Analyze information quality using LLM
            quality_prompt = f"""Analyze information quality of:
            Concepts: {llm_response.concepts}
            Implications: {llm_response.implications}
            Reasoning: {llm_response.reasoning}
            
            Assess reliability, completeness, and verification status.
            Provide analysis in JSON format."""
            
            quality_analysis = await self.llm.get_completion(quality_prompt)
            
            # Analyze integration opportunities using LLM
            integration_prompt = f"""Analyze integration opportunities between:
            New Information: {llm_response.response}
            Existing Knowledge: {content.get('similar_memories', [])}
            
            Identify connection points, synthesis opportunities, and potential conflicts.
            Provide analysis in JSON format."""
            
            integration_analysis = await self.llm.get_completion(integration_prompt)
            
            # Create enhanced response
            response = AgentResponse(
                # Core response synthesizing research analysis
                response=llm_response.response,
                concepts=llm_response.concepts,
                
                # Research-specific analysis
                key_points=llm_response.key_points,
                implications=llm_response.implications,
                uncertainties=llm_response.uncertainties,
                reasoning=llm_response.reasoning,
                
                # Research agent perspective
                perspective="Knowledge acquisition and integration analysis",
                
                # Confidence based on information quality
                confidence=await self._calculate_confidence(
                    llm_response,
                    gaps_analysis,
                    quality_analysis,
                    integration_analysis
                ),
                
                # Additional metadata
                metadata={
                    "knowledge_gaps": len(llm_response.uncertainties),
                    "information_sources": sum(1 for c in llm_response.concepts if c.get("type") == "source"),
                    "integration_opportunities": len(llm_response.implications),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing research response: {str(e)}")
            return AgentResponse(
                response="Error processing research analysis",
                concepts=[],
                perspective="research",
                confidence=0.0
            )
    
    async def _calculate_confidence(
        self,
        llm_response: Any,
        gaps_analysis: str,
        quality_analysis: str,
        integration_analysis: str
    ) -> float:
        """Calculate confidence using LLM analysis."""
        try:
            # Use LLM to analyze confidence
            confidence_prompt = f"""Analyze the quality and confidence of this research:
            
            Response: {llm_response.response}
            Gaps Analysis: {gaps_analysis}
            Quality Analysis: {quality_analysis}
            Integration Analysis: {integration_analysis}
            
            Provide confidence assessment in this format:
            {{
                "confidence": 0.0 to 1.0 score,
                "explanation": "Detailed explanation of score",
                "factors": ["List of contributing factors"]
            }}
            
            Consider:
            - Information completeness
            - Source reliability
            - Verification status
            - Integration potential
            
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
            logger.error(f"Error calculating research confidence: {str(e)}")
            return 0.5
    
    async def research_topic(
        self,
        topic: str,
        context: Dict[str, Any] = None
    ) -> AgentResponse:
        """Conduct research on a specific topic."""
        try:
            # Format research content
            content = {
                'content': topic,
                'context': context or {}
            }
            
            # Process through research lens
            return await self.process(content)
            
        except Exception as e:
            logger.error(f"Error researching topic: {str(e)}")
            return AgentResponse(
                response=f"Error researching topic: {str(e)}",
                concepts=[],
                perspective="research",
                confidence=0.0
            )
