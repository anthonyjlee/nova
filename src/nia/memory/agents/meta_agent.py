"""Meta agent for coordinating dialogue between specialized agents."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse, DialogueContext, DialogueMessage
from .base import BaseAgent
from .parsing_agent import ParsingAgent

logger = logging.getLogger(__name__)

class MetaAgent(BaseAgent):
    """Meta agent for coordinating dialogue."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize meta agent."""
        super().__init__(llm, store, vector_store, agent_type="meta")
        self.specialized_agents = {}
        self.parser = ParsingAgent(llm, store, vector_store)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for meta agent."""
        # Get dialogue context if available
        dialogue = content.get('dialogue_context')
        dialogue_text = ""
        if dialogue and isinstance(dialogue, DialogueContext):
            dialogue_text = "\n".join([
                f"{m.agent_type}: {m.content} ({m.message_type})"
                for m in dialogue.messages[-5:]  # Last 5 messages
            ])
            dialogue_text = f"\nCurrent Dialogue:\n{dialogue_text}\n"
        
        # Format prompt
        return f"""You are a meta agent coordinating dialogue between specialized agents.
        
        Content:
        {content.get('content', '')}
        {dialogue_text}
        
        Context:
        {content.get('context_analysis', {})}
        
        Provide:
        1. Dialogue actions - what actions should be taken by which agents?
        2. Validated concepts - what concepts have been validated through the dialogue?
        3. Key insights from the dialogue
        4. Areas needing more discussion
        5. Synthesis of current understanding
        
        Format your response in natural language with clear section headers."""
    
    async def process_interaction(self, content: str) -> AgentResponse:
        """Process user interaction."""
        try:
            # Create dialogue context if needed
            if not self.current_dialogue:
                self.current_dialogue = DialogueContext(
                    topic="User Interaction",
                    status="active"
                )
            
            # Add initial user message
            user_message = DialogueMessage(
                agent_type="user",
                content=content,
                message_type="input"
            )
            self.current_dialogue.add_message(user_message)
            
            # Get meta response
            meta_response = await self.llm.get_completion(
                self._format_prompt({
                    'content': content,
                    'dialogue_context': self.current_dialogue
                })
            )
            
            # Parse response using parsing agent
            parsed = await self.parser.parse_text(meta_response)
            
            # Process actions from parsed response
            for action in parsed.concepts:
                if action.get('type') == 'action':
                    try:
                        action_type = action.get('action_type', '').upper()
                        target_agent = action.get('target_agent')
                        action_content = action.get('content')
                        references = action.get('references', [])
                        purpose = action.get('purpose')
                        
                        # Create message for action
                        message = DialogueMessage(
                            agent_type=self.agent_type,
                            content=action_content,
                            message_type=action_type.lower(),
                            references=references,
                            metadata={
                                "target_agent": target_agent,
                                "purpose": purpose
                            }
                        )
                        
                        # Add message to dialogue
                        self.current_dialogue.add_message(message)
                        
                        # Add participants
                        self.current_dialogue.add_participant(self.agent_type)
                        if target_agent:
                            self.current_dialogue.add_participant(target_agent)
                        
                        # Perform action
                        if action_type == 'ASK':
                            await self.ask_question(
                                action_content,
                                references=references,
                                metadata={"target_agent": target_agent}
                            )
                        elif action_type == 'SYNTHESIZE':
                            await self.provide_insight(
                                action_content,
                                references=references,
                                metadata={"target_agent": target_agent}
                            )
                        elif action_type == 'VALIDATE':
                            await self.provide_insight(
                                action_content,
                                references=references,
                                metadata={
                                    "target_agent": target_agent,
                                    "validation": True
                                }
                            )
                        elif action_type == 'PROBE':
                            await self.ask_question(
                                action_content,
                                references=references,
                                metadata={
                                    "target_agent": target_agent,
                                    "probe": True
                                }
                            )
                    except Exception as e:
                        logger.error(f"Error processing action: {str(e)}")
            
            # Update response with dialogue context
            parsed.dialogue_context = self.current_dialogue
            return parsed
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            return AgentResponse(
                response=f"Error processing interaction: {str(e)}",
                concepts=[],
                perspective="meta",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def synthesize_dialogue(
        self,
        content: Dict[str, Any]
    ) -> AgentResponse:
        """Synthesize dialogue insights."""
        try:
            # Get meta synthesis
            meta_synthesis = await self.llm.get_completion(
                self._format_prompt(content)
            )
            
            # Parse synthesis using parsing agent
            parsed = await self.parser.parse_text(meta_synthesis)
            
            # Add metadata
            parsed.metadata.update({
                'dialogue_turns': len(content.get('dialogue_context', {}).messages),
                'participating_agents': list(set(
                    m.agent_type
                    for m in content.get('dialogue_context', {}).messages
                )),
                'synthesis_timestamp': datetime.now().isoformat()
            })
            
            # Update response
            parsed.dialogue_context = content.get('dialogue_context')
            parsed.perspective = "Collaborative dialogue synthesis"
            parsed.confidence = 0.9  # High confidence for synthesis
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error synthesizing dialogue: {str(e)}")
            return AgentResponse(
                response=f"Error synthesizing dialogue: {str(e)}",
                concepts=[],
                perspective="meta",
                confidence=0.0,
                timestamp=datetime.now()
            )
