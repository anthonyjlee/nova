"""
Feedback system for tracking and analyzing user feedback.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from .persistence import MemoryStore
from .error_handling import ErrorHandler

logger = logging.getLogger(__name__)

class FeedbackSystem:
    """Handles feedback tracking and analysis."""
    
    def __init__(self, memory_store: MemoryStore, error_handler: ErrorHandler):
        """Initialize feedback system."""
        self.memory_store = memory_store
        self.error_handler = error_handler
        self.feedback_count = 0
        self.feedback_types = {}
    
    async def process_feedback(self, feedback: str, source_agent: str,
                             context: Dict[str, Any]):
        """Process and store user feedback."""
        try:
            # Update feedback stats
            self.feedback_count += 1
            
            # Analyze feedback type
            feedback_type = self._analyze_feedback_type(feedback)
            self.feedback_types[feedback_type] = self.feedback_types.get(feedback_type, 0) + 1
            
            # Store feedback in memory
            self.memory_store.store_memory(
                agent_name=source_agent,
                memory_type="feedback",
                content={
                    'feedback': feedback,
                    'feedback_type': feedback_type,
                    'context': context,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Log feedback
            logger.info(
                f"Feedback for {source_agent}: {feedback_type}\n"
                f"Content: {feedback}\n"
                f"Context: {context}"
            )
            
        except Exception as e:
            await self.error_handler.report_error(
                error_type="feedback_processing_error",
                source_agent=source_agent,
                details={"error": str(e), "feedback": feedback},
                severity=1,
                context=context
            )
    
    def _analyze_feedback_type(self, feedback: str) -> str:
        """Analyze feedback to determine its type."""
        feedback = feedback.lower()
        
        if any(word in feedback for word in ['error', 'bug', 'issue', 'problem']):
            return 'error_report'
        elif any(word in feedback for word in ['improve', 'better', 'should', 'could']):
            return 'suggestion'
        elif any(word in feedback for word in ['good', 'great', 'nice', 'well']):
            return 'positive'
        elif any(word in feedback for word in ['bad', 'poor', 'wrong', 'incorrect']):
            return 'negative'
        else:
            return 'neutral'
    
    def get_stats(self) -> Dict:
        """Get feedback statistics."""
        return {
            'total_feedback': self.feedback_count,
            'feedback_types': self.feedback_types
        }
