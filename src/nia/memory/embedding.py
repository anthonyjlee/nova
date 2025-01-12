"""Embedding service for vector store."""

import logging
import numpy as np
from typing import List, Union
from transformers import AutoTokenizer, AutoModel
import torch

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for creating embeddings from text."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize embedding service.
        
        Args:
            model_name: Name of the model to use for embeddings
        """
        try:
            logger.debug(f"Loading tokenizer for model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            logger.debug(f"Loading model: {model_name}")
            self.model = AutoModel.from_pretrained(model_name)
            
            # Move model to GPU if available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = self.model.to(self.device)
            
            logger.info(f"Embedding service initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {str(e)}")
            raise
            
    def _mean_pooling(self, model_output, attention_mask):
        """Mean pooling of token embeddings."""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            
    async def create_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Create embeddings for text.
        
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
                
            # Tokenize texts
            encoded_input = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            # Move inputs to device
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
            
            # Compute token embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                
            # Perform mean pooling
            embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
            
            # Convert to numpy and normalize
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            embeddings = embeddings.cpu().numpy()
            
            # Return single embedding if input was single text
            if isinstance(text, str):
                return embeddings[0].tolist()
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to create embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 384  # Default embedding size
