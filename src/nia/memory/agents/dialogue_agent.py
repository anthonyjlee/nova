"""Dialogue management agent for handling conversation flow and participants."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..memory_types import AgentResponse, DialogueContext, DialogueMessage
from .base import BaseAgent

logger = logging.getLogger(__name__)

class DialogueAgent(BaseAgent):
    """Agent for managing dialogue flow and participants."""
    
    def __init__(self, *args, **kwargs):
        """Initialize dialogue agent."""
        super().__init__(*args, agent_type="dialogue", **kwargs)
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for dialogue management."""
        # Get content text
        text = content.get('content', '')
        
        # Format current dialogue state
        dialogue = content.get('dialogue_context')
        if dialogue:
            state = [
                f"Topic: {dialogue.topic}",
                f"Status: {dialogue.status}",
                f"Participants: {', '.join(dialogue.participants)}",
                "\nMessages:"
            ]
            
            for msg in dialogue.messages:
                state.append(
                    f"- {msg.agent_type}: {msg.content} "
                    f"({msg.message_type})"
                )
            
            dialogue_state = "\n".join(state)
        else:
            dialogue_state = "No active dialogue"
        
        # Format prompt
        prompt = f"""You are a dialogue management agent. Your task is to understand and track conversation flow, participants, and their interactions.

Current Content:
{text}

Current Dialogue State:
{dialogue_state}

Provide analysis in this exact format:
{{
    "response": "Dialogue management analysis",
    "concepts": [
        {{
            "name": "Participant or interaction name",
            "type": "participant|interaction|pattern",
            "description": "Clear description of the dialogue element",
            "related": ["Related elements"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["evidence"],
                "contradicted_by": [],
                "needs_verification": []
            }}
        }}
    ],
    "key_points": [
        "Key dialogue insight"
    ],
    "implications": [
        "Dialogue management implication"
    ],
    "uncertainties": [
        "Dialogue uncertainty"
    ],
    "reasoning": [
        "Dialogue management step"
    ],
    "participants": [
        {{
            "name": "participant name",
            "role": "participant role",
            "type": "participant type"
        }}
    ],
    "messages": [
        {{
            "from": "sender",
            "to": "recipient",
            "content": "message content",
            "type": "message type"
        }}
    ],
    "next_actions": [
        {{
            "action": "what should happen",
            "participant": "who should act"
        }}
    ]
}}

Focus on:
1. Identifying all participants
2. Tracking who is speaking to whom
3. Understanding message relationships
4. Maintaining conversation coherence
5. Ensuring proper turn-taking

Return ONLY the JSON object, no other text."""
        
        return prompt
    
    async def process_dialogue(
        self,
        text: str,
        dialogue: Optional[DialogueContext] = None
    ) -> DialogueContext:
        """Process dialogue text and update context."""
        try:
            # Create dialogue context if needed
            if not dialogue:
                dialogue = DialogueContext(
                    topic="New Dialogue",
                    status="active"
                )
            
            # Get dialogue analysis through base agent
            response = await self.process({
                'content': text,
                'dialogue_context': dialogue
            })
            
            # Update dialogue based on response
            if isinstance(response, AgentResponse):
                # Add participants
                for participant in response.metadata.get('participants', []):
                    name = participant.get('name')
                    if name and name not in dialogue.participants:
                        dialogue.add_participant(name)
                
                # Add messages
                for message in response.metadata.get('messages', []):
                    if 'from' in message and 'content' in message:
                        msg = DialogueMessage(
                            agent_type=message['from'],
                            content=message['content'],
                            message_type=message.get('type', 'message'),
                            metadata={'to': message.get('to')} if message.get('to') else {}
                        )
                        dialogue.add_message(msg)
            
            # Add default agents if no participants yet
            if len(dialogue.participants) <= 1:
                default_agents = ['belief', 'emotion', 'reflection']
                for agent in default_agents:
                    if agent not in dialogue.participants:
                        dialogue.add_participant(agent)
            
            return dialogue
            
        except Exception as e:
            logger.error(f"Error processing dialogue: {str(e)}")
            return dialogue or DialogueContext(
                topic="Error Dialogue",
                status="error"
            )
    
    async def suggest_next_action(
        self,
        dialogue: DialogueContext
    ) -> str:
        """Suggest next action in dialogue."""
        try:
            # Get next action through base agent
            response = await self.process({
                'content': 'What should happen next in this dialogue?',
                'dialogue_context': dialogue
            })
            
            if isinstance(response, AgentResponse):
                next_actions = response.metadata.get('next_actions', [])
                if next_actions:
                    action = next_actions[0]
                    return (
                        f"Next Action:\n"
                        f"- Action: {action.get('action', 'unknown')}\n"
                        f"- Participant: {action.get('participant', 'unknown')}"
                    )
            
            return response.response
            
        except Exception as e:
            logger.error(f"Error suggesting next action: {str(e)}")
            return "Error suggesting next action"
