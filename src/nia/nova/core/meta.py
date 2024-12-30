"""Meta agent for synthesizing responses from other agents."""

import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from ..types.memory_types import AgentResponse, DialogueContext, DialogueMessage
from .base import BaseAgent
from ..prompts import AGENT_PROMPTS, SYSTEM_PROMPT

if TYPE_CHECKING:
    from ..llm_interface import LLMInterface
    from ..neo4j.neo4j_store import Neo4jMemoryStore
    from ..vector.vector_store import VectorStore

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
                f"Main Concepts: {', '.join([c['name'] for c in response.concepts]) if response.concepts else 'None'}\n"
                f"Key Insights: {', '.join(response.key_points) if response.key_points else 'None'}\n"
                f"Implications: {', '.join(response.implications) if response.implications else 'None'}\n"
                f"Uncertainties: {', '.join(response.uncertainties) if response.uncertainties else 'None'}\n"
                "---"
            )
        
        # Format dialogue context if available
        dialogue_text = ""
        if dialogue:
            dialogue_text = "\nPrevious Dialogue Context:\n" + "\n".join([
                f"{m.agent_type}: {m.content}"
                for m in dialogue.messages
            ])
        
        # Format prompt using template
        return AGENT_PROMPTS["meta"].format(
            content=f"""Original Content:
{text}

Agent Perspectives:
{'\n'.join(response_text)}

{dialogue_text}"""
        )
    
    async def synthesize_dialogue(
        self,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Synthesize dialogue from agent responses."""
        try:
            # Process through base agent which uses parsing agent
            raw_response = await self.process(content)
            
            # Extract agent responses and raw response content
            agent_responses = content.get('agent_responses', {})
            
            # Try to parse raw response as JSON if it's a string
            try:
                if isinstance(raw_response.response, str):
                    if raw_response.response.strip().startswith('{'):
                        try:
                            parsed_response = json.loads(raw_response.response)
                        except json.JSONDecodeError:
                            parsed_response = {"response": raw_response.response}
                    else:
                        parsed_response = {"response": raw_response.response}
                else:
                    parsed_response = raw_response.response if isinstance(raw_response.response, dict) else {"response": str(raw_response.response)}
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                parsed_response = {"response": str(raw_response.response)}
            
            # Initialize synthesized response with parsed content
            synthesized_response = {
                'response': parsed_response.get('response', str(raw_response.response)),
                'dialogue': parsed_response.get('dialogue', parsed_response.get('response', str(raw_response.response))),
                'concepts': parsed_response.get('concepts', []),
                'key_points': parsed_response.get('key_points', []),
                'implications': parsed_response.get('implications', []),
                'uncertainties': parsed_response.get('uncertainties', []),
                'reasoning': parsed_response.get('reasoning', []),
                'whispers': []
            }
            
            # Collect insights from all agents
            for agent_type, agent_response in agent_responses.items():
                # Handle concepts
                if hasattr(agent_response, 'concepts') and agent_response.concepts:
                    synthesized_response['concepts'].extend(agent_response.concepts)
                
                # Handle key points
                if hasattr(agent_response, 'key_points') and agent_response.key_points:
                    synthesized_response['key_points'].extend(agent_response.key_points)
                
                # Handle implications
                if hasattr(agent_response, 'implications') and agent_response.implications:
                    synthesized_response['implications'].extend(agent_response.implications)
                
                # Handle uncertainties
                if hasattr(agent_response, 'uncertainties') and agent_response.uncertainties:
                    synthesized_response['uncertainties'].extend(agent_response.uncertainties)
                
                # Handle reasoning
                if hasattr(agent_response, 'reasoning') and agent_response.reasoning:
                    synthesized_response['reasoning'].extend(agent_response.reasoning)
                
                # Handle whispers
                if hasattr(agent_response, 'whispers') and agent_response.whispers:
                    synthesized_response['whispers'].extend(agent_response.whispers)
            
            # Create response object
            response = AgentResponse(
                response=synthesized_response['response'],
                dialogue=synthesized_response['dialogue'],
                concepts=synthesized_response['concepts'],
                key_points=synthesized_response['key_points'],
                implications=synthesized_response['implications'],
                uncertainties=synthesized_response['uncertainties'],
                reasoning=synthesized_response['reasoning'],
                whispers=synthesized_response['whispers'],
                perspective='meta',
                confidence=0.8,
                timestamp=datetime.now()
            )
            
            # Add dialogue context if available
            if isinstance(content, dict) and content.get('dialogue_context'):
                response.dialogue_context = content['dialogue_context']
            
            # Generate whispers from agent responses
            whispers = []
            agent_responses = content.get('agent_responses', {})
            
            # Emotion agent notices feelings
            if 'emotion' in agent_responses:
                emotion_resp = agent_responses['emotion']
                if emotion_resp.concepts:
                    emotion = emotion_resp.concepts[0]
                    whispers.append(f"*Emotion agent whispers: I sense {emotion['description']}*")
            
            # Belief agent shares insights
            if 'belief' in agent_responses:
                belief_resp = agent_responses['belief']
                if belief_resp.key_points:
                    whispers.append(f"*Belief agent whispers: I believe {belief_resp.key_points[0].lower()}*")
            
            # Desire agent reveals motivations
            if 'desire' in agent_responses:
                desire_resp = agent_responses['desire']
                if desire_resp.concepts:
                    desire = desire_resp.concepts[0]
                    whispers.append(f"*Desire agent whispers: They seem to want {desire['description'].lower()}*")
            
            # Reflection agent shares patterns
            if 'reflection' in agent_responses:
                reflection_resp = agent_responses['reflection']
                if reflection_resp.implications:
                    whispers.append(f"*Reflection agent whispers: This reminds me that {reflection_resp.implications[0].lower()}*")
            
            # Research agent adds knowledge
            if 'research' in agent_responses:
                research_resp = agent_responses['research']
                if research_resp.key_points:
                    whispers.append(f"*Research agent whispers: It's worth noting that {research_resp.key_points[0].lower()}*")
            
            # Add whispers to response
            response.whispers = whispers
            
            # Add metadata with agent interactions
            response.metadata = {
                'dialogue_turns': len(content.get('dialogue_context', {}).messages) if content.get('dialogue_context') else 0,
                'participating_agents': list(agent_responses.keys()),
                'synthesis_timestamp': datetime.now().isoformat(),
                'agent_interactions': []
            }

            # Add thinking interaction
            response.metadata['agent_interactions'].append({
                "role": "Meta Agent",
                "content": "Let me analyze this from multiple perspectives..."
            })

            # Add each agent's analysis
            for agent_type, resp in agent_responses.items():
                # Extract key points for interaction content
                key_points = resp.key_points if resp.key_points else []
                implications = resp.implications if resp.implications else []
                analysis_points = key_points + implications

                # Create meaningful interaction content
                if analysis_points:
                    content = f"From my analysis: {' '.join(analysis_points)}"
                else:
                    content = resp.response

                response.metadata['agent_interactions'].append({
                    "role": f"{agent_type.capitalize()} Agent",
                    "content": content
                })

            # Add synthesis interaction
            response.metadata['agent_interactions'].append({
                "role": "Meta Agent",
                "content": f"Based on all perspectives: {response.response}"
            })
            
            # Add assistant's response to dialogue context
            assistant_message = DialogueMessage(
                content=response.dialogue if response.dialogue else response.response,
                agent_type="assistant",
                message_type="response",
                references=[f"{agent_type}" for agent_type in content.get('agent_responses', {}).keys()]
            )
            self.current_dialogue.add_message(assistant_message)
            
            # If no dialogue was generated, use the response as dialogue
            if not response.dialogue:
                response.dialogue = response.response
            
            return response
            
        except Exception as e:
            logger.error(f"Error synthesizing dialogue: {str(e)}")
            return AgentResponse(
                response="Error synthesizing dialogue",
                dialogue="I apologize, but I encountered an error while processing your message.",
                whispers=["*Meta agent whispers: Something went wrong in the synthesis process...*"],
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
            
            # Clear Neo4j store - DETACH DELETE in clear_concepts handles everything
            await self.store.clear_concepts()
            
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
            # Create content dict and update dialogue context
            message = DialogueMessage(
                content=text,
                agent_type="user",
                message_type="input"
            )
            self.current_dialogue.add_message(message)
            
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
                    # Initialize agent metadata
                    agent_metadata = {
                        "type": "agent_response",
                        "agent": agent_type,
                        "timestamp": datetime.now().isoformat(),
                        "whispers": [],
                        "agent_interactions": []
                    }
                    if metadata:
                        agent_metadata.update(metadata)
                    
                    response = await agent.process(
                        content_dict['content'],
                        agent_metadata
                    )
                    
                    # Add whisper for this agent
                    whisper = f"*{agent_type.capitalize()} agent processing: {response.response}*"
                    agent_metadata["whispers"].append(whisper)
                    
                    # Add interaction record
                    agent_metadata["agent_interactions"].append({
                        "role": "assistant",
                        "content": f"[{agent_type.capitalize()} Agent] {response.response}"
                    })
                    
                    # Update response metadata
                    if not response.metadata:
                        response.metadata = {}
                    response.metadata.update(agent_metadata)
                    
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
                dialogue="I apologize, but I encountered an error while processing your message.",
                whispers=["*Meta agent whispers: Having trouble coordinating the agent responses...*"],
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="error",
                confidence=0.0,
                timestamp=datetime.now()
            )
