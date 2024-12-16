"""
Error handling and tracking.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from .persistence import MemoryStore

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handles error tracking and reporting."""
    
    def __init__(self, memory_store: MemoryStore):
        """Initialize error handler."""
        self.memory_store = memory_store
        self.error_count = 0
        self.error_types = {}
    
    async def report_error(self, error_type: str, source_agent: str,
                          details: Dict[str, Any], severity: int,
                          context: Dict[str, Any]):
        """Report and store an error."""
        try:
            # Update error stats
            self.error_count += 1
            self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
            
            # Store error in memory
            self.memory_store.store_memory(
                agent_name=source_agent,
                memory_type="error",
                content={
                    'error_type': error_type,
                    'details': details,
                    'severity': severity,
                    'context': context,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Log error
            logger.error(
                f"Error from {source_agent}: {error_type} "
                f"(severity: {severity})\n"
                f"Details: {details}\n"
                f"Context: {context}"
            )
            
        except Exception as e:
            logger.error(f"Error in error handling: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Get error statistics."""
        return {
            'total_errors': self.error_count,
            'error_types': self.error_types
        }
