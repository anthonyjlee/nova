"""Profile store implementation."""

from typing import Dict, Any, List, Optional
from .base_store import Neo4jBaseStore

class ProfileStore(Neo4jBaseStore):
    """Store for user profile operations."""
    
    async def initialize(self):
        """Initialize profile store."""
        await self.connect()
        
    async def create_profile(self, user_id: str, properties: Dict[str, Any]):
        """Create a user profile node."""
        query = """
        CREATE (p:Profile {id: $user_id})
        SET p += $properties
        RETURN p
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "properties": properties
        })
        
    async def get_profile(self, user_id: str):
        """Get profile by user ID."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        RETURN p
        """
        return await self.run_query(query, {"user_id": user_id})
        
    async def update_profile(self, user_id: str, properties: Dict[str, Any]):
        """Update profile properties."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        SET p += $properties
        RETURN p
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "properties": properties
        })
        
    async def delete_profile(self, user_id: str):
        """Delete profile by user ID."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        DETACH DELETE p
        """
        return await self.run_query(query, {"user_id": user_id})
        
    async def add_profile_preference(self, user_id: str, preference: Dict[str, Any]):
        """Add a preference to a profile."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        CREATE (pref:Preference)
        SET pref = $preference
        CREATE (p)-[:HAS_PREFERENCE]->(pref)
        RETURN pref
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "preference": preference
        })
        
    async def get_profile_preferences(self, user_id: str):
        """Get profile preferences."""
        query = """
        MATCH (p:Profile)-[:HAS_PREFERENCE]->(pref:Preference)
        WHERE p.id = $user_id
        RETURN pref
        """
        return await self.run_query(query, {"user_id": user_id})
        
    async def remove_profile_preference(self, user_id: str, preference_id: str):
        """Remove a preference from a profile."""
        query = """
        MATCH (p:Profile)-[r:HAS_PREFERENCE]->(pref:Preference)
        WHERE p.id = $user_id AND pref.id = $preference_id
        DELETE r, pref
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "preference_id": preference_id
        })
        
    async def add_profile_domain(self, user_id: str, domain: Dict[str, Any]):
        """Add a domain to a profile."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        CREATE (d:Domain)
        SET d = $domain
        CREATE (p)-[:HAS_DOMAIN]->(d)
        RETURN d
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "domain": domain
        })
        
    async def get_profile_domains(self, user_id: str):
        """Get profile domains."""
        query = """
        MATCH (p:Profile)-[:HAS_DOMAIN]->(d:Domain)
        WHERE p.id = $user_id
        RETURN d
        """
        return await self.run_query(query, {"user_id": user_id})
        
    async def remove_profile_domain(self, user_id: str, domain_id: str):
        """Remove a domain from a profile."""
        query = """
        MATCH (p:Profile)-[r:HAS_DOMAIN]->(d:Domain)
        WHERE p.id = $user_id AND d.id = $domain_id
        DELETE r, d
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "domain_id": domain_id
        })
