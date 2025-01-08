"""FastAPI dependency injection providers."""

from typing import AsyncGenerator, Any
from fastapi import Depends

from nia.core.neo4j.neo4j_store import Neo4jMemoryStore
from nia.core.profiles.profile_manager import ProfileManager
from nia.core.profiles.profile_agent import ProfileAgent
from nia.agents.base import CoordinationAgent, AnalyticsAgent
from nia.memory.graph_store import GraphStore

async def get_graph_store() -> GraphStore:
    """Get graph store instance."""
    return GraphStore()

async def get_coordination_agent() -> CoordinationAgent:
    """Get coordination agent instance."""
    return CoordinationAgent()

async def get_analytics_agent() -> AnalyticsAgent:
    """Get analytics agent instance."""
    return AnalyticsAgent()

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
