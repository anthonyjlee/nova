"""Embedding service for vector store."""

import logging
import aiohttp
import json
from typing import List, Union

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for creating embeddings using LM Studio API."""
    
    def __init__(
        self,
        model_name: str = "text-embedding-nomic-embed-text-v1.5@f16",
        api_base: str = "http://127.0.0.1:1234/v1"
    ):
        """Initialize embedding service.
        
        Args:
            model_name: Name of the model to use for embeddings
            api_base: Base URL for the LM Studio API
        """
        self.model = model_name
        self.api_base = api_base
        self._dimension = None  # Will be set on first embedding
        logger.info(f"Embedding service initialized with model: {model_name}")
    
    @property
    async def dimension(self) -> int:
        """Get the embedding dimension for the current model.
        
        Returns:
            int: Number of dimensions in the embedding
        """
        if self._dimension is None:
            # Create a test embedding to determine dimension
            test_embedding = await self.create_embedding("test")
            if isinstance(test_embedding, list):
                self._dimension = len(test_embedding)
                logger.info(f"Model {self.model} produces {self._dimension}-dimensional embeddings")
            else:
                raise ValueError("Failed to determine embedding dimension")
        return self._dimension
            
    async def create_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Create embeddings for text using LM Studio API.
        
        Args:
            text: Text or list of texts to embed
            
        Returns:
            List[float] or List[List[float]]: Embeddings
        """
        try:
            # Ensure text is a list
            if isinstance(text, str):
                texts = [text]
            else:
                texts = text
                
            # Prepare request
            url = f"{self.api_base}/embeddings"
            headers = {"Content-Type": "application/json"}
            data = {
                "model": self.model,
                "input": texts
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error: {error_text}")
                        
                    result = await response.json()
                    
            # Extract embeddings from response
            embeddings = []
            for item in result.get("data", []):
                embedding = item.get("embedding", [])
                if not embedding:
                    raise ValueError("No embedding returned from API")
                embeddings.append(embedding)
            
            # Update dimension if not set
            if self._dimension is None and embeddings:
                self._dimension = len(embeddings[0])
                logger.info(f"Model {self.model} produces {self._dimension}-dimensional embeddings")
            
            # Return single embedding if input was single text
            if isinstance(text, str):
                if not embeddings:
                    raise ValueError("No embedding returned from API")
                return embeddings[0]
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to create embedding: {str(e)}")
            if self._dimension is None:
                raise ValueError("Cannot create fallback vector: dimension not yet determined") 
            # Return zero vector as fallback
            zero_vector = [0.0] * self._dimension
            return zero_vector if isinstance(text, str) else [zero_vector]
