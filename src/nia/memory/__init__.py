"""
Memory system initialization.
"""

import logging
from typing import Dict, Optional

from .persistence import MemoryStore
from .error_handling import ErrorHandler
from .feedback import FeedbackSystem
from .agents import (
    MetaAgent,
    BeliefAgent,
    DesireAgent,
    EmotionAgent,
    ReflectionAgent,
    ResearchAgent
)

logger = logging.getLogger(__name__)

class MemorySystem:
    """Main memory system."""
    
    def __init__(self):
        """Initialize memory system."""
        # Core components
        self.memory_store = MemoryStore()
        self.error_handler = ErrorHandler()
        self.feedback_system = FeedbackSystem()
        
        # Initialize agents
        self.meta_agent = MetaAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        self.belief_agent = BeliefAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        self.desire_agent = DesireAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        self.emotion_agent = EmotionAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        self.reflection_agent = ReflectionAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        self.research_agent = ResearchAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        # Register agents with meta agent
        self.meta_agent.register_agent("BeliefAgent", self.belief_agent)
        self.meta_agent.register_agent("DesireAgent", self.desire_agent)
        self.meta_agent.register_agent("EmotionAgent", self.emotion_agent)
        self.meta_agent.register_agent("ReflectionAgent", self.reflection_agent)
        self.meta_agent.register_agent("ResearchAgent", self.research_agent)
        
        # Store agents in dict for easy access
        self._agents = {
            "BeliefAgent": self.belief_agent,
            "DesireAgent": self.desire_agent,
            "EmotionAgent": self.emotion_agent,
            "ReflectionAgent": self.reflection_agent,
            "ResearchAgent": self.research_agent,
            "MetaAgent": self.meta_agent
        }
    
    def get_agent(self, name: str) -> Optional[object]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def get_agents(self) -> Dict[str, object]:
        """Get all agents."""
        return self._agents.copy()
    
    async def initialize(self):
        """Initialize memory system."""
        await self.memory_store.initialize()
        logger.info("Memory system initialized")
