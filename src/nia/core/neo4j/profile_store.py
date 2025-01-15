"""Profile store implementation."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .base_store import Neo4jBaseStore

class ProfileStore(Neo4jBaseStore):
    """Store for user profile operations."""
    
    async def initialize(self):
        """Initialize profile store."""
        await self.connect()
        # Create indexes for better performance
        await self.run_query("""
            CREATE INDEX profile_id IF NOT EXISTS
            FOR (p:Profile)
            ON (p.id)
        """)
        await self.run_query("""
            CREATE INDEX preference_id IF NOT EXISTS
            FOR (p:Preference)
            ON (p.id)
        """)
        await self.run_query("""
            CREATE INDEX domain_id IF NOT EXISTS
            FOR (d:Domain)
            ON (d.id)
        """)
        
    async def create_profile(self, user_id: str, properties: Dict[str, Any]):
        """Create a user profile node with minimal data."""
        # Extract essential properties
        essential_props = {
            "id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add only necessary properties
        if "personality" in properties:
            essential_props["personality"] = {
                "openness": properties["personality"].get("openness", 0.5),
                "conscientiousness": properties["personality"].get("conscientiousness", 0.5)
            }
        if "learning_style" in properties:
            essential_props["learning_style"] = {
                "visual": properties["learning_style"].get("visual", 0.5),
                "auditory": properties["learning_style"].get("auditory", 0.5)
            }
        if "communication" in properties:
            essential_props["communication"] = {
                "direct": properties["communication"].get("direct", 0.5),
                "detailed": properties["communication"].get("detailed", 0.5)
            }
        
        query = """
        CREATE (p:Profile)
        SET p = $properties
        RETURN p
        """
        return await self.run_query(query, {"properties": essential_props})
        
    async def get_profile(self, user_id: str):
        """Get profile by user ID."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        OPTIONAL MATCH (p)-[:HAS_PREFERENCE]->(pref:Preference)
        OPTIONAL MATCH (p)-[:HAS_DOMAIN]->(d:Domain)
        RETURN p, collect(DISTINCT pref) as preferences, collect(DISTINCT d) as domains
        """
        return await self.run_query(query, {"user_id": user_id})
        
    async def update_profile(self, user_id: str, properties: Dict[str, Any]):
        """Update profile properties with minimal data."""
        # Extract essential properties
        essential_props = {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add only necessary properties
        if "personality" in properties:
            essential_props["personality"] = {
                "openness": properties["personality"].get("openness", 0.5),
                "conscientiousness": properties["personality"].get("conscientiousness", 0.5)
            }
        if "learning_style" in properties:
            essential_props["learning_style"] = {
                "visual": properties["learning_style"].get("visual", 0.5),
                "auditory": properties["learning_style"].get("auditory", 0.5)
            }
        if "communication" in properties:
            essential_props["communication"] = {
                "direct": properties["communication"].get("direct", 0.5),
                "detailed": properties["communication"].get("detailed", 0.5)
            }
        
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        SET p += $properties
        RETURN p
        """
        return await self.run_query(query, {
            "user_id": user_id,
            "properties": essential_props
        })
        
    async def delete_profile(self, user_id: str):
        """Delete profile by user ID."""
        query = """
        MATCH (p:Profile)
        WHERE p.id = $user_id
        OPTIONAL MATCH (p)-[:HAS_PREFERENCE]->(pref:Preference)
        OPTIONAL MATCH (p)-[:HAS_DOMAIN]->(d:Domain)
        DETACH DELETE p, pref, d
        """
        return await self.run_query(query, {"user_id": user_id})
        
    async def add_profile_preference(self, user_id: str, preference: Dict[str, Any]):
        """Add a preference to a profile with minimal data."""
        # Extract essential preference data
        essential_pref = {
            "id": preference.get("id", str(datetime.now(timezone.utc).timestamp())),
            "type": preference.get("type", "general"),
            "value": preference.get("value"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
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
            "preference": essential_pref
        })
        
    async def get_profile_preferences(self, user_id: str):
        """Get profile preferences."""
        query = """
        MATCH (p:Profile)-[:HAS_PREFERENCE]->(pref:Preference)
        WHERE p.id = $user_id
        RETURN pref
        ORDER BY pref.created_at DESC
        LIMIT 10
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
        """Add a domain to a profile with minimal data."""
        # Extract essential domain data
        essential_domain = {
            "id": domain.get("id", str(datetime.now(timezone.utc).timestamp())),
            "name": domain.get("name", "general"),
            "confidence": domain.get("confidence", 0.5),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
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
            "domain": essential_domain
        })
        
    async def get_profile_domains(self, user_id: str):
        """Get profile domains."""
        query = """
        MATCH (p:Profile)-[:HAS_DOMAIN]->(d:Domain)
        WHERE p.id = $user_id
        RETURN d
        ORDER BY d.confidence DESC
        LIMIT 5
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
