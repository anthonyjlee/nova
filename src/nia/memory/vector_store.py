"""Vector store implementation using Qdrant."""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
from .embedding import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for memory embeddings using Qdrant."""
    
    _client_instance = None
    _client_lock = None

    def __init__(self, embedding_service: EmbeddingService):
        """Initialize vector store.
        
        Args:
            embedding_service: Service for creating embeddings
        """
        # Read config
        import configparser
        import asyncio
        config = configparser.ConfigParser()
        config.read("config.ini")
        
        self.embedding_service = embedding_service
        self.host = config.get("QDRANT", "host", fallback="127.0.0.1")
        self.port = config.getint("QDRANT", "port", fallback=6333)
        
        # Initialize lock if needed
        if VectorStore._client_lock is None:
            VectorStore._client_lock = asyncio.Lock()
            
        # Initialize collection name
        self._collection_name = None
        
    @property
    async def client(self):
        """Get or create singleton client instance with connection pooling."""
        if VectorStore._client_instance is None:
            async with VectorStore._client_lock:
                if VectorStore._client_instance is None:
                    VectorStore._client_instance = QdrantClient(
                        url=f"http://{self.host}:{self.port}",
                        timeout=10.0,  # Add timeout
                        prefer_grpc=False  # Force HTTP to avoid GRPC recursion
                    )
        return VectorStore._client_instance

    async def connect(self):
        """Initialize connection and collections."""
        try:
            # Get singleton client instance
            client = await self.client
            
            # Get embedding dimension and model info
            dimension = await self.embedding_service.dimension
            model_name = self.embedding_service.model.replace("/", "_").replace("@", "_")
            collection_name = f"memories_{model_name}_{dimension}d"
            
            logger.info(f"Using collection: {collection_name} for {dimension}-dimensional vectors")
            
            # Check if collection exists
            collections = client.get_collections()
            collection_exists = collection_name in [c.name for c in collections.collections]
            
            if not collection_exists:
                # Create collection with required indexes and HNSW config
                logger.info(f"Creating collection {collection_name} with {dimension} dimensions")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=dimension,
                        distance=models.Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(
                            m=16,  # Number of edges per node
                            ef_construct=100,  # Dynamic candidate list size
                            full_scan_threshold=10  # Lower threshold for test data
                        )
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=10,  # Lower threshold for test data
                        memmap_threshold=10,  # Lower threshold for test data
                        default_segment_number=2,  # Use multiple segments
                        vacuum_min_vector_number=0,  # Clean up immediately
                        max_optimization_threads=4  # Use multiple threads
                    )
                )
                
                # Force index optimization
                client.update_collection(
                    collection_name=collection_name,
                    optimizer_config=models.OptimizersConfigDiff(
                        indexing_threshold=10,
                        memmap_threshold=10,
                        default_segment_number=2,
                        vacuum_min_vector_number=0,
                        max_optimization_threads=4
                    )
                )
            
            # Store collection name
            self._collection_name = collection_name
            logger.info(f"Using collection: {self._collection_name}")
            
            # Define required indexes with all metadata fields
            required_indexes = [
                ("metadata_type", models.PayloadSchemaType.KEYWORD),
                ("metadata_thread_id", models.PayloadSchemaType.KEYWORD),
                ("metadata_layer", models.PayloadSchemaType.KEYWORD),
                ("metadata_consolidated", models.PayloadSchemaType.BOOL),
                ("metadata_system", models.PayloadSchemaType.BOOL),
                ("metadata_pinned", models.PayloadSchemaType.BOOL),
                ("metadata_domain", models.PayloadSchemaType.KEYWORD),
                ("metadata_source", models.PayloadSchemaType.KEYWORD),
                ("metadata_timestamp", models.PayloadSchemaType.DATETIME),
                ("metadata_importance", models.PayloadSchemaType.FLOAT),
                ("metadata_id", models.PayloadSchemaType.KEYWORD)  # Add ID field
            ]
            
            # Create indexes with wait=true and verify
            for field_name, field_schema in required_indexes:
                logger.info(f"Creating index for {field_name}")
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_schema,
                        wait=True  # Wait for index to be created
                    )
                    # Wait for index to be ready
                    import time
                    time.sleep(0.5)  # Give time for index to be ready
                    
                    # Verify index exists
                    collection_info = client.get_collection(collection_name)
                    if field_name not in collection_info.payload_schema:
                        raise Exception(f"Index {field_name} not found after creation")
                        
                    logger.info(f"Created and verified index for {field_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.warning(f"Index {field_name} already exists")
            
            # Wait for all indexes to be ready
            time.sleep(1)
            logger.info("Vector store connection initialized with verified indexes")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
            
    async def store_vector(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        layer: str = "episodic"
    ) -> bool:
        """Store a vector in the specified collection.
        
        Args:
            content: Content to store
            metadata: Optional metadata
            layer: Memory layer
            
        Returns:
            bool: True if stored successfully
        """
        try:
            # Convert content to string for embedding
            content_str = json.dumps(content) if isinstance(content, dict) else str(content)
            
            # Generate embedding and normalize
            vector = await self.embedding_service.create_embedding(content_str)
            
            # Normalize vector (L2 norm)
            import numpy as np
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = [x/norm for x in vector]
                
            logger.info(f"Normalized storage vector first 5: {vector[:5]}")
            
            # Create point with flattened metadata
            payload = {
                "content": content,
                "layer": layer,
                "timestamp": datetime.now().isoformat()
            }
            
            # Flatten metadata into payload with metadata_ prefix
            if metadata:
                for k, v in metadata.items():
                    payload[f"metadata_{k}"] = v
            
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload
            )
            
            logger.debug(f"Creating point with metadata: {metadata}")
            
            logger.debug(f"Creating point with payload: {point.payload}")
            
            # Store point using singleton client and current collection
            client = await self.client
            
            # Get current collection info
            collection_info = await self.inspect_collection()
            collection_name = collection_info[0].collection_name if collection_info else None
            if not collection_name:
                raise ValueError("No collection available")
            
            # Log vector details for verification
            logger.info(
                f"Storing vector:\n"
                f"- Collection: {collection_name}\n"
                f"- ID: {point.id}\n"
                f"- Dimension: {len(point.vector)}\n"
                f"- Content: {content_str[:100]}...\n"
                f"- Layer: {layer}"
            )
            
            result = client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=True
            )
            
            # Verify stored vector
            stored = client.retrieve(
                collection_name=collection_name,
                ids=[point.id],
                with_vectors=True
            )
            if not stored or not stored[0].vector:
                raise ValueError("Failed to verify stored vector")
            
            stored_vector = stored[0].vector
            logger.info(
                f"Vector stored and verified:\n"
                f"- ID: {point.id}\n"
                f"- Stored dimension: {len(stored_vector)}\n"
                f"- First 5 values: {stored_vector[:5]}"
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to store vector: {str(e)}")
            raise
            
    async def search_vectors(
        self,
        content: Dict,
        limit: int = 5,
        score_threshold: float = 0.7,
        layer: Optional[str] = None,
        filter_conditions: Optional[List[models.FieldCondition]] = None,
        collection_name: Optional[str] = None
    ) -> List[Dict]:
        """Search for similar vectors.
        
        Args:
            content: Content to search for
            limit: Max results to return
            score_threshold: Minimum similarity score
            layer: Optional layer to search in
            filter_conditions: Optional filter conditions
            collection_name: Collection to search in
            
        Returns:
            List[Dict]: Search results
        """
        try:
            # Handle content for embedding based on type
            if isinstance(content, str):
                content_str = content
            elif isinstance(content, dict):
                # If content has text field, use that
                if 'text' in content:
                    content_str = content['text']
                # Otherwise use the raw dict
                else:
                    content_str = str(content)
            else:
                content_str = str(content)
            
            # Create query embedding and normalize
            query_vector = await self.embedding_service.create_embedding(content_str)
            
            # Normalize query vector (L2 norm)
            import numpy as np
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = [x/norm for x in query_vector]
                
            logger.info(f"Normalized query vector first 5: {query_vector[:5]}")
            
            # Process and validate filter conditions
            logger.info("Processing filter conditions...")
            must_conditions = []
            has_layer_filter = False
            
            if filter_conditions:
                for condition in filter_conditions:
                    logger.info(f"Processing condition: {condition}")
                    
                    if isinstance(condition, models.FieldCondition):
                        if condition.key == "metadata_layer":
                            has_layer_filter = True
                        must_conditions.append(condition)
                    else:
                        logger.warning(f"Skipping invalid condition: {condition}")
            
            # Add layer filter if not already present
            if layer and not has_layer_filter:
                must_conditions.append(
                    models.FieldCondition(
                        key="metadata_layer",
                        match=models.MatchValue(value=layer)
                    )
                )
            
            # Log final filter conditions
            logger.info(f"Final filter conditions: {must_conditions}")
            
            # Construct search parameters
            # Use current collection if none specified
            # Get current collection if none specified
            current_collection = (await self.inspect_collection())[0].collection_name if not collection_name else collection_name
            
            search_params = {
                "collection_name": current_collection,
                "query_vector": query_vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "with_payload": True
            }
            
            if must_conditions:
                search_params["query_filter"] = models.Filter(must=must_conditions)
            
            logger.info(f"Search parameters: {json.dumps(search_params, default=str, indent=2)}")
            
            # Execute search with singleton client
            logger.info("Executing search...")
            client = await self.client
            
            # Log search parameters for debugging
            logger.info(f"Search vector first 5 values: {query_vector[:5]}")
            
            try:
                # Try exact content match first
                exact_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="content",
                            match=models.MatchValue(value=content_str)
                        )
                    ] + must_conditions if must_conditions else []
                )
                
                exact_results = client.search(
                    collection_name=collection_name or (await self.inspect_collection())[0].collection_name,
                    query_vector=query_vector,
                    query_filter=exact_filter,
                    limit=limit,
                    with_payload=True
                )
                
                # Log exact match results
                logger.info(f"Exact match results: {json.dumps(exact_results, default=str, indent=2)}")
                
                # If no exact matches, try similarity search
                if not exact_results:
                    logger.info("No exact matches, trying similarity search...")
                    results = client.search(**search_params)
                    logger.info(f"Similarity search results: {json.dumps(results, default=str, indent=2)}")
                else:
                    results = exact_results
                    
                # Process results
                processed = []
                if results:
                    for hit in results:
                        if hasattr(hit, 'payload'):
                            # Log match details
                            logger.info(
                                f"Found match:\n"
                                f"- Score: {hit.score}\n"
                                f"- Content: {hit.payload.get('content')}\n"
                                f"- Layer: {hit.payload.get('layer')}"
                            )
                            # Extract metadata from flattened structure
                            metadata = {}
                            for k, v in hit.payload.items():
                                if k.startswith('metadata_'):
                                    metadata[k[9:]] = v  # Remove metadata_ prefix
                            
                            result = {
                                "content": hit.payload.get("content"),
                                "metadata": metadata,
                                "layer": hit.payload.get("layer"),
                                "timestamp": hit.payload.get("timestamp")
                            }
                            processed.append(result)
                else:
                    logger.warning("No matches found above threshold")
                
                return processed
                
            except Exception as e:
                logger.error(f"Search failed: {str(e)}")
                return []
        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}")
            return []
            
    async def update_metadata(
        self,
        vector_id: str,
        metadata: Dict,
        collection_name: Optional[str] = None
    ):
        """Update vector metadata.
        
        Args:
            vector_id: ID of vector to update
            metadata: New metadata values
            collection_name: Collection name
        """
        try:
            # Prepare payload with proper type handling
            payload = {}
            for k, v in metadata.items():
                key = f"metadata_{k}"
                # Handle special cases for field types
                if k == "timestamp":
                    # Ensure timestamp is in ISO format
                    if isinstance(v, str):
                        payload[key] = v
                    else:
                        payload[key] = datetime.now().isoformat()
                elif k == "importance":
                    # Ensure importance is float
                    payload[key] = float(v)
                elif k in ["consolidated", "system", "pinned"]:
                    # Handle boolean fields
                    if isinstance(v, str):
                        # Convert string 'true'/'false' to boolean
                        payload[key] = v.lower() == 'true'
                    else:
                        # Use boolean value directly
                        payload[key] = bool(v)
                else:
                    # Default handling
                    payload[key] = v
            
            logger.info(f"Updating metadata with payload: {json.dumps(payload, indent=2)}")
            # Get singleton client instance
            client = await self.client
            
            # Get current collection if none specified
            current_collection = (await self.inspect_collection())[0].collection_name if not collection_name else collection_name
            
            client.set_payload(
                collection_name=current_collection,
                points=[vector_id],
                payload=payload,
                wait=True  # Wait for operation to complete
            )
        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
            raise
            
    async def inspect_collection(
        self,
        collection_name: Optional[str] = None
    ) -> List[Dict]:
        """Inspect collection data.
        
        Args:
            collection_name: Collection to inspect
            
        Returns:
            List[Dict]: Collection data
        """
        try:
            # Use current collection if none specified
            target_collection = collection_name or self._collection_name
            logger.info(f"Inspecting collection: {target_collection}")
            
            # Get singleton client instance
            client = await self.client
            
            collection_info = client.get_collection(target_collection)
            logger.info(f"Collection info: {json.dumps(collection_info.dict(), indent=2)}")
            
            # Get points with a single request
            batch = client.scroll(
                collection_name=target_collection,
                limit=1000,  # Increased limit to get more points at once
                with_payload=True,
                with_vectors=False
            )
            
            points = batch[0] if batch[0] else []
                
            # Log points for inspection
            for point in points:
                logger.info(f"Point {point.id}:")
                try:
                    logger.info(f"Payload: {json.dumps(point.payload, indent=2)}")
                except TypeError:
                    # Handle non-JSON serializable types
                    logger.info("Payload: (non-JSON serializable)")
                    for k, v in point.payload.items():
                        logger.info(f"  {k}: {v}")
            
            logger.info(f"Total points found: {len(points)}")
            return points
        except Exception as e:
            logger.error(f"Failed to inspect collection: {str(e)}")
            raise

    async def delete_vectors(
        self,
        vector_ids: List[str],
        collection_name: Optional[str] = None
    ):
        """Delete vectors by ID.
        
        Args:
            vector_ids: IDs of vectors to delete
            collection_name: Collection name
        """
        try:
            logger.info(f"Deleting vectors: {vector_ids}")
            # Get singleton client instance
            client = await self.client
            
            # Get current collection if none specified
            current_collection = (await self.inspect_collection())[0].collection_name if not collection_name else collection_name
            
            client.delete(
                collection_name=current_collection,
                points_selector=models.PointIdsList(
                    points=vector_ids
                ),
                wait=True  # Wait for operation to complete
            )
            logger.info("Successfully deleted vectors")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise
