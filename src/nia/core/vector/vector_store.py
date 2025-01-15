"""Vector store implementation with enhanced serialization support."""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import json
import uuid
import asyncio
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from .embeddings import EmbeddingService
from ..types.memory_types import JSONSerializable

# Disable httpx logging to prevent recursion
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def serialize_for_vector_store(obj: Any, _seen: Optional[set] = None, _depth: int = 0) -> Any:
    """Serialize objects for vector store with cycle detection and depth limiting."""
    # Initialize seen set on first call
    if _seen is None:
        _seen = set()
        
    # Prevent infinite recursion
    if _depth > 10:  # Limit recursion depth
        return str(obj)
        
    # Handle basic types directly
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
        
    # Get object id for cycle detection
    obj_id = id(obj)
    if obj_id in _seen:
        return str(obj)  # Return string representation for cycles
    
    try:
        # Add to seen set for complex types
        if isinstance(obj, (dict, list, JSONSerializable)):
            _seen.add(obj_id)
            
        if isinstance(obj, JSONSerializable):
            return serialize_for_vector_store(obj.dict(minimal=True), _seen, _depth + 1)  # Use minimal serialization
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: serialize_for_vector_store(v, _seen, _depth + 1) 
                   for k, v in list(obj.items())[:100]}  # Limit dictionary size
        elif isinstance(obj, list):
            return [serialize_for_vector_store(i, _seen, _depth + 1) 
                   for i in obj[:100]]  # Limit array size
        return str(obj)
    finally:
        # Remove from seen set when done processing
        if isinstance(obj, (dict, list, JSONSerializable)):
            _seen.discard(obj_id)

