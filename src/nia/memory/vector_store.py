"""
Vector store implementation using Qdrant and sentence-transformers.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import torch
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for semantic memory search."""
    
    def __init__(
        self,
        collection_name: str = "memory_vectors",
        model_name: str = "all-MiniLM-L6-v2",
        host: str = "localhost",
        port: int = 6333,
        device: Optional[str] = None
    ):
        """Initialize vector store."""
        self.collection_name = collection_name
        self._vector_id_counter = 0
        
        # Set up PyTorch device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.device = device
        logger.info(f"Using PyTorch device: {device}")
        
        # Initialize sentence transformer model
        self.model = SentenceTransformer(model_name)
        self.model.to(device)
        logger.info(f"Loaded model: {model_name}")
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port)
        self._initialize_collection()
    
    def _initialize_collection(self) -> None:
        """Initialize vector collection."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.model.get_sentence_embedding_dimension(),
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            
            # Reset counter
            self._vector_id_counter = 0
            
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    async def store_vector(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> int:
        """Store content vector."""
        try:
            # Get next vector ID
            vector_id = self._vector_id_counter
            self._vector_id_counter += 1
            
            # Convert content to string for embedding
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            # Generate embedding
            with torch.no_grad():
                vector = self.model.encode(
                    content_str,
                    convert_to_tensor=True,
                    device=self.device
                ).cpu().numpy().tolist()
            
            # Store vector with payload
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=vector_id,
                        vector=vector,
                        payload={
                            'content': content,
                            'metadata': metadata or {},
                            'created_at': datetime.now().isoformat()
                        }
                    )
                ]
            )
            
            logger.info(f"Stored vector: {vector_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            raise
    
    async def search_vectors(
        self,
        content: Dict[str, Any],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            # Convert content to string for embedding
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            # Generate query vector
            with torch.no_grad():
                query_vector = self.model.encode(
                    content_str,
                    convert_to_tensor=True,
                    device=self.device
                ).cpu().numpy().tolist()
            
            # Search vectors
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            memories = []
            for result in results:
                memory = {
                    'id': result.id,
                    'score': result.score,
                    'content': result.payload['content'],
                    'metadata': result.payload['metadata'],
                    'created_at': result.payload['created_at']
                }
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    async def get_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """Get vector by ID."""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id]
            )
            
            if result:
                point = result[0]
                return {
                    'id': point.id,
                    'content': point.payload['content'],
                    'metadata': point.payload['metadata'],
                    'created_at': point.payload['created_at']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting vector: {str(e)}")
            return None
    
    async def cleanup(self) -> None:
        """Clean up vector store."""
        try:
            # Delete collection
            self.client.delete_collection(
                collection_name=self.collection_name
            )
            logger.info(f"Deleted collection: {self.collection_name}")
            
            # Recreate collection
            self._initialize_collection()
            logger.info("Re-initialized vector store")
            
        except Exception as e:
            logger.error(f"Error cleaning up vector store: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close vector store connection."""
        try:
            self.client.close()
            logger.info("Closed vector store connection")
        except Exception as e:
            logger.error(f"Error closing vector store connection: {str(e)}")
            raise
