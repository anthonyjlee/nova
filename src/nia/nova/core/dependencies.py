"""FastAPI dependency injection providers."""

from typing import AsyncGenerator, Any
from fastapi import Depends, APIRouter

# Default models to use
CHAT_MODEL = "default"  # Will use first available model from LMStudio
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default embedding model from sentence-transformers

# Create router for lifecycle events
ws_router = APIRouter()

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

_memory_system = None

async def get_memory_system() -> TwoLayerMemorySystem:
    """Get memory system instance."""
    global _memory_system
    if _memory_system is None:
        from nia.core.vector.vector_store import VectorStore
        from nia.core.vector.embeddings import EmbeddingService
        from nia.memory.two_layer import EpisodicLayer, SemanticLayer
        
        try:
            # Initialize vector store with embedding service
            embedding_service = EmbeddingService()
            vector_store = VectorStore(embedding_service)
            
            # Create memory system with vector store
            memory_system = TwoLayerMemorySystem(vector_store=vector_store)
            
            # Initialize layers
            episodic = EpisodicLayer(vector_store)
            episodic.store = vector_store  # Ensure store is set
            semantic = SemanticLayer()
            
            # Set layers
            memory_system.episodic = episodic
            memory_system.semantic = semantic
            memory_system.vector_store = vector_store  # Ensure vector_store is set
            
            # Initialize the system
            await memory_system.initialize()
            
            # Verify initialization
            if not hasattr(memory_system, 'episodic') or not hasattr(memory_system.episodic, 'store'):
                # Try to re-initialize layers
                memory_system.episodic = EpisodicLayer(vector_store)
                memory_system.episodic.store = vector_store  # Ensure store is set
                memory_system.semantic = SemanticLayer()
                memory_system.vector_store = vector_store  # Ensure vector_store is set
                await memory_system.initialize()
                
                # Verify again
                if not hasattr(memory_system, 'episodic') or not hasattr(memory_system.episodic, 'store'):
                    raise ValueError("Memory system not properly initialized")
            
            # Set initialized flag
            memory_system._initialized = True
            
            # Store the initialized memory system
            _memory_system = memory_system
                
        except Exception as e:
            print(f"Error initializing memory system: {str(e)}")
            _memory_system = None
            raise
    else:
        # Verify existing memory system
        if not hasattr(_memory_system, 'episodic') or not hasattr(_memory_system.episodic, 'store'):
            print("Warning: Existing memory system missing required attributes")
            _memory_system = None
            return await get_memory_system()
    return _memory_system

@ws_router.on_event("shutdown")
async def cleanup_memory_system():
    """Clean up memory system on shutdown."""
    global _memory_system
    if _memory_system is not None:
        await _memory_system.cleanup()
        _memory_system = None

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