class VectorStore:
    """Vector store for memory embeddings."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        host: str = "localhost",
        port: int = 6333,
        pool_size: int = 10
    ):
        """Initialize vector store."""
        self.embedding_service = embedding_service
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.collection_name = "memories"
        self._client_pool = []
        self._pool_lock = asyncio.Lock()
        self._initialize_pool()
        self._ensure_collection()
        
    def _initialize_pool(self):
        """Initialize connection pool."""
        for _ in range(self.pool_size):
            client = QdrantClient(
                host=self.host,
                port=self.port,
                prefer_grpc=True,  # Use gRPC to avoid HTTP middleware
                timeout=30.0  # Add timeout
            )
            self._client_pool.append({
                "client": client,
                "in_use": False,
                "last_used": datetime.now()
            })
    
    async def _get_client(self):
        """Get available client from pool."""
        async with self._pool_lock:
            # First try to find an available client
            for client_info in self._client_pool:
                if not client_info["in_use"]:
                    client_info["in_use"] = True
                    client_info["last_used"] = datetime.now()
                    return client_info
                    
            # If no clients available, create a new one
            client = QdrantClient(
                host=self.host,
                port=self.port,
                prefer_grpc=True,
                timeout=30.0
            )
            client_info = {
                "client": client,
                "in_use": True,
                "last_used": datetime.now()
            }
            self._client_pool.append(client_info)
            return client_info
            
    async def _release_client(self, client_info):
        """Release client back to pool."""
        async with self._pool_lock:
            client_info["in_use"] = False
            client_info["last_used"] = datetime.now()
    
    def _ensure_collection(self):
        """Ensure collection exists."""
        try:
            # Use first client to check collection
            client = self._client_pool[0]["client"]
            collections = client.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                client.create_collection(
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
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
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
            client_info["client"].upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "content": serialized_content,
                            "metadata": serialized_metadata,
                            "layer": layer,
                            "timestamp": datetime.now().isoformat(),
                            # Add metadata fields at top level for querying
                            **{f"metadata_{k}": v for k, v in serialized_metadata.items()}
                        }
                    )
                ]
            )
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            return False
        finally:
            if client_info:
                await self._release_client(client_info)
    
    async def search_vectors(
        self,
        content: Any,
        limit: int = 5,
        score_threshold: float = 0.7,
        include_metadata: bool = True,
        layer: Optional[str] = None,
        filter_conditions: Optional[List[models.FieldCondition]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
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
            conditions = []
            
            # Add layer filter
            if layer:
                conditions.append(
                    models.FieldCondition(
                        key="layer",
                        match=models.MatchValue(value=layer)
                    )
                )
            
            # Add provided filter conditions
            if filter_conditions:
                conditions.extend(filter_conditions)
            
            # Create filter if conditions exist
            search_filter = None
            if conditions:
                search_filter = models.Filter(must=conditions)
            
            # Search in Qdrant
            results = client_info["client"].search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=min(limit, 100),  # Limit maximum results
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Format results
            memories = []
            for result in results:
                # Extract content and metadata
                content = result.payload["content"]
                metadata = result.payload.get("metadata", {})
                
                # Create memory with minimal data
                memory = {
                    "content": content,
                    "score": result.score,
                    "type": (
                        metadata.get("type") or  # First try metadata
                        (content.get("type") if isinstance(content, dict) else None) or  # Then content
                        "unknown"  # Default
                    ),
                    "id": metadata.get("id") or str(uuid.uuid4()),
                    "layer": result.payload.get("layer", "unknown"),
                    "timestamp": result.payload.get("timestamp")
                }
                
                # Include minimal metadata if requested
                if include_metadata:
                    memory["metadata"] = {
                        k: v for k, v in metadata.items()
                        if k in ["type", "id", "thread_id", "task_id", "message_id"]
                    }
                
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
        finally:
            if client_info:
                await self._release_client(client_info)
    
    async def delete_vector(self, point_id: str) -> bool:
        """Delete a single vector from collection."""
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
            client_info["client"].delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[point_id]
                )
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting vector {point_id}: {str(e)}")
            return False
        finally:
            if client_info:
                await self._release_client(client_info)

    async def delete_vectors(
        self,
        ids: Optional[List[str]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Delete vectors from collection."""
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
            if ids:
                # Delete in batches to avoid memory issues
                batch_size = 1000
                for i in range(0, len(ids), batch_size):
                    batch = ids[i:i + batch_size]
                    client_info["client"].delete(
                        collection_name=self.collection_name,
                        points_selector=models.PointIdsList(
                            points=batch
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
                client_info["client"].delete(
                    collection_name=self.collection_name,
                    points_selector=models.FilterSelector(
                        filter=filter_obj
                    )
                )
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            return False
        finally:
            if client_info:
                await self._release_client(client_info)
    
    async def count_vectors(self, layer: Optional[str] = None) -> int:
        """Count vectors in collection."""
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
            # Build filter for layer if specified
            filter_obj = None
            if layer:
                filter_obj = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="layer",
                            match=models.MatchValue(value=layer)
                        )
                    ]
                )
            
            # Get count from Qdrant
            count = client_info["client"].count(
                collection_name=self.collection_name,
                count_filter=filter_obj
            )
            
            return count.count
            
        except Exception as e:
            logger.error(f"Error counting vectors: {str(e)}")
            return 0
        finally:
            if client_info:
                await self._release_client(client_info)
    
    async def clear_vectors(self, layer: Optional[str] = None) -> bool:
        """Clear vectors from collection."""
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
            if layer:
                # Delete vectors from specific layer
                filter_obj = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="layer",
                            match=models.MatchValue(value=layer)
                        )
                    ]
                )
                client_info["client"].delete(
                    collection_name=self.collection_name,
                    points_selector=models.FilterSelector(
                        filter=filter_obj
                    )
                )
            else:
                # Delete all vectors
                client_info["client"].delete_collection(self.collection_name)
                self._ensure_collection()
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vectors: {str(e)}")
            return False
        finally:
            if client_info:
                await self._release_client(client_info)
    
    async def update_metadata(self, point_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a point."""
        client_info = None
        try:
            # Get client from pool
            client_info = await self._get_client()
            
            # Get current payload
            points = client_info["client"].retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            if not points:
                logger.error(f"Point {point_id} not found")
                return False
                
            current_payload = points[0].payload
            
            # Update metadata with minimal data
            serialized_metadata = serialize_for_vector_store(metadata)
            current_payload["metadata"].update(serialized_metadata)
            
            # Update point
            client_info["client"].update_vectors(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        payload={
                            **current_payload,
                            # Update metadata fields at top level for querying
                            **{f"metadata_{k}": v for k, v in serialized_metadata.items()}
                        }
                    )
                ]
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            return False
        finally:
            if client_info:
                await self._release_client(client_info)
            
    async def cleanup(self):
        """Clean up vector store."""
        try:
            # Clear vectors
            await self.clear_vectors()
            
            # Close all clients in pool
            async with self._pool_lock:
                for client_info in self._client_pool:
                    try:
                        client_info["client"].close()
                    except:
                        pass
                self._client_pool.clear()
                
        except Exception as e:
            logger.error(f"Error cleaning up vector store: {str(e)}")
