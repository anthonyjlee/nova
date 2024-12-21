"""Reflection agent for meta-learning and pattern analysis."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..memory_types import AgentResponse, DialogueMessage
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ReflectionAgent(BaseAgent):
    """Agent for analyzing patterns and meta-learning."""
    
    def __init__(self, llm, store, vector_store):
        """Initialize reflection agent."""
        super().__init__(llm, store, vector_store, "reflection")
        self.current_dialogue = None
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for reflection analysis."""
        return f"""Analyze the patterns and meta-learning aspects in this content:

Content:
{content.get('content', '')}

Provide analysis in this format:
{{
    "response": "Clear analysis of patterns and learning",
    "concepts": [
        {{
            "name": "Pattern/Learning concept",
            "type": "pattern|insight|learning|evolution",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }}
        }}
    ],
    "key_points": [
        "Key pattern or learning insight"
    ],
    "implications": [
        "Important implication for learning/growth"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}}"""

    async def provide_insight(
        self,
        content: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Provide insight into current dialogue.
        
        Args:
            content: Insight content
            references: Optional list of referenced concepts/messages
            
        Returns:
            New dialogue message
        """
        if not self.current_dialogue:
            logger.warning("No active dialogue for insight")
            return None
            
        message = DialogueMessage(
            content=content,
            message_type="insight",
            agent_type=self.agent_type,
            references=references or [],
            timestamp=datetime.now()
        )
        
        self.current_dialogue.add_message(message)
        return message
    
    async def send_message(
        self,
        content: str,
        message_type: str,
        references: Optional[List[str]] = None
    ) -> DialogueMessage:
        """Send message to current dialogue.
        
        Args:
            content: Message content
            message_type: Type of message
            references: Optional list of referenced concepts/messages
            
        Returns:
            New dialogue message
        """
        if not self.current_dialogue:
            logger.warning("No active dialogue for message")
            return None
            
        message = DialogueMessage(
            content=content,
            message_type=message_type,
            agent_type=self.agent_type,
            references=references or [],
            timestamp=datetime.now()
        )
        
        self.current_dialogue.add_message(message)
        return message
