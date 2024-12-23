"""Meta agent for synthesizing responses from other agents."""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from ..memory_types import AgentResponse, DialogueContext
from .base import BaseAgent

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j_store import Neo4jMemoryStore
    from ..vector_store import VectorStore

logger = logging.getLogger(__name__)

class MetaAgent(BaseAgent):
    """Agent for synthesizing responses and managing dialogue."""
    
    def __init__(
        self,
        llm: 'LLMInterface',
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore',
        agents: Dict[str, BaseAgent]
    ):
        """Initialize meta agent."""
        super().__init__(llm, store, vector_store, agent_type="meta")
        
        # Store sub-agents
        self.belief_agent = agents.get('belief')
        self.desire_agent = agents.get('desire')
        self.emotion_agent = agents.get('emotion')
        self.reflection_agent = agents.get('reflection')
        self.research_agent = agents.get('research')
        self.task_planner_agent = agents.get('task_planner')
        
        # Initialize dialogue context
        self.current_dialogue = DialogueContext(
            topic="Meta Dialogue",
            status="active"
        )
        
        # Track consolidation
        self.last_consolidation = datetime.now()
        self.consolidation_interval = timedelta(hours=1)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        try:
            # Get vector store status
            episodic_count = await self.vector_store.count_vectors(layer="episodic")
            semantic_count = await self.vector_store.count_vectors(layer="semantic")
            
            # Get Neo4j status
            concept_count = await self.store.count_concepts()
            relationship_count = await self.store.count_relationships()
            
            # Calculate next consolidation
            next_consolidation = self.last_consolidation + self.consolidation_interval
            
            return {
                'vector_store': {
                    'episodic_count': episodic_count,
                    'semantic_count': semantic_count,
                    'last_consolidation': self.last_consolidation.isoformat(),
                    'next_consolidation': next_consolidation.isoformat()
                },
                'neo4j': {
                    'concept_count': concept_count,
                    'relationship_count': relationship_count
                },
                'active_agents': [
                    'belief',
                    'desire',
                    'emotion',
                    'reflection',
                    'research',
                    'task_planner'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                'vector_store': {
                    'episodic_count': 0,
                    'semantic_count': 0,
                    'last_consolidation': 'Never',
                    'next_consolidation': 'Unknown'
                },
                'neo4j': {
                    'concept_count': 0,
                    'relationship_count': 0
                },
                'active_agents': []
            }
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for LLM."""
        # Get content and responses
        text = content.get('content', {}).get('content', '')
        responses = content.get('agent_responses', {})
        dialogue = content.get('dialogue_context')
        
        # Format agent responses with clear separation
        response_text = []
        for agent_type, response in responses.items():
            response_text.append(
                f"{agent_type.capitalize()} Agent Perspective:\n"
                f"Response: {response.response}\n"
                f"Main Concepts: {[c['name'] for c in response.concepts]}\n"
                f"Key Insights: {response.key_points}\n"
                f"Implications: {response.implications}\n"
                f"Uncertainties: {response.uncertainties}\n"
                "---"
            )
        
        # Format dialogue context if available
        dialogue_text = ""
        if dialogue:
            dialogue_text = "\nPrevious Dialogue Context:\n" + "\n".join([
                f"{m.agent_type}: {m.content}"
                for m in dialogue.messages
            ])
        
        # Format prompt
        prompt = f"""Analyze and synthesize multiple agent perspectives into a unified understanding.

Original Content:
{text}

Agent Perspectives:
{'\n'.join(response_text)}

{dialogue_text}

Analysis Guidelines:
1. Check which agents returned errors vs successful responses
2. Focus on extracting a clear answer from working agents
3. Keep the response simple and direct
4. Only add context if it directly helps answer the question
5. If most agents error, provide a graceful fallback response

Provide synthesis in this exact format:
{
    "response": "Start with a clear, direct answer to the user's question in one sentence. If needed, add 1-2 sentences of relevant context from working agents.",
    "concepts": [
        {
            "name": "Most relevant concept to the question",
            "type": "synthesis",
            "description": "Brief description that helps answer the question",
            "related": ["Only directly relevant concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["Working agent responses"],
                "contradicted_by": [],
                "needs_verification": ["Critical uncertainties"]
            }
        }
    ],
    "key_points": [
        "The direct answer",
        "Only essential supporting points"
    ],
    "implications": [
        "Most important implication for the user"
    ],
    "uncertainties": [
        "Only mention if it affects the answer"
    ],
    "reasoning": [
        "Brief explanation of how you arrived at the answer"
    ]
}

Guidelines:
1. Focus on directly answering the user's question first
2. Keep the response concise and clear
3. Include only the most relevant insights from agents
4. Add context only if it helps clarify the answer
5. Format as proper JSON

Return ONLY the JSON object, no other text."""
        
        return prompt
    
    async def synthesize_dialogue(
        self,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Synthesize dialogue from agent responses."""
        try:
            # Process through base agent which uses parsing agent
            response = await self.process(content)
            
            # Add dialogue context if available
            if content.get('dialogue_context'):
                response.dialogue_context = content['dialogue_context']
            
            # Add metadata
            response.metadata = {
                'dialogue_turns': len(content.get('dialogue_context', {}).messages) if content.get('dialogue_context') else 0,
                'participating_agents': list(content.get('agent_responses', {}).keys()),
                'synthesis_timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error synthesizing dialogue: {str(e)}")
            return AgentResponse(
                response="Error synthesizing dialogue",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="meta",
                confidence=0.0,
                timestamp=datetime.now()
            )
            
    async def _consolidate_memories(self) -> None:
        """Force memory consolidation."""
        try:
            # Get all episodic memories
            episodic_memories = await self.vector_store.search_vectors(
                content="",
                layer="episodic",
                limit=1000
            )
            
            # Process and store as semantic memories
            for memory in episodic_memories:
                await self.vector_store.store_vector(
                    content=memory,
                    layer="semantic",
                    metadata={
                        "type": "consolidation",
                        "timestamp": datetime.now()
                    }
                )
            
            # Update consolidation timer
            self.last_consolidation = datetime.now()
            
            logger.info("Memory consolidation complete")
            
        except Exception as e:
            logger.error(f"Error during consolidation: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clear vector store
            await self.vector_store.clear_vectors(layer="episodic")
            await self.vector_store.clear_vectors(layer="semantic")
            
            # Clear Neo4j store
            await self.store.clear_concepts()
            await self.store.clear_relationships()
            await self.store.clear_memories()
            
            # Reset consolidation timer
            self.last_consolidation = datetime.now()
            
            # Clear dialogue context
            self.current_dialogue = DialogueContext(
                topic="Meta Dialogue",
                status="active"
            )
            
            logger.info("Cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    async def process_interaction(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process interaction through meta agent."""
        try:
            # Create content dict
            content_dict = {
                'content': {'content': text},
                'dialogue_context': self.current_dialogue,
                'agent_responses': {}
            }
            
            # Store episodic memory first
            await self.vector_store.store_vector(
                content=text,
                metadata={"type": "input", "timestamp": datetime.now()},
                layer="episodic"
            )
            
            # Get agent responses and store their concepts
            for agent_type in ['belief', 'desire', 'emotion', 'reflection', 'research', 'task_planner']:
                agent = getattr(self, f"{agent_type}_agent", None)
                if agent:
                    response = await agent.process(
                        content_dict['content'],
                        metadata
                    )
                    content_dict['agent_responses'][agent_type] = response
                    
                    # Store concepts from each agent
                    for concept in response.concepts:
                        await self.store.store_concept(
                            name=concept["name"],
                            type=concept["type"],
                            description=concept["description"],
                            related=concept.get("related", [])
                        )
                        
                    # Store agent response as semantic memory
                    await self.vector_store.store_vector(
                        content=response.dict(),
                        metadata={"type": "agent_response", "agent": agent_type, "timestamp": datetime.now()},
                        layer="semantic"
                    )
            
            # Synthesize responses
            return await self.synthesize_dialogue(content_dict)
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            return AgentResponse(
                response="Error processing interaction",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="error",
                confidence=0.0,
                timestamp=datetime.now()
            )
