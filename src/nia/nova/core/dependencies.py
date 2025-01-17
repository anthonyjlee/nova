"""FastAPI dependencies for Nova's endpoints."""

from typing import Any, Optional
from pathlib import Path
import uuid
import asyncio
import logging
from fastapi import Depends

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.neo4j.concept_manager import ConceptManager
from nia.core.neo4j.graph_store import GraphStore
from nia.core.neo4j.agent_store import AgentStore
from nia.core.neo4j.profile_store import ProfileStore
from nia.core.interfaces.llm_interface import LLMInterface
# Core cognitive agents
from nia.agents.specialized.belief_agent import BeliefAgent
from nia.agents.specialized.desire_agent import DesireAgent
from nia.agents.specialized.emotion_agent import EmotionAgent
from nia.agents.specialized.reflection_agent import ReflectionAgent
from nia.agents.specialized.meta_agent import MetaAgent
from nia.agents.specialized.self_model_agent import SelfModelAgent
from nia.agents.specialized.analysis_agent import AnalysisAgent
from nia.agents.specialized.research_agent import ResearchAgent
from nia.agents.specialized.integration_agent import IntegrationAgent
from nia.agents.specialized.task_agent import TaskAgent
from nia.agents.specialized.logging_agent import LoggingAgent

# Support agents
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.agents.specialized.coordination_agent import CoordinationAgent
from nia.agents.specialized.analytics_agent import AnalyticsAgent
from nia.agents.specialized.orchestration_agent import OrchestrationAgent
from nia.agents.specialized.dialogue_agent import DialogueAgent
from nia.agents.specialized.context_agent import ContextAgent
from nia.agents.specialized.validation_agent import ValidationAgent
from nia.agents.specialized.synthesis_agent import SynthesisAgent
from nia.agents.specialized.alerting_agent import AlertingAgent
from nia.agents.specialized.monitoring_agent import MonitoringAgent
from nia.agents.specialized.schema_agent import SchemaAgent
from nia.agents.specialized.response_agent import ResponseAgent
from nia.agents.tiny_factory import TinyFactory
from nia.world.world import World, NIAWorld
from .thread_manager import ThreadManager

# Global instances
_memory_system: Optional[TwoLayerMemorySystem] = None
_world: Optional[World] = None
_llm: Optional[LLMInterface] = None

# Core cognitive agents
_belief_agent: Optional[BeliefAgent] = None
_desire_agent: Optional[DesireAgent] = None
_emotion_agent: Optional[EmotionAgent] = None
_reflection_agent: Optional[ReflectionAgent] = None
_meta_agent: Optional[MetaAgent] = None
_self_model_agent: Optional[SelfModelAgent] = None
_analysis_agent: Optional[AnalysisAgent] = None
_research_agent: Optional[ResearchAgent] = None
_integration_agent: Optional[IntegrationAgent] = None
_task_agent: Optional[TaskAgent] = None
_logging_agent: Optional[LoggingAgent] = None

# Support agents
_parsing_agent: Optional[ParsingAgent] = None
_coordination_agent: Optional[CoordinationAgent] = None
_analytics_agent: Optional[AnalyticsAgent] = None
_orchestration_agent: Optional[OrchestrationAgent] = None
_dialogue_agent: Optional[DialogueAgent] = None
_context_agent: Optional[ContextAgent] = None
_validation_agent: Optional[ValidationAgent] = None
_synthesis_agent: Optional[SynthesisAgent] = None
_alerting_agent: Optional[AlertingAgent] = None
_monitoring_agent: Optional[MonitoringAgent] = None
_schema_agent: Optional[SchemaAgent] = None
_response_agent: Optional[ResponseAgent] = None

# Infrastructure
_tiny_factory: Optional[TinyFactory] = None
_graph_store: Optional[GraphStore] = None
_agent_store: Optional[AgentStore] = None
_profile_store: Optional[ProfileStore] = None
_thread_manager: Optional[ThreadManager] = None
_concept_manager: Optional[ConceptManager] = None

async def get_concept_manager() -> ConceptManager:
    """Get or create concept manager instance."""
    global _concept_manager
    if _concept_manager is None:
        _concept_manager = ConceptManager()
        await initialize_with_retry(_concept_manager, "ConceptManager", store={})
    return _concept_manager

# Model configurations
CHAT_MODEL = "gpt-4"
EMBEDDING_MODEL = "text-embedding-ada-002"

async def get_memory_system(
    max_retries: int = 5,
    retry_delay: float = 1.0,
    name: str = "TwoLayerMemorySystem"
) -> TwoLayerMemorySystem:
    """Get or create memory system instance."""
    global _memory_system
    if _memory_system is None:
        logger.debug("Creating new memory system instance")
        _memory_system = TwoLayerMemorySystem()
        try:
            # Initialize with retries
            retry_count = 0
            while retry_count < max_retries:
                try:
                    logger.debug(f"Attempting memory system initialization (attempt {retry_count + 1}/{max_retries})")
                    await initialize_with_retry(_memory_system, name, store={}, max_retries=max_retries, retry_delay=retry_delay)
                    logger.debug("Memory system initialization complete")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.warning(f"Memory system initialization failed after {max_retries} retries: {str(e)}")
                        # Continue without full initialization
                        break
                    logger.warning(f"Memory system initialization attempt {retry_count} failed: {str(e)}")
                    await asyncio.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Error in memory system initialization: {str(e)}")
            # Don't raise - allow startup to continue
            logger.warning("Continuing without fully initialized memory system")
    return _memory_system

async def initialize_with_retry(
    instance: Any,
    name: Optional[str] = None,
    store: Optional[Any] = None,
    max_retries: int = 5,
    retry_delay: float = 1.0
) -> bool:
    """Helper function to initialize components with retry logic.
    
    Args:
        instance: The component instance to initialize
        name: Optional name for logging (defaults to class name)
        store: Optional store to attach to instance
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    # Set default name if not provided
    if name is None:
        name = instance.__class__.__name__
    
    # Handle store attribute
    if store is None and hasattr(instance, 'store'):
        store = {}
    if hasattr(instance, 'store'):
        instance.store = store
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.debug(f"Attempting {name} initialization (attempt {retry_count + 1}/{max_retries})")
            if hasattr(instance, 'initialize'):
                await instance.initialize()
            logger.debug(f"{name} initialization complete")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                logger.warning(f"{name} initialization failed after {max_retries} retries: {str(e)}")
                return False
            logger.warning(f"{name} initialization attempt {retry_count} failed: {str(e)}")
            await asyncio.sleep(retry_delay)
    return False

async def get_world() -> World:
    """Get or create world instance."""
    global _world
    if _world is None:
        _world = World()
        await initialize_with_retry(_world, "World", store={})
    return _world

async def get_llm() -> LLMInterface:
    """Get or create LLM interface instance."""
    global _llm
    if _llm is None:
        _llm = LLMInterface()
        await initialize_with_retry(_llm, "LLMInterface", store={})
    return _llm

async def get_parsing_agent() -> ParsingAgent:
    """Get or create parsing agent instance."""
    global _parsing_agent
    if _parsing_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _parsing_agent = ParsingAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_parsing_agent, "ParsingAgent", store={})
    return _parsing_agent

async def get_coordination_agent() -> CoordinationAgent:
    """Get or create coordination agent instance."""
    global _coordination_agent
    if _coordination_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _coordination_agent = CoordinationAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_coordination_agent, "CoordinationAgent", store={})
    return _coordination_agent

async def get_tiny_factory() -> TinyFactory:
    """Get or create tiny factory instance."""
    global _tiny_factory
    if _tiny_factory is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _tiny_factory = TinyFactory(
            memory_system=memory_system,
            world=world
        )
        await initialize_with_retry(_tiny_factory, "TinyFactory", store={})
    return _tiny_factory

async def get_analytics_agent() -> AnalyticsAgent:
    """Get or create analytics agent instance."""
    global _analytics_agent
    if _analytics_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _analytics_agent = AnalyticsAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_analytics_agent, "AnalyticsAgent", store={})
    return _analytics_agent

async def get_orchestration_agent() -> OrchestrationAgent:
    """Get or create orchestration agent instance."""
    global _orchestration_agent
    if _orchestration_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _orchestration_agent = OrchestrationAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_orchestration_agent, "OrchestrationAgent", store={})
    return _orchestration_agent

async def get_graph_store() -> GraphStore:
    """Get or create graph store instance."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
        await initialize_with_retry(_graph_store, "GraphStore", store={})
    return _graph_store

