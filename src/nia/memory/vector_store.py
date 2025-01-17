"""Vector store implementation using Qdrant."""

import json
import logging
import uuid
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
            model_name = self.embedding_service.model.replace("/", "_").replace("@", "_")
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

    async def connect(self):
        """Initialize connection and collections."""
        try:
            # Get client instance
            client = self.client
            
            # Get embedding dimension and model info
            dimension = await self.embedding_service.dimension
            model_name = self.embedding_service.model.replace("/", "_").replace("@", "_")
            self._collection_name = f"memories_{model_name}_{dimension}d"
            
            logger.info(f"Using collection: {self._collection_name} for {dimension}-dimensional vectors")
            
            # Check if collection exists
            try:
                collections = client.get_collections()
                if not collections:
                    raise ValueError("Failed to retrieve collections")
                    
                # Check if our collection exists
                collection_exists = False
                for c in collections:
                    collection_name = self._get_collection_name_from_info(c)
                    if collection_name == self._collection_name:
                        collection_exists = True
                        break
                        
                if collection_exists:
                    logger.info(f"Using existing collection {self._collection_name}")
                    # Verify collection is properly initialized and update optimizer config
                    collection_info = client.get_collection(self._collection_name)
                    if not collection_info:
                        raise ValueError(f"Collection {self._collection_name} exists but cannot be accessed")
                    
                    # Update optimizer config for existing collection
                    client.update_collection(
                        collection_name=self._collection_name,
                        optimizer_config=models.OptimizersConfigDiff(
                            indexing_threshold=10,  # Lower threshold for test data
                            memmap_threshold=10,  # Lower threshold for test data
                            default_segment_number=2,  # Use multiple segments
                            vacuum_min_vector_number=0,  # Clean up immediately
                            max_optimization_threads=4  # Use multiple threads
                        )
                    )
                    logger.info("Collection verified and optimizer config updated")
            except Exception as e:
                logger.error(f"Error checking collections: {str(e)}")
                raise ValueError(f"Failed to verify collection state: {str(e)}")
                
            # Create collection if it doesn't exist
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
                            vacuum_min_vector_number=0,  # Clean up immediately
                            max_optimization_threads=4  # Use multiple threads
                        )
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise
                    logger.warning(f"Collection {self._collection_name} already exists")
            
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
            
            # Create indexes with wait=true and verify
            for field_name, field_schema in required_indexes:
                logger.info(f"Creating index for {field_name}")
                try:
                    client.create_payload_index(
                        collection_name=self._collection_name,
                        field_name=field_name,
                        field_schema=field_schema,
                        wait=True  # Wait for index to be created
                    )
                    # Wait for index to be ready
                    import time
                    time.sleep(0.5)  # Give time for index to be ready
                    
                    # Verify index exists
                    collection_info = client.get_collection(self._collection_name)
                    if not collection_info:
                        raise Exception(f"Failed to verify collection {self._collection_name}")
                        
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

    def _normalize_vector(self, vector: Union[List[float], np.ndarray]) -> List[float]:
        """Normalize vector to unit length.
        
        Args:
            vector: Input vector
            
        Returns:
            List[float]: Normalized vector
            
        Raises:
            ValueError: If vector cannot be normalized
        """
        try:
            # Convert to numpy array if needed
            if isinstance(vector, list):
                vector = np.array(vector, dtype=np.float32)
            elif not isinstance(vector, np.ndarray):
                raise ValueError(f"Invalid vector type: {type(vector)}")
                
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector.tolist()
        except Exception as e:
            raise ValueError(f"Failed to normalize vector: {str(e)}")
            
    def _convert_point_to_dict(self, point: Union[Record, ScoredPoint, Dict]) -> Dict:
        """Convert point to dictionary format.
        
        Args:
            point: Point to convert
            
        Returns:
            Dict: Point as dictionary
        """
        if isinstance(point, (Record, ScoredPoint)):
            # Convert Record/ScoredPoint to dict
            point_dict = {}
            for key in ['id', 'payload', 'vector']:
                if hasattr(point, key):
                    point_dict[key] = getattr(point, key)
            if isinstance(point, ScoredPoint) and hasattr(point, 'score'):
                point_dict['score'] = point.score
            return point_dict
        elif isinstance(point, dict):
            return point
        else:
            raise ValueError(f"Invalid point type: {type(point)}")
            
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
            vector = models.Vector(list=vector_list)  # Create Vector instance first
            point = models.PointStruct(
                id=point_id,
                vector=vector,  # Use Vector instance
                payload=payload
            )
            
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
            
            result = client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=True
            )
            
            # Verify stored vector
            stored = client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_vectors=True
            )
            if not stored or not stored[0].vector:
                raise ValueError("Failed to verify stored vector")
            
            # Convert vector to list and get first few values safely
            try:
                stored_point = self._convert_point_to_dict(stored[0])
                stored_vector = stored_point.get('vector')
                if not isinstance(stored_vector, (list, np.ndarray)):
                    raise ValueError(f"Invalid vector type: {type(stored_vector)}")
                    
                vector_list = list(stored_vector)
                dimension = len(vector_list)
                first_values = vector_list[:5] if dimension >= 5 else vector_list
                
                logger.info(
                    f"Vector stored and verified:\n"
                    f"- ID: {point_id}\n"
                    f"- Stored dimension: {dimension}\n"
                    f"- First values: {first_values}"
                )
            except (AttributeError, TypeError, IndexError) as e:
                raise ValueError(f"Failed to process stored vector: {str(e)}")
            
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
            query_vector = self._normalize_vector(query_vector)
                
            # Get first few values safely
            first_values = query_vector[:5] if len(query_vector) >= 5 else query_vector
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
            
            try:
                # Create single filter combining all conditions
                search_filter = None
                if must_conditions:
                    search_conditions = [models.Condition(c) for c in must_conditions]
                    search_filter = models.Filter(must=search_conditions)

                # Perform single search operation
                results = client.search(
                    collection_name=target_collection,
                    query_vector=query_vector,
                    query_filter=search_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                    with_vectors=False
                )
                logger.info(f"Search results: {json.dumps(results, default=str, indent=2)}")
                    
                # Process results
                processed = []
                if results:
                    for hit in results:
                        if isinstance(hit, models.ScoredPoint):
                            point_dict = self._convert_point_to_dict(hit)
                            payload = point_dict.get('payload', {})
                            
                            # Log match details
                            logger.info(
                                f"Found match:\n"
                                f"- Score: {point_dict.get('score')}\n"
                                f"- Content: {payload.get('content')}\n"
                                f"- Layer: {payload.get('layer')}"
                            )
                            
                            # Extract metadata from flattened structure
                            metadata = {}
                            for k, v in payload.items():
                                if k.startswith('metadata_'):
                                    metadata[k[9:]] = v  # Remove metadata_ prefix
                            
                            result = {
                                "content": payload.get("content"),
                                "metadata": metadata,
                                "layer": payload.get("layer"),
                                "timestamp": payload.get("timestamp")
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
            except Exception as e:
                logger.error(f"Failed to verify collection: {str(e)}")
                raise
            
            # Get points with a single request through scroll API
            try:
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
                
                # Log points for inspection
                for point in points:
                    point_dict = self._convert_point_to_dict(point)
                    logger.info(f"Point {point_dict.get('id')}:")
                    try:
                        logger.info(f"Payload: {json.dumps(point_dict.get('payload', {}), indent=2)}")
                    except TypeError:
                        # Handle non-JSON serializable types
                        logger.info("Payload: (non-JSON serializable)")
                        for k, v in point_dict.get('payload', {}).items():
                            logger.info(f"  {k}: {v}")
                
                logger.info(f"Total points found: {len(points)}")
                
                # Convert Record objects to dicts
                return [self._convert_point_to_dict(p) for p in points]
            except Exception as e:
                logger.error(f"Failed to get points: {str(e)}")
                return []
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
                selector = models.PointIdsList(points=cast(List[str], point_ids))
                
                # Delete points with selector
                client.delete(
                    collection_name=target_collection,
                    points_selector=selector,
                    wait=True  # Wait for operation to complete
                )
                
                # Verify deletion
                remaining = client.retrieve(
                    collection_name=target_collection,
                    ids=point_ids,
                    with_payload=False
                )
                if remaining:
                    raise ValueError(f"Failed to delete some vectors: {[p.id for p in remaining]}")
                    
                logger.info("Successfully deleted vectors")
            except Exception as e:
                logger.error(f"Failed to delete vectors: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise
