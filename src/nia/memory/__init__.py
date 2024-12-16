"""
Memory system initialization.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from .persistence import MemoryStore
from .agents.meta_agent import MetaAgent
from .agents.belief_agent import BeliefAgent
from .agents.desire_agent import DesireAgent
from .agents.emotion_agent import EmotionAgent
from .agents.reflection_agent import ReflectionAgent
from .agents.research_agent import ResearchAgent
from .error_handling import ErrorHandler
from .feedback import FeedbackSystem

logger = logging.getLogger(__name__)

class MemorySystem:
    """Manages memory and agent coordination."""
    
    def __init__(self, collection_name: str = "memory_vectors"):
        """Initialize memory system."""
        # Initialize core components in correct dependency order
        self.memory_store = MemoryStore(collection_name=collection_name)
        self.error_handler = ErrorHandler(self.memory_store)
        self.feedback_system = FeedbackSystem(self.memory_store, self.error_handler)
        
        # Initialize meta agent
        self.meta_agent = MetaAgent(
            self.memory_store,
            self.error_handler,
            self.feedback_system
        )
        
        # Initialize and register other agents
        self._init_agents()
        
        # Track initialization time
        self.init_time = datetime.now().isoformat()
        
        # Track unique interactions to avoid duplicates
        self.seen_interactions = set()
    
    async def initialize(self, reset: bool = False, recreate_vectors: bool = True):
        """Initialize memory store and other components."""
        try:
            # Initialize vector store with recreation flag
            await self.memory_store.vector_store.init_collection(recreate=recreate_vectors)
            
            # Reset if requested
            if reset:
                logger.info("Resetting memory system...")
                await self.memory_store.vector_store.clear_collection()
                self.seen_interactions.clear()
                logger.info("Memory system reset complete")
            
            # Initialize memory store
            await self.memory_store.initialize()
            
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            raise
    
    def _init_agents(self):
        """Initialize and register all agents."""
        # Create agents
        self.belief_agent = BeliefAgent(self.memory_store, self.error_handler, self.feedback_system)
        self.desire_agent = DesireAgent(self.memory_store, self.error_handler, self.feedback_system)
        self.emotion_agent = EmotionAgent(self.memory_store, self.error_handler, self.feedback_system)
        self.reflection_agent = ReflectionAgent(self.memory_store, self.error_handler, self.feedback_system)
        self.research_agent = ResearchAgent(self.memory_store, self.error_handler, self.feedback_system)
        
        # Register agents with meta agent
        self.meta_agent.register_agent("BeliefAgent", self.belief_agent)
        self.meta_agent.register_agent("DesireAgent", self.desire_agent)
        self.meta_agent.register_agent("EmotionAgent", self.emotion_agent)
        self.meta_agent.register_agent("ReflectionAgent", self.reflection_agent)
        self.meta_agent.register_agent("ResearchAgent", self.research_agent)
    
    async def process_interaction(self, content: str) -> str:
        """Process user interaction."""
        try:
            # Skip empty content
            if not content or not content.strip():
                return "I cannot process empty input. Please provide some content."
            
            # Check for duplicate interaction
            if content in self.seen_interactions:
                return await self.meta_agent.process_interaction(content)
            
            # Store new interaction
            self.seen_interactions.add(content)
            
            # Gather agent outputs
            agent_outputs = {}
            
            # Process with belief agent
            belief_output = await self.belief_agent.process_interaction(content)
            agent_outputs["BeliefAgent"] = belief_output
            
            # Process with desire agent
            desire_output = await self.desire_agent.process_interaction(content)
            agent_outputs["DesireAgent"] = desire_output
            
            # Process with emotion agent
            emotion_output = await self.emotion_agent.process_interaction(content)
            agent_outputs["EmotionAgent"] = emotion_output
            
            # Process with reflection agent
            reflection_output = await self.reflection_agent.process_interaction(content)
            agent_outputs["ReflectionAgent"] = reflection_output
            
            # Process with research agent
            research_output = await self.research_agent.process_interaction(content)
            agent_outputs["ResearchAgent"] = research_output
            
            # Process with meta agent
            return await self.meta_agent.process_interaction(content, agent_outputs)
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            await self.error_handler.report_error(
                error_type="interaction_processing_error",
                source_agent="memory_system",
                details={"error": str(e), "content": content},
                severity=2,
                context={"activity": "process_interaction"}
            )
            return f"I apologize, but I encountered an error processing that interaction. Could you try rephrasing or asking something else?"
    
    async def get_system_state(self) -> Dict:
        """Get current system state."""
        try:
            # Get recent memories without duplicates
            recent_memories = []
            seen_timestamps = set()
            
            # Get all memories
            memories = await self.memory_store.get_recent_memories(limit=10)
            
            # Filter and deduplicate
            for memory in memories:
                if isinstance(memory.get('content'), dict):
                    timestamp = memory.get('timestamp', '')
                    content = memory['content'].get('input', '')
                    
                    # Skip empty or duplicate content
                    if not content or timestamp in seen_timestamps:
                        continue
                    
                    seen_timestamps.add(timestamp)
                    recent_memories.append({
                        'input': content,
                        'timestamp': timestamp,
                        'type': memory.get('memory_type', 'unknown')
                    })
            
            # Sort by timestamp, most recent first
            recent_memories.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'system_info': {
                    'initialized_at': self.init_time,
                    'current_time': datetime.now().isoformat(),
                    'registered_agents': list(self.meta_agent.registered_agents.keys())
                },
                'memory_stats': {
                    'short_term_memories': len(self.seen_interactions),
                    'recent_interactions': recent_memories[:5]  # Limit to 5 most recent
                },
                'error_stats': self.error_handler.get_stats(),
                'feedback_stats': self.feedback_system.get_stats()
            }
        except Exception as e:
            logger.error(f"Error getting system state: {str(e)}")
            return {
                'error': str(e),
                'system_info': {
                    'initialized_at': self.init_time,
                    'current_time': datetime.now().isoformat()
                }
            }
    
    async def cleanup(self):
        """Clean up system resources."""
        try:
            # Clear short-term memory
            self.seen_interactions.clear()
            
            # Clear vector store
            await self.memory_store.vector_store.clear_collection()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise
