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
        # Read config
        import configparser
        config = configparser.ConfigParser()
        config.read("config.ini")
        
        self.embedding_service = embedding_service
        host = config.get("QDRANT", "host", fallback="127.0.0.1")
        port = config.getint("QDRANT", "port", fallback=6333)
        self.client = QdrantClient(url=f"http://{host}:{port}")
        
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
                ("metadata_importance", models.PayloadSchemaType.FLOAT),
                ("metadata_id", models.PayloadSchemaType.KEYWORD)  # Add ID field
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
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        layer: str = "episodic"
    ) -> bool:
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
            # Generate a unique ID for this vector
            point_id = str(uuid.uuid4())
            logger.info(f"Using point ID: {point_id}")
            
            # Convert content to string for embedding
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            # Generate vector embedding
            vector = await self.embedding_service.create_embedding(content_str)
            
            # Prepare payload
            payload = {
                "content": content,
                "metadata": metadata or {},
                "layer": layer,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in Qdrant
            self.client.upsert(
                collection_name="memories",
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ],
                wait=True
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
            
            # Create query embedding from processed content
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
                # Return the complete payload
                processed.append(hit.payload)
                
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
