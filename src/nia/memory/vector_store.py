"""
Vector store implementation using Qdrant and LMStudio embeddings.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import aiohttp
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import CollectionInfo

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for semantic memory search."""
    
    def __init__(
        self,
        collection_name: str = "memory_vectors",
        embedding_url: str = "http://localhost:1234/v1/embeddings",
        embedding_model: str = "text-embedding-nomic-embed-text-v1.5@q8_0",
        vector_size: int = 768,  # Nomic embed dimension
        host: str = "localhost",
        port: int = 6333
    ):
        """Initialize vector store."""
        self.collection_name = collection_name
        self._vector_id_counter = 0
        self.embedding_url = embedding_url
        self.embedding_model = embedding_model
        self.vector_size = vector_size
        
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
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            
            # Reset counter
            self._vector_id_counter = 0
            
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from LMStudio."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.embedding_url,
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Embedding request failed: {response.status}")
                    
                    result = await response.json()
                    if not result.get("data"):
                        raise ValueError("No embedding data in response")
                    
                    embedding = result["data"][0]["embedding"]
                    if not isinstance(embedding, list) or len(embedding) != self.vector_size:
                        raise ValueError(f"Invalid embedding dimension: {len(embedding)}")
                    
                    return embedding
                    
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise
    
    async def store_vector(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None,
        layer: str = "episodic"  # 'episodic' or 'semantic'
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
            
            # Get embedding from LMStudio
            vector = await self._get_embedding(content_str)
            
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
                            'created_at': datetime.now().isoformat(),
                            'layer': layer  # Track memory layer
                        }
                    )
                ]
            )
            
            logger.info(f"Stored vector in {layer} layer: {vector_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            raise
    
    async def search_vectors(
        self,
        content: Dict[str, Any],
        limit: int = 10,
        score_threshold: float = 0.7,
        layer: Optional[str] = None  # Filter by layer if specified
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            # Convert content to string for embedding
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            # Get embedding from LMStudio
            query_vector = await self._get_embedding(content_str)
            
            # Add layer filter if specified
            filter_query = None
            if layer:
                filter_query = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="layer",
                            match=models.MatchValue(value=layer)
                        )
                    ]
                )
            
            # Search vectors
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_query
            )
            
            # Format results
            memories = []
            for result in results:
                memory = {
                    'id': result.id,
                    'score': result.score,
                    'content': result.payload['content'],
                    'metadata': result.payload['metadata'],
                    'created_at': result.payload['created_at'],
                    'layer': result.payload['layer']
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
                    'created_at': point.payload['created_at'],
                    'layer': point.payload['layer']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting vector: {str(e)}")
            return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get vector store status."""
        try:
            # Get collection info
            collection: CollectionInfo = self.client.get_collection(self.collection_name)
            
            # Count vectors by layer
            episodic_count = len(self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="layer",
                            match=models.MatchValue(value="episodic")
                        )
                    ]
                )
            )[0])
            
            semantic_count = len(self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="layer",
                            match=models.MatchValue(value="semantic")
                        )
                    ]
                )
            )[0])
            
            return {
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "total_vectors": collection.points_count,
                "episodic_memories": episodic_count,
                "semantic_memories": semantic_count,
                "embedding_model": self.embedding_model,
                "status": collection.status
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "error": str(e)
            }
    
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
