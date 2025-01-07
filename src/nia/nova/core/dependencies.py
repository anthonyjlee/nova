"""FastAPI dependency functions."""

from fastapi import Depends
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.world.environment import NIAWorld
from nia.nova.core.llm import LMStudioLLM
from nia.agents.specialized.coordination_agent import CoordinationAgent
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.agents.tinytroupe_agent import TinyFactory
from nia.nova.core.analytics import AnalyticsAgent
import uuid
from typing import AsyncGenerator, Any

# LM Studio configuration
CHAT_MODEL = "llama-3.2-3b-instruct"
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

async def get_memory_system() -> AsyncGenerator[TwoLayerMemorySystem, None]:
    """Get memory system instance."""
    memory_system = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687"
    )
    try:
        # Initialize Neo4j connection
        await memory_system.semantic.connect()
        # Initialize vector store if needed
        if hasattr(memory_system.episodic.store, 'connect'):
            await memory_system.episodic.store.connect()
        yield memory_system
    finally:
        # Cleanup connections
        if hasattr(memory_system.semantic, 'close'):
            await memory_system.semantic.close()
        if hasattr(memory_system.episodic.store, 'close'):
            await memory_system.episodic.store.close()

async def get_world() -> NIAWorld:
    """Get world instance."""
    return NIAWorld()

async def get_llm() -> LMStudioLLM:
    """Get LLM instance."""
    return LMStudioLLM(
        chat_model=CHAT_MODEL,
        embedding_model=EMBEDDING_MODEL
    )

async def get_graph_store() -> AsyncGenerator[Any, None]:
    """Get graph store instance."""
    from nia.memory.graph_store import GraphStore
    store = GraphStore(
        neo4j_uri="bolt://localhost:7687"
    )
    try:
        await store.connect()
        yield store
    finally:
        await store.close()

async def get_agent_store() -> AsyncGenerator[Any, None]:
    """Get agent store instance."""
    from nia.memory.agent_store import AgentStore
    store = AgentStore(
        neo4j_uri="bolt://localhost:7687"
    )
    try:
        await store.connect()
        yield store
    finally:
        await store.close()

async def get_profile_store() -> AsyncGenerator[Any, None]:
    """Get profile store instance."""
    from nia.memory.profile_store import ProfileStore
    store = ProfileStore(
        neo4j_uri="bolt://localhost:7687"
    )
    try:
        await store.connect()
        yield store
    finally:
        await store.close()

async def get_coordination_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    world: NIAWorld = Depends(get_world),
    llm: LMStudioLLM = Depends(get_llm)
) -> CoordinationAgent:
    """Get coordination agent instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None

    agent = CoordinationAgent(
        name="nova_coordinator",
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    agent.llm = llm
    return agent

async def get_llm_interface() -> LMStudioLLM:
    """Get LLM interface instance."""
    return LMStudioLLM(
        chat_model=CHAT_MODEL,
        embedding_model=EMBEDDING_MODEL
    )

async def get_tiny_factory(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system)
) -> TinyFactory:
    """Get TinyFactory instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None

    return TinyFactory(memory_system=memory_system)

async def get_analytics_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    llm: LMStudioLLM = Depends(get_llm)
) -> AnalyticsAgent:
    """Get analytics agent instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None
    
    return AnalyticsAgent(
        domain="professional",
        llm=llm,
        store=memory_system.semantic.store if memory_system else None,
        vector_store=memory_system.episodic.store if memory_system else None
    )

async def get_orchestration_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    llm: LMStudioLLM = Depends(get_llm)
) -> OrchestrationAgent:
    """Get orchestration agent instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None
    
    # Generate unique name for each agent instance
    agent_name = f"nova_orchestrator_{uuid.uuid4().hex[:8]}"
    agent = OrchestrationAgent(
        name=agent_name,
        memory_system=memory_system,
        domain="professional"
    )
    agent.llm = llm
    return agent

async def get_parsing_agent(
    memory_system: TwoLayerMemorySystem = Depends(get_memory_system),
    world: NIAWorld = Depends(get_world),
    llm: LMStudioLLM = Depends(get_llm)
) -> ParsingAgent:
    """Get parsing agent instance."""
    # Get memory system from async generator
    if hasattr(memory_system, '__aiter__'):
        try:
            memory_system = await anext(memory_system.__aiter__())
        except StopAsyncIteration:
            memory_system = None

    # Generate unique name for each agent instance
    agent_name = f"nova_parser_{uuid.uuid4().hex[:8]}"
    agent = ParsingAgent(
        name=agent_name,
        memory_system=memory_system,
        world=world,
        domain="professional"
    )
    agent.llm = llm
    return agent
