"""Vector store implementation with enhanced serialization support."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from .embeddings import EmbeddingService
from .memory_types import JSONSerializable

logger = logging.getLogger(__name__)

def serialize_for_vector_store(obj: Any) -> Any:
    """Serialize objects for vector store."""
    if isinstance(obj, JSONSerializable):
        return obj.dict()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_vector_store(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_vector_store(i) for i in obj]
    return obj

class VectorStore:
    """Vector store for memory embeddings."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        host: str = "localhost",
        port: int = 6333
    ):
        """Initialize vector store."""
        self.embedding_service = embedding_service
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "memories"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure collection exists."""
        try:
            collections = self.client.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # Default embedding size
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error ensuring collection: {str(e)}")
    
    async def store_vector(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        layer: str = "episodic"
    ) -> bool:
        """Store vector in collection."""
        try:
            # Serialize content and metadata
            serialized_content = serialize_for_vector_store(content)
            serialized_metadata = serialize_for_vector_store(metadata) if metadata else {}
            
            # Convert content to string for embedding
            if isinstance(serialized_content, dict):
                content_str = json.dumps(serialized_content)
            else:
                content_str = str(serialized_content)
            
            # Get embedding
            embedding = await self.embedding_service.get_embedding(content_str)
            
            # Generate unique ID
            point_id = str(uuid.uuid4())
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "content": serialized_content,
                            "metadata": serialized_metadata,
                            "layer": layer,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                ]
            )
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            return False
    
    async def search_vectors(
        self,
        content: Any,
        limit: int = 5,
        score_threshold: float = 0.7,
        include_metadata: bool = True,
        layer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            # Serialize content for consistent comparison
            serialized_content = serialize_for_vector_store(content)
            
            # Convert content to string for embedding
            if isinstance(serialized_content, dict):
                content_str = json.dumps(serialized_content)
            else:
                content_str = str(serialized_content)
            
            # Get embedding
            embedding = await self.embedding_service.get_embedding(content_str)
            
            # Build search filter
            search_filter = None
            if layer:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="layer",
                            match=models.MatchValue(value=layer)
                        )
                    ]
                )
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Format results
            memories = []
            for result in results:
                memory = {
                    "content": result.payload["content"],
                    "score": result.score
                }
                if include_metadata:
                    memory["metadata"] = result.payload.get("metadata", {})
                    memory["layer"] = result.payload.get("layer", "unknown")
                    memory["timestamp"] = result.payload.get("timestamp")
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    async def delete_vectors(
        self,
        ids: Optional[List[str]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Delete vectors from collection."""
        try:
            if ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(
                        points=ids
                    )
                )
            elif filter_conditions:
                filter_obj = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=k,
                            match=models.MatchValue(value=v)
                        )
                        for k, v in filter_conditions.items()
                    ]
                )
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.FilterSelector(
                        filter=filter_obj
                    )
                )
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up vector store."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception as e:
            logger.error(f"Error cleaning up vector store: {str(e)}")
