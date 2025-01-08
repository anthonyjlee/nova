"""FastAPI dependency injection providers."""

from typing import AsyncGenerator
from fastapi import Depends

from nia.core.neo4j.neo4j_store import Neo4jMemoryStore
from nia.core.profiles.profile_manager import ProfileManager
from nia.core.profiles.profile_agent import ProfileAgent

async def get_neo4j_store() -> AsyncGenerator[Neo4jMemoryStore, None]:
    """Get Neo4j store instance."""
    store = Neo4jMemoryStore()
    try:
        yield store
    finally:
        await store.close()

async def get_profile_manager(
    store: Neo4jMemoryStore = Depends(get_neo4j_store)
) -> AsyncGenerator[ProfileManager, None]:
    """Get profile manager instance."""
    manager = ProfileManager(store=store)
    try:
        yield manager
    finally:
        pass  # Manager cleanup if needed

async def get_profile_agent(
    manager: ProfileManager = Depends(get_profile_manager)
) -> AsyncGenerator[ProfileAgent, None]:
    """Get profile agent instance."""
    agent = ProfileAgent(profile_manager=manager)
    try:
        yield agent
    finally:
        pass  # Agent cleanup if needed
