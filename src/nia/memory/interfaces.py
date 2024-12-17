"""Abstract base classes for interfaces."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class LLMInterfaceBase(ABC):
    """Abstract base class for LLM interfaces."""
    
    @abstractmethod
    async def get_completion(self, prompt: str) -> str:
        """Get raw text completion."""
        pass
    
    @abstractmethod
    async def get_structured_completion(self, prompt: str) -> Any:
        """Get structured completion."""
        pass
    
    @abstractmethod
    async def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for text."""
        pass
    
    @abstractmethod
    async def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        pass
    
    @abstractmethod
    async def extract_concepts(self, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Extract concepts from text."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close interface."""
        pass
