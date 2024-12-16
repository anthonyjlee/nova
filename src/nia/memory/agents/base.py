"""
Base agent class with time awareness and memory capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..error_handling import ErrorHandler
from ..feedback import FeedbackSystem
from ..persistence import MemoryStore
from ..llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class TimeAwareAgent:
    """Base class for time-aware agents with memory capabilities."""
    
    def __init__(
        self,
        agent_name: str,
        memory_store: MemoryStore,
        error_handler: ErrorHandler,
        feedback_system: FeedbackSystem,
        llm_interface: LLMInterface
    ):
        """Initialize agent."""
        self.name = agent_name
        self.memory_store = memory_store
        self.error_handler = error_handler
        self.feedback_system = feedback_system
        self.llm_interface = llm_interface
        
        # State tracking
        self.state_vectors: Dict[str, List[float]] = {}
        self.last_update: Dict[str, datetime] = {}
        
        logger.info(f"Initialized {agent_name}")
    
    def _safe_str(self, value: Any, default: str = "") -> str:
        """Safely convert value to string."""
        try:
            if value is None:
                return default
            return str(value)
        except:
            return default
    
    def _safe_list(self, value: Any) -> List:
        """Safely convert value to list."""
        try:
            if isinstance(value, list):
                return value
            elif isinstance(value, str):
                return [value]
            elif value is None:
                return []
            return list(value)
        except:
            return []
    
    def _extract_context(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Extract context from content if present."""
        # Default implementation just returns content and empty context
        return content, {}
    
    async def get_completion(self, prompt: str) -> str:
        """Get completion from LLM."""
        try:
            return await self.llm_interface.get_completion(prompt)
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            raise
    
    async def get_json_completion(
        self,
        prompt: str,
        retries: int = 3,
        default_response: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get JSON completion from LLM."""
        try:
            return await self.llm_interface.get_json_completion(
                prompt=prompt,
                retries=retries,
                default_response=default_response
            )
        except Exception as e:
            logger.error(f"Error getting JSON completion: {str(e)}")
            if default_response is not None:
                return default_response
            raise
    
    async def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> None:
        """Store a memory."""
        try:
            await self.memory_store.store_memory(
                agent_name=self.name,
                memory_type=memory_type,
                content=content,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
    
    async def get_state_similarity(self, state_type: str, content: str) -> float:
        """Get similarity between content and current state."""
        try:
            if state_type not in self.state_vectors:
                return 0.0
            
            # Get embedding for content
            content_embedding = await self.memory_store.embedding_service.get_embedding(content)
            
            # Get current state vector
            state_vector = self.state_vectors[state_type]
            
            # Calculate similarity
            similarity = float(sum(a * b for a, b in zip(content_embedding, state_vector)) /
                            (sum(a * a for a in content_embedding) ** 0.5 *
                             sum(b * b for b in state_vector) ** 0.5))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error getting state similarity: {str(e)}")
            return 0.0
    
    async def update_state_vector(self, state_type: str, content: str) -> None:
        """Update state vector with new content."""
        try:
            # Get embedding for content
            embedding = await self.memory_store.embedding_service.get_embedding(content)
            
            # Update state vector
            self.state_vectors[state_type] = embedding
            self.last_update[state_type] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating state vector: {str(e)}")
            raise
    
    async def process_interaction(self, content: str) -> str:
        """Process an interaction."""
        raise NotImplementedError("Subclasses must implement process_interaction")
