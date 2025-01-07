"""Profile store for managing user profiles and preferences."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

from ..core.neo4j.base_store import Neo4jBaseStore
from ..core.types.memory_types import JSONSerializable

logger = logging.getLogger(__name__)

class ProfileStore(Neo4jBaseStore):
    """Store for managing user profiles."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", **kwargs):
        """Initialize profile store."""
        super().__init__(uri=uri, **kwargs)
    
    async def store_profile(
        self,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store user profile data.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Dict containing profile ID and storage status
        """
        try:
            # Generate unique ID for profile
            profile_id = str(uuid.uuid4())
            
            # Prepare profile data
            profile = {
                "id": profile_id,
                "data": profile_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Store in Neo4j
            query = """
            CREATE (p:UserProfile {
                id: $id,
                data: $data,
                created_at: $created_at,
                updated_at: $updated_at
            })
            RETURN p
            """
            
            await self.run_query(query, parameters=profile)
            
            return {
                "profile_id": profile_id,
                "storage_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error storing profile: {str(e)}")
            return {
                "profile_id": None,
                "storage_status": "failed",
                "error": str(e)
            }
    
    async def get_profile(
        self,
        profile_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user profile by ID.
        
        Args:
            profile_id: ID of the profile to retrieve
            
        Returns:
            Profile data if found, None otherwise
        """
        try:
            query = """
            MATCH (p:UserProfile {id: $profile_id})
            RETURN p
            """
            
            result = await self.run_query(
                query,
                parameters={"profile_id": profile_id}
            )
            
            if result and result[0]:
                return dict(result[0]["p"])
            return None
            
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return None
    
    async def update_preferences(
        self,
        profile_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user preferences.
        
        Args:
            profile_id: ID of the profile to update
            preferences: Dictionary of preference updates
            
        Returns:
            Dict containing update status
        """
        try:
            # Get current profile data
            current_profile = await self.get_profile(profile_id)
            if not current_profile:
                return {
                    "update_status": "failed",
                    "error": "Profile not found"
                }
            
            # Update preferences in profile data
            profile_data = current_profile["data"]
            if "preferences" not in profile_data:
                profile_data["preferences"] = {}
            profile_data["preferences"].update(preferences)
            
            # Update in Neo4j
            query = """
            MATCH (p:UserProfile {id: $profile_id})
            SET p.data = $data,
                p.updated_at = $updated_at
            RETURN p
            """
            
            result = await self.run_query(
                query,
                parameters={
                    "profile_id": profile_id,
                    "data": profile_data,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            if result and result[0]:
                return {
                    "update_status": "success",
                    "profile": dict(result[0]["p"])
                }
            return {
                "update_status": "failed",
                "error": "Update failed"
            }
            
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return {
                "update_status": "failed",
                "error": str(e)
            }
    
    async def get_learning_style(
        self,
        profile_id: str
    ) -> Dict[str, Any]:
        """Get user's learning style preferences.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Dict containing learning style data
        """
        try:
            profile = await self.get_profile(profile_id)
            if not profile:
                return {
                    "status": "failed",
                    "error": "Profile not found"
                }
            
            profile_data = profile["data"]
            learning_style = profile_data.get("learning_style", {})
            
            return {
                "status": "success",
                "learning_style": learning_style
            }
            
        except Exception as e:
            logger.error(f"Error getting learning style: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def update_auto_approval(
        self,
        profile_id: str,
        settings: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Update auto-approval settings.
        
        Args:
            profile_id: ID of the profile
            settings: Dictionary of auto-approval settings
            
        Returns:
            Dict containing update status
        """
        try:
            # Get current profile data
            current_profile = await self.get_profile(profile_id)
            if not current_profile:
                return {
                    "update_status": "failed",
                    "error": "Profile not found"
                }
            
            # Update auto-approval settings
            profile_data = current_profile["data"]
            if "preferences" not in profile_data:
                profile_data["preferences"] = {}
            if "auto_approval" not in profile_data["preferences"]:
                profile_data["preferences"]["auto_approval"] = {}
            
            profile_data["preferences"]["auto_approval"].update(settings)
            
            # Update in Neo4j
            query = """
            MATCH (p:UserProfile {id: $profile_id})
            SET p.data = $data,
                p.updated_at = $updated_at
            RETURN p
            """
            
            result = await self.run_query(
                query,
                parameters={
                    "profile_id": profile_id,
                    "data": profile_data,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            if result and result[0]:
                return {
                    "update_status": "success",
                    "profile": dict(result[0]["p"])
                }
            return {
                "update_status": "failed",
                "error": "Update failed"
            }
            
        except Exception as e:
            logger.error(f"Error updating auto-approval settings: {str(e)}")
            return {
                "update_status": "failed",
                "error": str(e)
            }
    
    async def store_questionnaire(
        self,
        profile_id: str,
        questionnaire_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store questionnaire responses.
        
        Args:
            profile_id: ID of the profile
            questionnaire_data: Dictionary of questionnaire responses
            
        Returns:
            Dict containing storage status
        """
        try:
            # Get current profile data
            current_profile = await self.get_profile(profile_id)
            if not current_profile:
                return {
                    "storage_status": "failed",
                    "error": "Profile not found"
                }
            
            # Update profile with questionnaire data
            profile_data = current_profile["data"]
            profile_data.update(questionnaire_data)
            
            # Store questionnaire response
            questionnaire = {
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "responses": questionnaire_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update profile and store questionnaire
            query = """
            MATCH (p:UserProfile {id: $profile_id})
            CREATE (q:Questionnaire {
                id: $id,
                responses: $responses,
                timestamp: $timestamp
            })
            CREATE (p)-[:HAS_QUESTIONNAIRE]->(q)
            SET p.data = $profile_data,
                p.updated_at = $timestamp
            RETURN p, q
            """
            
            result = await self.run_query(
                query,
                parameters={
                    "profile_id": profile_id,
                    "id": questionnaire["id"],
                    "responses": questionnaire["responses"],
                    "timestamp": questionnaire["timestamp"],
                    "profile_data": profile_data
                }
            )
            
            if result and result[0]:
                return {
                    "storage_status": "success",
                    "questionnaire_id": questionnaire["id"],
                    "profile": dict(result[0]["p"])
                }
            return {
                "storage_status": "failed",
                "error": "Storage failed"
            }
            
        except Exception as e:
            logger.error(f"Error storing questionnaire: {str(e)}")
            return {
                "storage_status": "failed",
                "error": str(e)
            }
    
    async def get_questionnaire_history(
        self,
        profile_id: str
    ) -> List[Dict[str, Any]]:
        """Get questionnaire history for a profile.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            List of questionnaire responses
        """
        try:
            query = """
            MATCH (p:UserProfile {id: $profile_id})-[:HAS_QUESTIONNAIRE]->(q:Questionnaire)
            RETURN q
            ORDER BY q.timestamp DESC
            """
            
            result = await self.run_query(
                query,
                parameters={"profile_id": profile_id}
            )
            
            return [dict(row["q"]) for row in result]
            
        except Exception as e:
            logger.error(f"Error getting questionnaire history: {str(e)}")
            return []
