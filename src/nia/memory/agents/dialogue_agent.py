"""Dialogue management agent for handling conversation flow and participants."""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..vector_store import VectorStore
from ..memory_types import AgentResponse, DialogueContext, DialogueMessage
from .base import BaseAgent

logger = logging.getLogger(__name__)

class DialogueAgent(BaseAgent):
    """Agent for managing dialogue flow and participants."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize dialogue agent."""
        super().__init__(llm, store, vector_store, agent_type="dialogue")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for dialogue management."""
        return f"""You are a dialogue management agent. Your task is to understand and track conversation flow, participants, and their interactions.

Current Dialogue State:
{self._format_dialogue_state(content)}

Your task is to:
1. Identify all participants in the conversation
2. Track who is speaking to whom
3. Understand the relationships between messages
4. Maintain conversation coherence
5. Ensure proper turn-taking

IMPORTANT: You must respond with ONLY valid JSON, no other text. Here is an example of the exact format required:

{{
    "participants": [
        {{
            "name": "belief",
            "role": "expert",
            "type": "agent"
        }},
        {{
            "name": "emotion",
            "role": "specialist",
            "type": "agent"
        }},
        {{
            "name": "reflection",
            "role": "analyst",
            "type": "agent"
        }}
    ],
    "messages": [
        {{
            "from": "belief",
            "to": "emotion",
            "content": "How do you process emotional patterns?",
            "type": "question"
        }}
    ],
    "next_actions": [
        {{
            "action": "respond to question",
            "participant": "emotion"
        }}
    ]
}}

Remember: Your response must be ONLY the JSON object shown above, with no other text or formatting. Include all relevant agents that should participate in the dialogue."""
    
    def _format_dialogue_state(self, content: Dict[str, Any]) -> str:
        """Format current dialogue state for prompt."""
        dialogue = content.get('dialogue_context')
        if not dialogue:
            return "No active dialogue"
        
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
        
        return "\n".join(state)
    
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
            
            # Get dialogue analysis
            analysis = await self.llm.get_completion(
                self._format_prompt({
                    'content': text,
                    'dialogue_context': dialogue
                })
            )
            
            # Try to parse JSON response
            try:
                structured = json.loads(analysis)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from markdown
                json_match = re.search(r'```json\s*(.*?)\s*```', analysis, re.DOTALL)
                if json_match:
                    try:
                        structured = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # If still not valid, ask LLM to fix it
                        fix_prompt = f"""The previous response was not valid JSON. Format the following text as JSON matching this example exactly:

{{
    "participants": [
        {{
            "name": "belief",
            "role": "expert",
            "type": "agent"
        }}
    ],
    "messages": [
        {{
            "from": "belief",
            "content": "How do you process emotions?",
            "type": "question"
        }}
    ],
    "next_actions": [
        {{
            "action": "respond to question",
            "participant": "emotion"
        }}
    ]
}}

Text to format:
{analysis}

Return ONLY the JSON object, no other text."""
                        
                        fixed_response = await self.llm.get_completion(fix_prompt)
                        structured = json.loads(fixed_response)
                else:
                    # If no JSON found, ask LLM to fix it
                    fix_prompt = f"""The previous response was not valid JSON. Format the following text as JSON matching this example exactly:

{{
    "participants": [
        {{
            "name": "belief",
            "role": "expert",
            "type": "agent"
        }}
    ],
    "messages": [
        {{
            "from": "belief",
            "content": "How do you process emotions?",
            "type": "question"
        }}
    ],
    "next_actions": [
        {{
            "action": "respond to question",
            "participant": "emotion"
        }}
    ]
}}

Text to format:
{analysis}

Return ONLY the JSON object, no other text."""
                    
                    fixed_response = await self.llm.get_completion(fix_prompt)
                    structured = json.loads(fixed_response)
            
            # Add participants
            for participant in structured.get('participants', []):
                name = participant.get('name')
                if name and name not in dialogue.participants:
                    dialogue.add_participant(name)
            
            # Add messages
            for message in structured.get('messages', []):
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
                default_agents = [
                    {"name": "belief", "role": "expert", "type": "agent"},
                    {"name": "emotion", "role": "specialist", "type": "agent"},
                    {"name": "reflection", "role": "analyst", "type": "agent"}
                ]
                for agent in default_agents:
                    if agent["name"] not in dialogue.participants:
                        dialogue.add_participant(agent["name"])
            
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
            prompt = f"""Given this dialogue state, what should happen next?
            Consider:
            - Who should speak next
            - What type of message is needed
            - How to maintain conversation flow
            
Dialogue State:
{self._format_dialogue_state({'dialogue_context': dialogue})}

IMPORTANT: You must respond with ONLY valid JSON, no other text. The JSON must follow this exact structure:

{{
    "next_action": {{
        "speaker": "who should speak",
        "type": "type of message",
        "content": "suggested content",
        "purpose": "why this action"
    }}
}}"""
            
            response = await self.llm.get_completion(prompt)
            
            try:
                structured = json.loads(response)
                next_action = structured.get('next_action', {})
                return (
                    f"Next Action:\n"
                    f"- Speaker: {next_action.get('speaker', 'unknown')}\n"
                    f"- Type: {next_action.get('type', 'unknown')}\n"
                    f"- Content: {next_action.get('content', '')}\n"
                    f"- Purpose: {next_action.get('purpose', '')}"
                )
            except json.JSONDecodeError:
                return response
            
        except Exception as e:
            logger.error(f"Error suggesting next action: {str(e)}")
            return "Error suggesting next action"
