"""Neo4j memory store."""

import logging
from typing import Dict, List, Optional, Union

from .neo4j import ConceptStore

logger = logging.getLogger(__name__)

class Neo4jMemoryStore(ConceptStore):
    """Neo4j memory store implementation.
    
    This class is maintained for backward compatibility.
    It inherits from ConceptStore which contains the actual implementation.
    """
    
    def __init__(
        self,
        uri: str = "bolt://0.0.0.0:7687",
        user: str = "neo4j",
        password: str = "password",
        max_retry_time: int = 30,
        retry_interval: int = 1,
        llm: Optional['LLMInterface'] = None
    ):
        """Initialize Neo4j store with connection settings."""
        super().__init__(uri, user, password, max_retry_time, retry_interval)
        
        # Initialize LLM interface if not provided
        if llm is None:
            from .llm_interface import LLMInterface
            self.llm = LLMInterface()
        else:
            self.llm = llm
