"""Vector store implementation using Qdrant."""

import json
import logging
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Union, Sequence, cast
from datetime import datetime
import numpy as np
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Record, ScoredPoint
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
    def client(self):
        """Get or create singleton client instance with connection pooling."""
        if VectorStore._client_instance is None:
            VectorStore._client_instance = QdrantClient(
                url=f"http://{self.host}:{self.port}",
                timeout=30,  # Increased timeout
                prefer_grpc=False,  # Force HTTP
                https=False  # Disable HTTPS to prevent cert issues
            )
        return VectorStore._client_instance

    async def get_collection_name(self) -> str:
        """Get the current collection name."""
        if not self._collection_name:
            # Get embedding dimension and model info
            dimension = await self.embedding_service.dimension
            # Handle model name with quantization format
            model_name = self.embedding_service.model
            # Replace slashes first
            model_name = model_name.replace("/", "_")
            # Replace @ with _ for consistency
            model_name = model_name.replace(" ", "_").replace("@", "_")
            self._collection_name = f"memories_{model_name}_{dimension}d"
        return self._collection_name

    def _get_collection_name_from_info(self, collection_info: Any) -> Optional[str]:
        """Extract collection name from collection info object.
        
        Args:
            collection_info: Collection info object from Qdrant
            
        Returns:
            str: Collection name if found, None otherwise
        """
        if isinstance(collection_info, tuple):
            return str(collection_info[0]) if len(collection_info) > 0 else None
        elif hasattr(collection_info, 'name'):
            return str(collection_info.name)
        return None

    async def connect(self, max_retries=5, retry_delay=2):
        """Initialize connection and collections."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Get client instance
                client = self.client
                
                # Get embedding dimension and model info
                dimension = await self.embedding_service.dimension
                # Handle model name with quantization format
                model_name = self.embedding_service.model
                # Replace special characters with underscore
                model_name = model_name.replace("/", "_").replace(" ", "_").replace("@", "_")
                self._collection_name = f"memories_{model_name}_{dimension}d"
                
                logger.info(f"Using collection: {self._collection_name} for {dimension}-dimensional vectors")
                
                # Check if collection exists first
                collections = client.get_collections()
                collection_exists = False
                for c in collections:
                    collection_name = self._get_collection_name_from_info(c)
                    if collection_name == self._collection_name:
                        collection_exists = True
                        break
                
                if not collection_exists:
                    logger.info(f"Creating collection {self._collection_name} with {dimension} dimensions")
                    try:
                        client.create_collection(
                            collection_name=self._collection_name,
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
                                vacuum_min_vector_number=100,  # Minimum value required by Qdrant
                                max_optimization_threads=4  # Use multiple threads
                            )
                        )
                        logger.info(f"Created collection {self._collection_name}")
                    except Exception as e:
                        if "already exists" in str(e):
                            logger.info(f"Collection {self._collection_name} already exists")
                        else:
                            raise
                
                # Get collection info to verify configuration
                try:
                    collection_info = client.get_collection(self._collection_name)
                    logger.info(f"Retrieved collection info for {self._collection_name}")
                except Exception as e:
                    logger.error(f"Failed to get collection info: {str(e)}")
                    raise

                # Verify collection configuration
                if collection_info:
                    config = collection_info.config
                    if not config or not hasattr(config, 'params'):
                        raise ValueError(f"Invalid collection configuration for {self._collection_name}")
                    
                    # Get vector size from the vector params
                    vector_params = config.params.vectors
                    if not vector_params:
                        raise ValueError(f"Invalid vector configuration for {self._collection_name}")
                    
                    # Handle both dict and VectorParams object cases
                    if isinstance(vector_params, dict):
                        vector_size = vector_params.get('size')
                        if vector_size is None:
                            raise ValueError(f"Invalid vector configuration for {self._collection_name}")
                    else:
                        # Assume it's a VectorParams object
                        try:
                            vector_size = vector_params.size
                        except AttributeError:
                            raise ValueError(f"Invalid vector configuration for {self._collection_name}")
                            
                    if vector_size != dimension:
                        raise ValueError(
                            f"Collection {self._collection_name} has wrong dimension: "
                            f"expected {dimension}, got {vector_size}"
                        )
                    logger.info(f"Verified collection {self._collection_name} configuration")
                
                logger.info(f"Using collection: {self._collection_name}")
                
                # Define and create required indexes
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
                
                # Create required indexes without checking existing ones
                for field_name, field_schema in required_indexes:
                    try:
                        client.create_payload_index(
                            collection_name=self._collection_name,
                            field_name=field_name,
                            field_schema=field_schema,
                            wait=True  # Wait for index to be created
                        )
                        logger.info(f"Created index for {field_name}")
                    except Exception as e:
                        if "already exists" in str(e):
                            logger.info(f"Index {field_name} already exists")
                        else:
                            logger.error(f"Failed to create index {field_name}: {str(e)}")
                            raise

                # Wait for indexes to be ready
                import time
                time.sleep(0.5)
                logger.info("Vector store connection initialized with verified indexes")
                return
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to initialize vector store after {max_retries} retries: {str(e)}")
                    raise
                logger.warning(f"Retry {retry_count}/{max_retries} after error: {str(e)}")
                await asyncio.sleep(retry_delay * retry_count)

    def _normalize_vector(self, vector: Union[List[float], np.ndarray, List[List[float]]]) -> List[float]:
        """Normalize vector to unit length.
        
        Args:
            vector: Input vector
            
        Returns:
            List[float]: Normalized vector
            
        Raises:
            ValueError: If vector cannot be normalized
        """
        # Convert to numpy array if needed
        try:
            if isinstance(vector, list):
                # Handle nested lists
                if vector and isinstance(vector[0], list):
                    vector = np.array(vector[0], dtype=np.float32)
                else:
                    vector = np.array(vector, dtype=np.float32)
            elif not isinstance(vector, np.ndarray):
                raise ValueError(f"Invalid vector type: {type(vector)}")
                
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            # Convert to list and ensure float type
            result = [float(x) for x in vector.tolist()]
            return result
        except Exception as e:
            raise ValueError(f"Failed to normalize vector: {str(e)}")
            
    def _convert_point_to_dict(self, point: Union[Record, ScoredPoint, Dict]) -> Dict:
        """Convert point to dictionary format.
        
        Args:
            point: Point to convert
            
        Returns:
            Dict: Point as dictionary
        """
        if isinstance(point, dict):
            return point
        
        # For Record/ScoredPoint, directly access attributes
        result = {
            'id': getattr(point, 'id', None),
            'payload': getattr(point, 'payload', {}),
            'vector': getattr(point, 'vector', None)
        }
        
        # Add score for ScoredPoint
        if isinstance(point, ScoredPoint):
            result['score'] = getattr(point, 'score', None)
            
        return result
            
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
            if not isinstance(vector, (list, np.ndarray)):
                raise ValueError(f"Invalid vector type from embedding service: {type(vector)}")
            vector_list = self._normalize_vector(vector)
                
            # Get first few values safely
            first_values = vector_list[:5] if len(vector_list) >= 5 else vector_list
            logger.info(f"Normalized storage vector first values: {first_values}")
            
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
            
            # Create point with proper typing
            point_id = str(uuid.uuid4())
            try:
                # Create point with vector
                point = models.PointStruct(
                    id=point_id,
                    vector=vector_list,  # Vector list is already normalized
                    payload=payload
                )
            except Exception as e:
                logger.error(f"Failed to create point: {str(e)}")
                raise ValueError(f"Failed to create point: {str(e)}")
            
            logger.debug(f"Creating point with metadata: {metadata}")
            logger.debug(f"Creating point with payload: {point.payload}")
            
            # Store point using client
            client = self.client
            
            # Get current collection name
            collection_name = self._collection_name
            if not collection_name:
                collection_name = await self.get_collection_name()
                
            # Log vector details for verification
            logger.info(
                f"Storing vector:\n"
                f"- Collection: {collection_name}\n"
                f"- ID: {point_id}\n"
                f"- Dimension: {len(vector_list)}\n"
                f"- Content: {content_str[:100]}...\n"
                f"- Layer: {layer}"
            )
            
            # Store vector without verification
            client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=True
            )
            
            logger.info(
                f"Vector stored successfully:\n"
                f"- ID: {point_id}\n"
                f"- Dimension: {len(vector_list)}\n"
                f"- First values: {vector_list[:5] if len(vector_list) >= 5 else vector_list}"
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to store vector: {str(e)}")
            raise
            
    async def delete_vector(self, vector_id: str):
        """Delete a vector by ID."""
        await self.delete_vectors([vector_id])

    async def cleanup(self):
        """Clean up resources."""
        try:
            # Close client connection if it exists
            if VectorStore._client_instance:
                VectorStore._client_instance.close()
                VectorStore._client_instance = None
            logger.info("Vector store cleanup complete")
        except Exception as e:
            logger.error(f"Failed to clean up vector store: {str(e)}")
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
            query_vector_list = self._normalize_vector(query_vector)
                
            # Get first few values safely
            first_values = query_vector_list[:5] if len(query_vector_list) >= 5 else query_vector_list
            logger.info(f"Normalized query vector first values: {first_values}")
            
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
            
            # Use current collection if none specified
            target_collection = collection_name or self._collection_name
            if not target_collection:
                target_collection = await self.get_collection_name()
            if not target_collection:
                raise ValueError("No collection available - not initialized")
            
            # Execute search with client
            logger.info("Executing search...")
            client = self.client
            
            # Create single filter combining all conditions
            search_filter = None
            if must_conditions:
                # Use conditions directly since they are already properly typed
                search_filter = models.Filter(
                    must=must_conditions,
                    should=None,
                    must_not=None,
                    min_should=None
                )

            # Perform search operation
            results = client.search(
                collection_name=target_collection,
                query_vector=query_vector_list,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Process results
            processed = []
            for hit in results:
                if isinstance(hit, models.ScoredPoint):
                    payload = getattr(hit, 'payload', {})
                    
                    # Extract metadata from flattened structure
                    metadata = {}
                    for k, v in payload.items():
                        if k.startswith('metadata_'):
                            metadata[k[9:]] = v  # Remove metadata_ prefix
                    
                    result = {
                        "content": payload.get("content"),
                        "metadata": metadata,
                        "layer": payload.get("layer"),
                        "timestamp": payload.get("timestamp"),
                        "score": getattr(hit, 'score', None)
                    }
                    processed.append(result)
            
            return processed
                
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
            
            # Get client instance
            client = self.client
            
            # Use provided collection name or default to initialized one
            target_collection = collection_name or self._collection_name
            if not target_collection:
                target_collection = await self.get_collection_name()
            if not target_collection:
                raise ValueError("No collection available - not initialized")
            
            client.set_payload(
                collection_name=target_collection,
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
            if not target_collection:
                target_collection = await self.get_collection_name()
            logger.info(f"Inspecting collection: {target_collection}")
            
            # Get client instance
            client = self.client
            
            # Check if collection exists
            try:
                # Check if collection exists
                collections = client.get_collections()
                collection_exists = False
                for c in collections:
                    collection_name = self._get_collection_name_from_info(c)
                    if collection_name == target_collection:
                        collection_exists = True
                        break
                        
                if not collection_exists:
                    raise ValueError(f"Collection {target_collection} not found")
                logger.info(f"Collection {target_collection} exists")
                
                # Get points with a single request through scroll API
                batch = client.scroll(
                    collection_name=target_collection,
                    limit=1000,  # Increased limit to get more points at once
                    with_payload=True,
                    with_vectors=False
                )
                
                if not batch or not batch[0]:
                    logger.info("No points found in collection")
                    return []
                    
                points = batch[0]
                
                # Convert Record objects to dicts and return
                return [self._convert_point_to_dict(p) for p in points]
                
            except Exception as e:
                logger.error(f"Failed to inspect collection: {str(e)}")
                raise
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
            
            # Get client instance
            client = self.client
            
            # Use provided collection name or default to initialized one
            target_collection = collection_name or self._collection_name
            if not target_collection:
                target_collection = await self.get_collection_name()
            if not target_collection:
                raise ValueError("No collection available - not initialized")
            
            try:
                # Convert vector_ids to list of strings and create selector
                point_ids = [str(vid) for vid in vector_ids]
                selector = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="id",
                            match=models.MatchAny(any=point_ids)
                        )
                    ]
                )
                
                # Delete points without verification
                client.delete(
                    collection_name=target_collection,
                    points_selector=selector,
                    wait=True  # Wait for operation to complete
                )
                logger.info("Successfully deleted vectors")
                
            except Exception as e:
                logger.error(f"Failed to delete vectors: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise
