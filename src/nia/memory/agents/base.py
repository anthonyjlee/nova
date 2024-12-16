"""
Base agent class with time awareness.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
import traceback
import numpy as np

from ..error_handling import ErrorHandler
from ..feedback import FeedbackSystem
from ..persistence import MemoryStore

logger = logging.getLogger(__name__)

class TimeAwareAgent:
    """Base class for time-aware agents."""
    
    def __init__(self, name: str, memory_store: MemoryStore, error_handler: ErrorHandler,
                 feedback_system: FeedbackSystem):
        """Initialize agent."""
        self.name = name
        self.memory_store = memory_store
        self.error_handler = error_handler
        self.feedback_system = feedback_system
        
        # Track state vectors (768-dimensional to match embedding model)
        self.state_vectors: Dict[str, np.ndarray] = {}
        
        # Log initialization
        logger.info(f"Initialized {name} with prompt length: {len(self._get_base_prompt())}")
    
    def _get_base_prompt(self) -> str:
        """Get base prompt for agent."""
        return """You are a helpful AI assistant."""
    
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
    
    def _extract_context(self, content: str) -> Tuple[str, Dict]:
        """Extract context from content."""
        # Default implementation just returns content and empty context
        return content, {}
    
    async def get_completion(self, prompt: str) -> str:
        """Get completion from LLM."""
        # This should be overridden by the interactive system
        return "LLM completion not implemented"
    
    async def get_state_similarity(self, vector_type: str, content: str) -> float:
        """Get similarity between content and current state vector."""
        try:
            # Get embedding for content
            embedding = await self.memory_store.embedding_service.get_embedding(content)
            
            # Get current state vector or zero vector if none exists
            current_vector = self.state_vectors.get(vector_type, np.zeros(768))
            
            # Calculate magnitudes
            embedding_norm = np.linalg.norm(embedding)
            current_norm = np.linalg.norm(current_vector)
            
            # Handle zero magnitude vectors
            if embedding_norm == 0 or current_norm == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = float(np.dot(embedding, current_vector) / (embedding_norm * current_norm))
            
            # Ensure similarity is within [-1, 1]
            return max(min(similarity, 1.0), -1.0)
            
        except Exception as e:
            error_msg = f"Error calculating state similarity: {str(e)}"
            logger.error(error_msg)
            await self.error_handler.report_error(
                error_type="state_similarity_error",
                source_agent=self.name,
                details={"error": error_msg, "vector_type": vector_type},
                severity=2,
                context={"activity": "get_state_similarity"}
            )
            return 0.0
    
    async def update_state_vector(self, vector_type: str, content: str) -> None:
        """Update state vector with new content."""
        try:
            # Get embedding for content
            embedding = await self.memory_store.embedding_service.get_embedding(content)
            
            # Ensure embedding is not zero vector
            if np.linalg.norm(embedding) == 0:
                logger.warning(f"Got zero embedding for content in {self.name}")
                return
            
            # Update state vector (simple replacement for now)
            self.state_vectors[vector_type] = embedding
            
        except Exception as e:
            error_msg = f"Error updating state vector: {str(e)}"
            logger.error(error_msg)
            await self.error_handler.report_error(
                error_type="state_vector_update_error",
                source_agent=self.name,
                details={"error": error_msg, "vector_type": vector_type},
                severity=2,
                context={"activity": "update_state_vector"}
            )
    
    async def store_memory(self, memory_type: str, content: Dict[str, Any],
                          metadata: Optional[Dict] = None) -> None:
        """Store memory in persistence layer."""
        try:
            await self.memory_store.store_memory(
                agent_name=self.name,
                memory_type=memory_type,
                content=content,
                metadata=metadata
            )
            logger.info(f"Stored {memory_type} memory for {self.name}")
            
        except Exception as e:
            error_msg = f"Error storing memory: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            await self.error_handler.report_error(
                error_type="memory_storage_error",
                source_agent=self.name,
                details={"error": error_msg, "memory_type": memory_type},
                severity=2,
                context={"activity": "store_memory"}
            )
    
    async def process_interaction(self, content: str) -> str:
        """Process interaction and return response."""
        raise NotImplementedError("Subclasses must implement process_interaction")
    
    async def reflect(self) -> Dict:
        """Reflect on agent state."""
        raise NotImplementedError("Subclasses must implement reflect")
