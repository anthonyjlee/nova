"""FastAPI dependency injection providers."""

from typing import AsyncGenerator, Any

# Default models to use
CHAT_MODEL = "default"  # Will use first available model from LMStudio
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default embedding model from sentence-transformers
from fastapi import Depends

from nia.core.neo4j.neo4j_store import Neo4jMemoryStore
from nia.core.profiles.profile_manager import ProfileManager
from nia.core.profiles.profile_agent import ProfileAgent
from nia.agents.base import CoordinationAgent, AnalyticsAgent, ParsingAgent, OrchestrationAgent
from nia.agents.tinytroupe_agent import TinyFactory
from nia.memory.graph_store import GraphStore
from nia.memory.agent_store import AgentStore
from nia.memory.profile_store import ProfileStore
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld
from nia.core.interfaces.llm_interface import LLMInterface

async def get_llm() -> LLMInterface:
    """Get LLM interface instance."""
    return LLMInterface()

async def get_llm_interface() -> LLMInterface:
    """Get LLM interface instance."""
    return LLMInterface()

async def get_memory_system() -> AsyncGenerator[TwoLayerMemorySystem, None]:
    """Get memory system instance."""
    system = TwoLayerMemorySystem()
    try:
        await system.initialize()
        yield system
    finally:
        await system.cleanup()

async def get_world(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> AsyncGenerator[NIAWorld, None]:
    """Get world instance."""
    world = NIAWorld(memory_system=memory_system)
    try:
        yield world
    finally:
        await world.cleanup()

async def get_graph_store() -> GraphStore:
    """Get graph store instance."""
    return GraphStore()

async def get_coordination_agent() -> CoordinationAgent:
    """Get coordination agent instance."""
    return CoordinationAgent()

async def get_analytics_agent() -> AnalyticsAgent:
    """Get analytics agent instance."""
    return AnalyticsAgent()

async def get_parsing_agent() -> ParsingAgent:
    """Get parsing agent instance."""
    return ParsingAgent()

async def get_orchestration_agent() -> OrchestrationAgent:
    """Get orchestration agent instance."""
    return OrchestrationAgent()

async def get_profile_store() -> AsyncGenerator[ProfileStore, None]:
    """Get profile store instance."""
    store = ProfileStore()
    try:
        yield store
    finally:
        await store.close()

async def get_agent_store() -> AsyncGenerator[AgentStore, None]:
    """Get agent store instance."""
    store = AgentStore()
    try:
        yield store
    finally:
        await store.close()

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

async def get_tiny_factory(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    world: NIAWorld = Depends(get_world)
) -> TinyFactory:
    """Get TinyFactory instance."""
    return TinyFactory(memory_system=memory_system, world=world)
