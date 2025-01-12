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
    
    def __init__(self, embedding_service: EmbeddingService):
        """Initialize vector store.
        
        Args:
            embedding_service: Service for creating embeddings
        """
        self.embedding_service = embedding_service
        self.client = QdrantClient(host="localhost", port=6333)
        
    async def connect(self):
        """Initialize connection and collections."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = "memories" in [c.name for c in collections.collections]
            
            if not collection_exists:
                # Create collection with required indexes
                logger.info("Creating memories collection with indexes")
                self.client.create_collection(
                    collection_name="memories",
                    vectors_config=models.VectorParams(
                        size=384,  # Default embedding size
                        distance=models.Distance.COSINE
                    )
                )
            
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
                ("metadata_importance", models.PayloadSchemaType.FLOAT)
            ]
            
            # Create indexes with wait=true and verify
            for field_name, field_schema in required_indexes:
                logger.info(f"Creating index for {field_name}")
                try:
                    self.client.create_payload_index(
                        collection_name="memories",
                        field_name=field_name,
                        field_schema=field_schema,
                        wait=True  # Wait for index to be created
                    )
                    # Wait for index to be ready
                    import time
                    time.sleep(0.5)  # Give time for index to be ready
                    
                    # Verify index exists
                    collection_info = self.client.get_collection("memories")
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
        collection_name: str,
        payload: dict,
        vector: Optional[List[float]] = None,
        point_id: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """Store a vector in the specified collection with verification.
        
        Args:
            collection_name: Name of collection to store in
            payload: Dictionary containing the data and metadata
            vector: Optional vector embedding. If not provided, will be generated from payload
            point_id: Optional point ID. If not provided, a UUID will be generated
            max_retries: Maximum number of storage attempts
            
        Returns:
            str: ID of stored vector
        """
        try:
            # Use provided point_id or generate a new UUID
            if point_id is None:
                point_id = str(uuid.uuid4())
            logger.info(f"Using point ID: {point_id}")
            
            # Generate vector embedding if not provided
            if vector is None:
                content_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
                vector = await self.embedding_service.create_embedding(content_str)
                logger.info("Generated vector embedding")
            
            # Store with retry logic
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting to store vector (attempt {attempt + 1}/{max_retries})")
                    
                    # Store the point
                    self.client.upsert(
                        collection_name=collection_name,
                        points=[
                            models.PointStruct(
                                id=point_id,
                                vector=vector,
                                payload=payload
                            )
                        ],
                        wait=True  # Wait for operation to complete
                    )
                    logger.info("Vector storage operation completed")
                    
                    # Verify the point was stored
                    logger.info("Verifying stored point...")
                    stored_point = self.client.retrieve(
                        collection_name=collection_name,
                        ids=[point_id],
                        with_payload=True,
                        with_vectors=True
                    )
                    
                    if not stored_point or not stored_point[0]:
                        raise Exception("Point not found after storage")
                        
                    logger.info(f"Successfully verified stored point: {point_id}")
                    return point_id
                    
                except Exception as e:
                    logger.error(f"Storage attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    import time
                    time.sleep(1)  # Wait before retrying
            
            raise Exception(f"Failed to store vector after {max_retries} attempts")
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
        collection_name: str = "memories"
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
            # Convert content to string
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
                
            # Create query embedding
            query_vector = await self.embedding_service.create_embedding(content_str)
            
            # Process and validate filter conditions
            logger.info("Processing filter conditions...")
            must_conditions = []
            has_layer_filter = False
            
            if filter_conditions:
                for condition in filter_conditions:
                    # Log each condition
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
            search_params = {
                "collection_name": collection_name,
                "query_vector": query_vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "with_payload": True
            }
            
            if must_conditions:
                search_params["query_filter"] = models.Filter(must=must_conditions)
            
            logger.info(f"Search parameters: {json.dumps(search_params, default=str, indent=2)}")
            
            # Execute search
            logger.info("Executing search...")
            results = self.client.search(**search_params)
            
            # Log raw results
            logger.info(f"Raw search results: {json.dumps(results, default=str, indent=2)}")
            
            # Process results
            processed = []
            for hit in results:
                result = hit.payload.get("content", {})
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except:
                        pass
                # Add metadata
                metadata = {
                    k[9:]: v for k, v in hit.payload.items()
                    if k.startswith("metadata_")
                }
                if isinstance(result, dict):
                    result.update(metadata)
                processed.append(result)
                
            return processed
        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}")
            return []
            
    async def update_metadata(
        self,
        vector_id: str,
        metadata: Dict,
        collection_name: str = "memories"
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
            self.client.set_payload(
                collection_name=collection_name,
                points=[vector_id],
                payload=payload,
                wait=True  # Wait for operation to complete
            )
        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
            raise
            
    async def inspect_collection(
        self,
        collection_name: str = "memories"
    ) -> List[Dict]:
        """Inspect collection data.
        
        Args:
            collection_name: Collection to inspect
            
        Returns:
            List[Dict]: Collection data
        """
        try:
            logger.info(f"Inspecting collection: {collection_name}")
            
            # Get collection info
            collection_info = self.client.get_collection(collection_name)
            logger.info(f"Collection info: {json.dumps(collection_info.dict(), indent=2)}")
            
            # Get points with a single request
            batch = self.client.scroll(
                collection_name=collection_name,
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
        collection_name: str = "memories"
    ):
        """Delete vectors by ID.
        
        Args:
            vector_ids: IDs of vectors to delete
            collection_name: Collection name
        """
        try:
            logger.info(f"Deleting vectors: {vector_ids}")
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=vector_ids
                ),
                wait=True  # Wait for operation to complete
            )
            logger.info("Successfully deleted vectors")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise
