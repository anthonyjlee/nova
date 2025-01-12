"""FastAPI dependencies for Nova's endpoints."""

from typing import Any, Optional
import uuid

from fastapi import Depends
from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.neo4j.concept_manager import ConceptManager
from nia.core.neo4j.graph_store import GraphStore
from nia.core.neo4j.agent_store import AgentStore
from nia.core.neo4j.profile_store import ProfileStore
from nia.core.interfaces.llm_interface import LLMInterface
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.agents.specialized.coordination_agent import CoordinationAgent
from nia.agents.specialized.analytics_agent import AnalyticsAgent
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.tiny_factory import TinyFactory
from nia.world.world import World
from .thread_manager import ThreadManager

# Global instances
_memory_system: Optional[TwoLayerMemorySystem] = None
_world: Optional[World] = None
_llm: Optional[LLMInterface] = None
_parsing_agent: Optional[ParsingAgent] = None
_coordination_agent: Optional[CoordinationAgent] = None
_tiny_factory: Optional[TinyFactory] = None
_analytics_agent: Optional[AnalyticsAgent] = None
_orchestration_agent: Optional[OrchestrationAgent] = None
_graph_store: Optional[GraphStore] = None
_agent_store: Optional[AgentStore] = None
_profile_store: Optional[ProfileStore] = None
_thread_manager: Optional[ThreadManager] = None

# Model configurations
CHAT_MODEL = "gpt-4"
EMBEDDING_MODEL = "text-embedding-ada-002"

async def get_memory_system() -> TwoLayerMemorySystem:
    """Get or create memory system instance."""
    global _memory_system
    if _memory_system is None:
        _memory_system = TwoLayerMemorySystem()
        await _memory_system.initialize()
    return _memory_system

async def get_world() -> World:
    """Get or create world instance."""
    global _world
    if _world is None:
        _world = World()
        await _world.initialize()
    return _world

async def get_llm() -> LLMInterface:
    """Get or create LLM interface instance."""
    global _llm
    if _llm is None:
        _llm = LLMInterface()
        await _llm.initialize()
    return _llm

async def get_parsing_agent() -> ParsingAgent:
    """Get or create parsing agent instance."""
    global _parsing_agent
    if _parsing_agent is None:
        _parsing_agent = ParsingAgent()
        await _parsing_agent.initialize()
    return _parsing_agent

async def get_coordination_agent() -> CoordinationAgent:
    """Get or create coordination agent instance."""
    global _coordination_agent
    if _coordination_agent is None:
        _coordination_agent = CoordinationAgent()
        await _coordination_agent.initialize()
    return _coordination_agent

async def get_tiny_factory() -> TinyFactory:
    """Get or create tiny factory instance."""
    global _tiny_factory
    if _tiny_factory is None:
        _tiny_factory = TinyFactory()
        await _tiny_factory.initialize()
    return _tiny_factory

async def get_analytics_agent() -> AnalyticsAgent:
    """Get or create analytics agent instance."""
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = AnalyticsAgent()
        await _analytics_agent.initialize()
    return _analytics_agent

async def get_orchestration_agent() -> OrchestrationAgent:
    """Get or create orchestration agent instance."""
    global _orchestration_agent
    if _orchestration_agent is None:
        _orchestration_agent = OrchestrationAgent()
        await _orchestration_agent.initialize()
    return _orchestration_agent

async def get_graph_store() -> GraphStore:
    """Get or create graph store instance."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
        await _graph_store.initialize()
    return _graph_store

async def get_agent_store() -> AgentStore:
    """Get or create agent store instance."""
    global _agent_store
    if _agent_store is None:
        _agent_store = AgentStore()
        await _agent_store.initialize()
    return _agent_store

async def get_profile_store() -> ProfileStore:
    """Get or create profile store instance."""
    global _profile_store
    if _profile_store is None:
        _profile_store = ProfileStore()
        await _profile_store.initialize()
    return _profile_store

async def get_thread_manager() -> ThreadManager:
    """Get or create thread manager instance."""
    global _thread_manager
    if _thread_manager is None:
        memory_system = await get_memory_system()
        _thread_manager = ThreadManager(memory_system)
    return _thread_manager

async def get_llm_interface() -> LLMInterface:
    """Get LLM interface instance."""
    return await get_llm()
