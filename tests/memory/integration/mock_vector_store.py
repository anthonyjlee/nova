"""Mock vector store for testing."""

import logging
import json
from typing import Dict, List, Optional, Any
import uuid

from nia.core.types.memory_types import ValidationSchema

logger = logging.getLogger(__name__)

class MockVectorStore:
    """Mock vector store for testing."""
    
    def __init__(self):
        self.vectors = {}
        self.metadata = {}
        
    async def store_vector(
        self,
        content: Any,
        metadata: Optional[Dict] = None,
        layer: Optional[str] = None
    ) -> str:
        """Store content with metadata."""
        vector_id = str(uuid.uuid4())
        
        # Handle validation in content
        if isinstance(content, dict) and "validation" in content:
            if isinstance(content["validation"], ValidationSchema):
                content["validation"] = content["validation"].dict()
            elif isinstance(content["validation"], str):
                content["validation"] = json.loads(content["validation"])
                
        # Handle validation in metadata
        if metadata and "validation" in metadata:
            if isinstance(metadata["validation"], ValidationSchema):
                metadata["validation"] = metadata["validation"].dict()
            elif isinstance(metadata["validation"], str):
                metadata["validation"] = json.loads(metadata["validation"])
        
        # Log validation data
        if isinstance(content, dict) and "validation" in content:
            logger.info(f"Vector content validation data: {json.dumps(content['validation'], indent=2)}")
        if metadata and "validation" in metadata:
            logger.info(f"Vector metadata validation data: {json.dumps(metadata['validation'], indent=2)}")
            
        self.vectors[vector_id] = content
        if metadata:
            self.metadata[vector_id] = metadata
        return vector_id
            
    async def search_vectors(
        self,
        content: Optional[Dict] = None,
        filter: Optional[Dict] = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        layer: Optional[str] = None
    ) -> List[Dict]:
        """Search for similar vectors."""
        # Return all vectors for testing
        results = []
        for vector_id in self.vectors:
            vector_content = self.vectors[vector_id]
            
            # Handle validation in vector content
            if isinstance(vector_content, dict) and "validation" in vector_content:
                if isinstance(vector_content["validation"], ValidationSchema):
                    vector_content["validation"] = vector_content["validation"].dict()
                elif isinstance(vector_content["validation"], str):
                    vector_content["validation"] = json.loads(vector_content["validation"])
            
            result = {
                "id": vector_id,
                "content": vector_content,
                "score": 0.9,  # Mock similarity score
                "is_consolidation": True  # Mark as consolidated
            }
            
            if vector_id in self.metadata:
                metadata = self.metadata[vector_id]
                # Handle validation in metadata
                if "validation" in metadata:
                    if isinstance(metadata["validation"], ValidationSchema):
                        metadata["validation"] = metadata["validation"].dict()
                    elif isinstance(metadata["validation"], str):
                        metadata["validation"] = json.loads(metadata["validation"])
                result.update(metadata)
            
            # Log validation data in results
            if isinstance(result["content"], dict) and "validation" in result["content"]:
                logger.info(f"Search result validation data: {json.dumps(result['content']['validation'], indent=2)}")
            
            results.append(result)
        return results[:limit]
        
    async def get_vector(self, vector_id: str) -> Optional[Dict]:
        """Get a vector by ID."""
        if vector_id in self.vectors:
            vector_content = self.vectors[vector_id]
            
            # Handle validation in vector content
            if isinstance(vector_content, dict) and "validation" in vector_content:
                if isinstance(vector_content["validation"], ValidationSchema):
                    vector_content["validation"] = vector_content["validation"].dict()
                elif isinstance(vector_content["validation"], str):
                    vector_content["validation"] = json.loads(vector_content["validation"])
            
            result = {
                "id": vector_id,
                "content": vector_content,
                "is_consolidation": True  # Mark as consolidated
            }
            
            if vector_id in self.metadata:
                metadata = self.metadata[vector_id]
                # Handle validation in metadata
                if "validation" in metadata:
                    if isinstance(metadata["validation"], ValidationSchema):
                        metadata["validation"] = metadata["validation"].dict()
                    elif isinstance(metadata["validation"], str):
                        metadata["validation"] = json.loads(metadata["validation"])
                result.update(metadata)
            
            # Log validation data
            if isinstance(result["content"], dict) and "validation" in result["content"]:
                logger.info(f"Get vector validation data: {json.dumps(result['content']['validation'], indent=2)}")
            return result
        return None
        
    async def delete_vector(self, vector_id: str):
        """Delete a vector."""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
        if vector_id in self.metadata:
            del self.metadata[vector_id]

    async def update_metadata(self, vector_id: str, metadata: Dict):
        """Update metadata for a vector."""
        if vector_id in self.vectors:
            # Handle validation in metadata
            if "validation" in metadata:
                if isinstance(metadata["validation"], ValidationSchema):
                    metadata["validation"] = metadata["validation"].dict()
                elif isinstance(metadata["validation"], str):
                    metadata["validation"] = json.loads(metadata["validation"])
            
            if vector_id not in self.metadata:
                self.metadata[vector_id] = {}
            self.metadata[vector_id].update(metadata)
            # Log validation data
            if "validation" in metadata:
                logger.info(f"Updated metadata validation data: {json.dumps(metadata['validation'], indent=2)}")
