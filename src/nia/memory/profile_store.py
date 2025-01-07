"""Profile store implementation."""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from nia.core.neo4j.base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)

class ProfileStore(Neo4jBaseStore):
    """Store for managing user profiles."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize store."""
        super().__init__(uri=uri, **kwargs)
        
    async def store_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """Store user profile data."""
        try:
            # Create profile node with data
            query = """
            MERGE (p:Profile {id: $profile_id})
            SET p += $profile_data
            """
            
            await self.driver.execute_query(
                query,
                parameters={
                    "profile_id": profile_id,
                    "profile_data": profile_data
                }
            )
        except Exception as e:
            logger.error(f"Error storing profile: {str(e)}")
            raise
    
    async def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile data."""
        try:
            # Get most recently updated profile
            query = """
            MATCH (p:Profile)
            RETURN p
            ORDER BY p.updated_at DESC
            LIMIT 1
            """
            
            result = await self.driver.execute_query(query)
            if result and result[0]:
                profile_data = dict(result[0][0])
                # Remove Neo4j internal ID
                if "id" in profile_data:
                    del profile_data["id"]
                return profile_data
            return None
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            raise
    
    async def update_preferences(self, preferences: Dict[str, Any], updated_at: str) -> None:
        """Update user preferences."""
        try:
            # Update preferences on most recent profile
            query = """
            MATCH (p:Profile)
            WITH p
            ORDER BY p.updated_at DESC
            LIMIT 1
            SET p.preferences = $preferences,
                p.updated_at = $updated_at
            """
            
            await self.driver.execute_query(
                query,
                parameters={
                    "preferences": preferences,
                    "updated_at": updated_at
                }
            )
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            raise
    
    async def get_learning_style(self) -> Optional[Dict[str, float]]:
        """Get user learning style."""
        try:
            # Get learning style from most recent profile
            query = """
            MATCH (p:Profile)
            WHERE p.learning_style IS NOT NULL
            RETURN p.learning_style
            ORDER BY p.updated_at DESC
            LIMIT 1
            """
            
            result = await self.driver.execute_query(query)
            if result and result[0]:
                return dict(result[0][0])
            return None
        except Exception as e:
            logger.error(f"Error getting learning style: {str(e)}")
            raise
    
    async def get_auto_approval(self) -> Optional[Dict[str, bool]]:
        """Get auto-approval settings."""
        try:
            # Get auto-approval settings from most recent profile
            query = """
            MATCH (p:Profile)
            WHERE p.preferences IS NOT NULL
            AND p.preferences.auto_approval IS NOT NULL
            RETURN p.preferences.auto_approval
            ORDER BY p.updated_at DESC
            LIMIT 1
            """
            
            result = await self.driver.execute_query(query)
            if result and result[0]:
                return dict(result[0][0])
            return None
        except Exception as e:
            logger.error(f"Error getting auto-approval settings: {str(e)}")
            raise