async def get_agent_store() -> AgentStore:
    """Get or create agent store instance."""
    global _agent_store
    if _agent_store is None:
        _agent_store = AgentStore()
        await initialize_with_retry(_agent_store, "AgentStore", store={})
    return _agent_store

async def get_profile_store() -> ProfileStore:
    """Get or create profile store instance."""
    global _profile_store
    if _profile_store is None:
        _profile_store = ProfileStore()
        await initialize_with_retry(_profile_store, "ProfileStore", store={})
    return _profile_store

async def get_thread_manager(max_retries: int = 5, retry_delay: float = 1.0) -> ThreadManager:
    """Get or create thread manager instance."""
    global _thread_manager
    if _thread_manager is None:
        logger.debug("Creating new thread manager instance")
        try:
            # Get memory system with retries
            retry_count = 0
            memory_system = None
            while retry_count < max_retries:
                try:
                    memory_system = await get_memory_system()
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.warning(f"Failed to get memory system after {max_retries} retries: {str(e)}")
                        break
                    await asyncio.sleep(retry_delay)
            
            memory_system = await get_memory_system()
            # Ensure memory system is initialized
            if not memory_system._initialized:
                await initialize_with_retry(memory_system, "TwoLayerMemorySystem", max_retries=max_retries, retry_delay=retry_delay)
                if not memory_system._initialized:
                    logger.error("Failed to initialize memory system")
                    raise RuntimeError("Failed to initialize memory system")
            
            # Create thread manager with initialized memory system
            _thread_manager = ThreadManager(memory_system)
            if not await initialize_with_retry(_thread_manager, "Thread Manager"):
                raise RuntimeError("Failed to initialize thread manager")
            logger.debug("Thread manager created successfully")
        except Exception as e:
            logger.error(f"Error creating thread manager: {str(e)}")
            # Create a new memory system and thread manager as fallback
            memory_system = TwoLayerMemorySystem()
            await initialize_with_retry(memory_system, "TwoLayerMemorySystem", max_retries=max_retries, retry_delay=retry_delay)
            _thread_manager = ThreadManager(memory_system)
            await initialize_with_retry(_thread_manager, "Thread Manager")
            logger.warning("Created fallback thread manager")
    return _thread_manager

# Core cognitive agent getters
async def get_belief_agent() -> BeliefAgent:
    """Get or create belief agent instance."""
    global _belief_agent
    if _belief_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _belief_agent = BeliefAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_belief_agent, "BeliefAgent", store={})
    return _belief_agent

async def get_desire_agent() -> DesireAgent:
    """Get or create desire agent instance."""
    global _desire_agent
    if _desire_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _desire_agent = DesireAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_desire_agent, "DesireAgent", store={})
    return _desire_agent

async def get_emotion_agent() -> EmotionAgent:
    """Get or create emotion agent instance."""
    global _emotion_agent
    if _emotion_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _emotion_agent = EmotionAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_emotion_agent, "EmotionAgent", store={})
    return _emotion_agent

async def get_reflection_agent() -> ReflectionAgent:
    """Get or create reflection agent instance."""
    global _reflection_agent
    if _reflection_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _reflection_agent = ReflectionAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_reflection_agent, "ReflectionAgent", store={})
    return _reflection_agent

