"""
Vector store implementation using Qdrant.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

class VectorStore:
    """Qdrant-based vector store."""
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "memories",
        dim: int = 384  # Default for all-MiniLM-L6-v2
    ):
        """Initialize Qdrant client."""
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.dim = dim
        
        # Initialize collection
        self.initialize_collection()
    
    def initialize_collection(self) -> None:
        """Initialize vector collection."""
        try:
            # Create collection if it doesn't exist
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dim,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created collection {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    async def store_vector(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None,
        layer: str = "semantic"
    ) -> str:
        """Store vector in collection."""
        try:
            # Generate UUID for point ID
            point_id = str(uuid.uuid4())
            
            # Serialize datetime objects in content and metadata
            content = serialize_datetime(content)
            metadata = serialize_datetime(metadata) if metadata else {}
            
            # Add layer and timestamp to metadata
            metadata.update({
                "layer": layer,
                "timestamp": datetime.now().isoformat(),
                "id": point_id  # Store original ID in metadata
            })
            
            # Convert content to JSON string
            content_str = json.dumps(content)
            
            # Generate temporary random vector (replace with actual embeddings)
            temp_vector = np.random.rand(self.dim).tolist()
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,  # Use UUID string as ID
                        vector=temp_vector,  # Required vector field
                        payload={
                            "content": content_str,
                            "metadata": metadata
                        }
                    )
                ]
            )
            
            return point_id
            
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            raise
    
    async def search_vectors(
        self,
        content: Dict[str, Any],
        filter: Optional[Dict] = None,
        limit: int = 10,
        layer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search vectors by similarity."""
        try:
            # Serialize datetime objects in content
            content = serialize_datetime(content)
            
            # Convert content to JSON string
            content_str = json.dumps(content)
            
            # Generate temporary query vector (replace with actual embeddings)
            query_vector = np.random.rand(self.dim).tolist()
            
            # Build search filter
            search_filter = {}
            if filter:
                search_filter.update(filter)
            if layer:
                search_filter["metadata.layer"] = layer
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,  # Required query vector
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=k,
                            match=models.MatchValue(value=v)
                        )
                        for k, v in search_filter.items()
                    ]
                ) if search_filter else None,
                limit=limit
            )
            
            # Process results
            memories = []
            for result in results:
                try:
                    content = json.loads(result.payload["content"])
                    metadata = result.payload.get("metadata", {})
                    memories.append({
                        "id": metadata.get("id", result.id),  # Use original ID from metadata
                        "content": content,
                        "metadata": metadata,
                        "score": result.score
                    })
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode content for vector {result.id}")
                    continue
            
            return memories
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Get vector store status."""
        try:
            collections = self.client.get_collections()
            collection = next(
                (c for c in collections.collections if c.name == self.collection_name),
                None
            )
            
            if collection:
                return {
                    "name": collection.name,
                    "vectors_count": collection.vectors_count,
                    "status": "ready"
                }
            
            return {
                "name": self.collection_name,
                "status": "not_found"
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "name": self.collection_name,
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Clean up vector store."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection {self.collection_name}")
            
            # Recreate collection
            self.initialize_collection()
            
        except Exception as e:
            logger.error(f"Error cleaning up vector store: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close vector store connection."""
        try:
            self.client.close()
            logger.info("Closed vector store connection")
        except Exception as e:
            logger.error(f"Error closing vector store: {str(e)}")
            raise
