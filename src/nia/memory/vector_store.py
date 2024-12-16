"""
Vector storage and retrieval using Qdrant.
"""

import logging
import numpy as np
import aiohttp
import json
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
import uuid
from dateutil import parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages vector storage and retrieval using Qdrant."""
    
    def __init__(self, api_base: str = "http://localhost:6333", 
                 api_key: str = None,  # Made API key optional
                 collection_name: str = "memory_vectors",
                 decay_factor: float = 0.995,
                 vector_size: int = 768):  # Match embedding model dimension
        """Initialize vector store."""
        self.api_base = api_base
        self.api_key = api_key
        self.collection_name = collection_name
        self.decay_factor = decay_factor
        self.vector_size = vector_size
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["api-key"] = self.api_key
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def create_collection(self) -> bool:
        """Create collection with schema."""
        try:
            url = f"{self.api_base}/collections/{self.collection_name}"
            payload = {
                "vectors": {
                    "size": self.vector_size,
                    "distance": "Cosine"
                },
                "shard_number": 1,
                "replication_factor": 1,
                "write_consistency_factor": 1,
                "on_disk_payload": True,
                "hnsw_config": {
                    "m": 16,
                    "ef_construct": 100,
                    "full_scan_threshold": 10000
                },
                "optimizers_config": {
                    "deleted_threshold": 0.2,
                    "vacuum_min_vector_number": 1000,
                    "default_segment_number": 2,
                    "indexing_threshold": 20000,
                    "flush_interval_sec": 5,
                    "max_optimization_threads": 1
                },
                "wal_config": {
                    "wal_capacity_mb": 32,
                    "wal_segments_ahead": 0
                }
            }
            
            # First create the collection
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.put(url, json=payload) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        logger.warning(f"Failed to create collection: {response_text}")
                        return False
                    
                    logger.info(f"Created collection: {response_text}")
                    
                    # Now create the payload indexes
                    index_url = f"{url}/index"
                    
                    # Create memory_type index
                    memory_type_payload = {
                        "field_name": "memory_type",
                        "field_type": "keyword"
                    }
                    async with session.put(index_url, json=memory_type_payload) as index_response:
                        index_text = await index_response.text()
                        logger.info(f"Memory type index response: {index_text}")
                        if index_response.status != 200:
                            logger.warning(f"Failed to create memory_type index: {index_text}")
                            return False
                    
                    # Create timestamp index
                    timestamp_payload = {
                        "field_name": "timestamp",
                        "field_type": "keyword"
                    }
                    async with session.put(index_url, json=timestamp_payload) as index_response:
                        index_text = await index_response.text()
                        logger.info(f"Timestamp index response: {index_text}")
                        if index_response.status != 200:
                            logger.warning(f"Failed to create timestamp index: {index_text}")
                            return False
                    
                    # Create importance index
                    importance_payload = {
                        "field_name": "importance",
                        "field_type": "float"
                    }
                    async with session.put(index_url, json=importance_payload) as index_response:
                        index_text = await index_response.text()
                        logger.info(f"Importance index response: {index_text}")
                        if index_response.status != 200:
                            logger.warning(f"Failed to create importance index: {index_text}")
                            return False
                    
                    logger.info("Created all payload indexes")
                    return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return False
    
    async def delete_collection(self) -> None:
        """Delete the collection if it exists."""
        try:
            url = f"{self.api_base}/collections/{self.collection_name}"
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.delete(url) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        logger.info(f"Deleted collection {self.collection_name}")
                    elif response.status != 404:  # 404 means collection didn't exist
                        logger.warning(f"Failed to delete collection: {response_text}")
                        
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
    
    async def init_collection(self, recreate: bool = False) -> None:
        """Initialize or verify collection."""
        try:
            # Delete collection if recreate is True
            if recreate:
                await self.delete_collection()
            
            url = f"{self.api_base}/collections/{self.collection_name}"
            
            # Check if collection exists
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(url) as response:
                    response_text = await response.text()
                    logger.info(f"Collection check response: {response_text}")
                    
                    if response.status == 404 or recreate:
                        # Create collection with schema
                        if not await self.create_collection():
                            logger.error("Failed to create collection with schema")
                            return
                                
                    elif response.status == 200:
                        # Check vector size of existing collection
                        result = json.loads(response_text)
                        existing_size = result.get('result', {}).get('config', {}).get('params', {}).get('vectors', {}).get('size')
                        if existing_size and existing_size != self.vector_size:
                            logger.warning(f"Collection exists with different vector size ({existing_size}). Recreating...")
                            await self.init_collection(recreate=True)
                        else:
                            logger.info(f"Using existing collection {self.collection_name}")
                    else:
                        logger.error(f"Failed to check collection: {response_text}")
                        
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    async def add_vectors(self, vectors: Union[np.ndarray, List[List[float]]], 
                         metadata_list: List[Dict]) -> None:
        """Add vectors with metadata to store."""
        try:
            if len(vectors) != len(metadata_list):
                raise ValueError("Number of vectors must match number of metadata entries")
            
            # Convert vectors and metadata to JSON serializable format
            vectors = [self._pad_vector(v) for v in vectors]  # Ensure correct dimension
            metadata_list = self._convert_to_json_serializable(metadata_list)
            
            # Prepare points
            points = []
            for i, (vector, metadata) in enumerate(zip(vectors, metadata_list)):
                point_id = str(uuid.uuid4()).replace('-', '')  # Remove hyphens for Qdrant
                metadata['timestamp'] = datetime.now().isoformat()
                metadata['importance'] = metadata.get('importance', 0.5)  # Default importance
                points.append({
                    "id": point_id,
                    "vector": vector,
                    "payload": metadata
                })
            
            # Add points in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                url = f"{self.api_base}/collections/{self.collection_name}/points"
                payload = {
                    "points": batch
                }
                
                async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                    async with session.put(url, json=payload) as response:
                        response_text = await response.text()
                        if response.status != 200:
                            raise Exception(f"Failed to add vectors: {response_text}")
            
            logger.info(f"Added {len(vectors)} vectors to collection {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding vectors: {str(e)}")
            raise
    
    def _convert_to_json_serializable(self, obj: Any) -> Any:
        """Convert numpy arrays and other non-serializable types to JSON serializable types."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int8, np.int16, np.int32, np.int64,
                            np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(v) for v in obj]
        return obj
    
    def _calculate_decay_score(self, timestamp: str) -> float:
        """Calculate exponential decay score based on time difference."""
        try:
            memory_time = parser.parse(timestamp)
            now = datetime.now()
            time_diff = (now - memory_time).total_seconds() / 3600  # Hours
            return pow(self.decay_factor, time_diff)
        except Exception as e:
            logger.error(f"Error calculating decay score: {str(e)}")
            return 0.0
    
    def _pad_vector(self, vector: Union[List[float], np.ndarray]) -> List[float]:
        """Pad or truncate vector to match expected dimension."""
        vector = np.array(vector)
        current_dim = len(vector)
        
        if current_dim == self.vector_size:
            return vector.tolist()
        elif current_dim < self.vector_size:
            # Pad with zeros
            padding = np.zeros(self.vector_size - current_dim)
            return np.concatenate([vector, padding]).tolist()
        else:
            # Truncate
            return vector[:self.vector_size].tolist()
    
    async def search_vectors(self, query_vector: Union[np.ndarray, List[float]], 
                           k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search for similar vectors with decay-based scoring."""
        try:
            # Ensure query vector has correct dimension
            query_vector = self._pad_vector(query_vector)
            
            url = f"{self.api_base}/collections/{self.collection_name}/points/search"
            payload = {
                "vector": query_vector,
                "limit": k * 2,  # Get more results to account for decay filtering
                "with_payload": True,
                "with_vector": False
            }
            
            # Add filter if provided
            if filter_dict:
                payload["filter"] = {
                    "must": [
                        {
                            "key": k,
                            "match": {
                                "value": v
                            }
                        }
                        for k, v in filter_dict.items()
                    ]
                }
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        raise Exception(f"Failed to search vectors: {response_text}")
                    
                    result = json.loads(response_text)
                    
                    # Format results with decay scoring
                    results = []
                    for match in result.get("result", []):
                        # Calculate decay score
                        timestamp = match["payload"].get("timestamp", datetime.now().isoformat())
                        decay_score = self._calculate_decay_score(timestamp)
                        
                        # Get importance score
                        importance = float(match["payload"].get("importance", 0.5))
                        
                        # Combine scores
                        # You can adjust these weights based on your needs
                        similarity_weight = 0.4
                        decay_weight = 0.3
                        importance_weight = 0.3
                        
                        combined_score = (
                            similarity_weight * match["score"] +
                            decay_weight * decay_score +
                            importance_weight * importance
                        )
                        
                        results.append({
                            "id": match["id"],
                            "score": combined_score,
                            "similarity": match["score"],
                            "decay": decay_score,
                            "importance": importance,
                            "metadata": match["payload"]
                        })
                    
                    # Sort by combined score and limit to k results
                    results.sort(key=lambda x: x["score"], reverse=True)
                    return results[:k]
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    async def delete_vectors(self, filter_dict: Dict) -> None:
        """Delete vectors matching filter."""
        try:
            url = f"{self.api_base}/collections/{self.collection_name}/points/delete"
            payload = {
                "filter": {
                    "must": [
                        {
                            "key": k,
                            "match": {
                                "value": v
                            }
                        }
                        for k, v in filter_dict.items()
                    ]
                }
            }
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        raise Exception(f"Failed to delete vectors: {response_text}")
            
            logger.info(f"Deleted vectors matching filter: {filter_dict}")
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            raise
    
    async def clear_collection(self) -> None:
        """Clear all vectors from collection."""
        try:
            url = f"{self.api_base}/collections/{self.collection_name}/points/delete"
            payload = {
                "filter": {}  # Empty filter matches all points
            }
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        raise Exception(f"Failed to clear collection: {response_text}")
            
            logger.info(f"Cleared collection {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise
