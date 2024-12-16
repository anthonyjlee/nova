"""
Embedding service using local LLM.
"""

import logging
import aiohttp
import numpy as np
from typing import List, Union, Optional
import json

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using local LLM."""
    
    def __init__(self, api_base: str = "http://localhost:1234/v1",
                 api_key: str = "not-needed",
                 model: str = "local",
                 max_tokens: int = 2048,
                 embedding_dim: int = 768):  # Default to 768 for most models
        """Initialize embedding service."""
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.embedding_dim = embedding_dim
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within token limit."""
        # Rough approximation: average English word is 4 characters
        # and typically corresponds to one token
        char_limit = self.max_tokens * 4
        if len(text) > char_limit:
            logger.warning(f"Truncating text from {len(text)} to {char_limit} characters")
            # Try to truncate at a word boundary
            truncated = text[:char_limit]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            # Add EOS token marker
            truncated += " <|endoftext|>"
            return truncated
        return text + " <|endoftext|>"  # Always add EOS token
    
    def _pad_vector(self, vector: List[float], target_dim: int) -> np.ndarray:
        """Pad or truncate vector to target dimension."""
        vector = np.array(vector)
        current_dim = len(vector)
        
        if current_dim == target_dim:
            return vector
        elif current_dim < target_dim:
            # Pad with zeros
            padding = np.zeros(target_dim - current_dim)
            return np.concatenate([vector, padding])
        else:
            # Truncate
            return vector[:target_dim]
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text."""
        try:
            # Truncate text if needed
            text = self._truncate_text(text)
            
            url = f"{self.api_base}/embeddings"
            payload = {
                "model": self.model,
                "input": text,
                "encoding_format": "float"
            }
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to get embedding: {error_text}")
                    
                    result = await response.json()
                    if 'data' in result and len(result['data']) > 0:
                        embedding = result['data'][0]['embedding']
                        # Ensure consistent dimensionality
                        return self._pad_vector(embedding, self.embedding_dim)
                    else:
                        raise Exception("Invalid response format from embedding service")
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dim)
    
    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts."""
        try:
            # Process texts in batches to avoid overwhelming the service
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                # Truncate each text if needed
                batch = [self._truncate_text(text) for text in batch]
                
                url = f"{self.api_base}/embeddings"
                payload = {
                    "model": self.model,
                    "input": batch,
                    "encoding_format": "float"
                }
                
                async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                    async with session.post(url, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Failed to get embeddings: {error_text}")
                        
                        result = await response.json()
                        if 'data' in result:
                            # Sort embeddings by index to maintain order
                            sorted_embeddings = sorted(result['data'], key=lambda x: x['index'])
                            batch_embeddings = [
                                self._pad_vector(item['embedding'], self.embedding_dim) 
                                for item in sorted_embeddings
                            ]
                            all_embeddings.extend(batch_embeddings)
                        else:
                            raise Exception("Invalid response format from embedding service")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            # Return zero vectors as fallback
            return [np.zeros(self.embedding_dim) for _ in texts]
    
    async def get_similarity(self, text1: str, text2: str) -> float:
        """Get cosine similarity between two texts."""
        try:
            # Get embeddings
            embedding1 = await self.get_embedding(text1)
            embedding2 = await self.get_embedding(text2)
            
            # Calculate cosine similarity
            similarity = float(np.dot(embedding1, embedding2) / 
                            (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0  # Return minimum similarity as fallback
    
    async def search_similar(self, query: str, texts: List[str],
                           top_k: Optional[int] = None) -> List[tuple[int, float]]:
        """Search for most similar texts."""
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Get embeddings for all texts
            text_embeddings = await self.get_embeddings(texts)
            
            # Calculate similarities
            similarities = []
            for i, embedding in enumerate(text_embeddings):
                similarity = float(np.dot(query_embedding, embedding) / 
                                (np.linalg.norm(query_embedding) * np.linalg.norm(embedding)))
                similarities.append((i, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k if specified
            if top_k is not None:
                return similarities[:top_k]
            return similarities
            
        except Exception as e:
            logger.error(f"Error searching similar texts: {str(e)}")
            return []  # Return empty list as fallback