async def get_meta_agent() -> MetaAgent:
    """Get or create meta agent instance."""
    global _meta_agent
    if _meta_agent is None:
        _meta_agent = MetaAgent()
    return _meta_agent

async def get_self_model_agent() -> SelfModelAgent:
    """Get or create self model agent instance."""
    global _self_model_agent
    if _self_model_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _self_model_agent = SelfModelAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_self_model_agent, "SelfModelAgent", store={})
    return _self_model_agent

async def get_analysis_agent() -> AnalysisAgent:
    """Get or create analysis agent instance."""
    global _analysis_agent
    if _analysis_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _analysis_agent = AnalysisAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_analysis_agent, "AnalysisAgent", store={})
    return _analysis_agent

async def get_research_agent() -> ResearchAgent:
    """Get or create research agent instance."""
    global _research_agent
    if _research_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _research_agent = ResearchAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_research_agent, "ResearchAgent", store={})
    return _research_agent

async def get_integration_agent() -> IntegrationAgent:
    """Get or create integration agent instance."""
    global _integration_agent
    if _integration_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _integration_agent = IntegrationAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_integration_agent, "IntegrationAgent", store={})
    return _integration_agent

async def get_task_agent() -> TaskAgent:
    """Get or create task agent instance."""
    global _task_agent
    if _task_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _task_agent = TaskAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_task_agent, "TaskAgent", store={})
    return _task_agent

async def get_logging_agent() -> LoggingAgent:
    """Get or create logging agent instance."""
    global _logging_agent
    if _logging_agent is None:
        _logging_agent = LoggingAgent()  # LoggingAgent doesn't inherit from TinyTroupeAgent
        await initialize_with_retry(_logging_agent, "LoggingAgent", store={})
    return _logging_agent

# Support agent getters
async def get_dialogue_agent() -> DialogueAgent:
    """Get or create dialogue agent instance."""
    global _dialogue_agent
    if _dialogue_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _dialogue_agent = DialogueAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_dialogue_agent, "DialogueAgent", store={})
    return _dialogue_agent

async def get_context_agent() -> ContextAgent:
    """Get or create context agent instance."""
    global _context_agent
    if _context_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _context_agent = ContextAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_context_agent, "ContextAgent", store={})
    return _context_agent

async def get_validation_agent() -> ValidationAgent:
    """Get or create validation agent instance."""
    global _validation_agent
    if _validation_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _validation_agent = ValidationAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_validation_agent, "ValidationAgent", store={})
    return _validation_agent

async def get_synthesis_agent() -> SynthesisAgent:
    """Get or create synthesis agent instance."""
    global _synthesis_agent
    if _synthesis_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _synthesis_agent = SynthesisAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_synthesis_agent, "SynthesisAgent", store={})
    return _synthesis_agent

async def get_alerting_agent() -> AlertingAgent:
    """Get or create alerting agent instance."""
    global _alerting_agent
    if _alerting_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _alerting_agent = AlertingAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_alerting_agent, "AlertingAgent", store={})
    return _alerting_agent

async def get_monitoring_agent() -> MonitoringAgent:
    """Get or create monitoring agent instance."""
    global _monitoring_agent
    if _monitoring_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _monitoring_agent = MonitoringAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_monitoring_agent, "MonitoringAgent", store={})
    return _monitoring_agent

async def get_schema_agent() -> SchemaAgent:
    """Get or create schema agent instance."""
    global _schema_agent
    if _schema_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _schema_agent = SchemaAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_schema_agent, "SchemaAgent", store={})
    return _schema_agent

async def get_llm_interface() -> LLMInterface:
    """Get LLM interface instance."""
    return await get_llm()

async def get_response_agent() -> ResponseAgent:
    """Get or create response agent instance."""
    global _response_agent
    if _response_agent is None:
        memory_system = await get_memory_system()
        world = await get_world()
        _response_agent = ResponseAgent(
            memory_system=memory_system,
            world=world,
            attributes=None
        )
        await initialize_with_retry(_response_agent, "ResponseAgent", store={})
    return _response_agent
