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
from nia.agents.specialized.memory_agent import MemoryAgent
from nia.agents.specialized.planning_agent import PlanningAgent
from nia.agents.specialized.reasoning_agent import ReasoningAgent
from nia.agents.specialized.learning_agent import LearningAgent

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
from nia.agents.specialized.debugging_agent import DebuggingAgent
from nia.agents.specialized.schema_agent import SchemaAgent
from nia.agents.tiny_factory import TinyFactory
from nia.world.world import World
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
_memory_agent: Optional[MemoryAgent] = None
_planning_agent: Optional[PlanningAgent] = None
_reasoning_agent: Optional[ReasoningAgent] = None
_learning_agent: Optional[LearningAgent] = None

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
_debugging_agent: Optional[DebuggingAgent] = None
_schema_agent: Optional[SchemaAgent] = None

# Infrastructure
_tiny_factory: Optional[TinyFactory] = None
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
        logger.debug("Creating new memory system instance")
        _memory_system = TwoLayerMemorySystem()
        try:
            # Initialize with retries
            retry_count = 0
            max_retries = 5
            while retry_count < max_retries:
                try:
                    logger.debug(f"Attempting memory system initialization (attempt {retry_count + 1}/{max_retries})")
                    await _memory_system.initialize()
                    logger.debug("Memory system initialization complete")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.warning(f"Memory system initialization failed after {max_retries} retries: {str(e)}")
                        # Continue without full initialization
                        break
                    logger.warning(f"Memory system initialization attempt {retry_count} failed: {str(e)}")
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in memory system initialization: {str(e)}")
            # Don't raise - allow startup to continue
            logger.warning("Continuing without fully initialized memory system")
    return _memory_system

async def initialize_with_retry(instance: Any, name: str) -> bool:
    """Helper function to initialize components with retry logic."""
    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            logger.debug(f"Attempting {name} initialization (attempt {retry_count + 1}/{max_retries})")
            await instance.initialize()
            logger.debug(f"{name} initialization complete")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                logger.warning(f"{name} initialization failed after {max_retries} retries: {str(e)}")
                return False
            logger.warning(f"{name} initialization attempt {retry_count} failed: {str(e)}")
            await asyncio.sleep(1)
    return False

async def get_world() -> World:
    """Get or create world instance."""
    global _world
    if _world is None:
        _world = World()
        await initialize_with_retry(_world, "World")
    return _world

async def get_llm() -> LLMInterface:
    """Get or create LLM interface instance."""
    global _llm
    if _llm is None:
        _llm = LLMInterface()
        await initialize_with_retry(_llm, "LLM Interface")
    return _llm

async def get_parsing_agent() -> ParsingAgent:
    """Get or create parsing agent instance."""
    global _parsing_agent
    if _parsing_agent is None:
        _parsing_agent = ParsingAgent()
        await initialize_with_retry(_parsing_agent, "Parsing Agent")
    return _parsing_agent

async def get_coordination_agent() -> CoordinationAgent:
    """Get or create coordination agent instance."""
    global _coordination_agent
    if _coordination_agent is None:
        _coordination_agent = CoordinationAgent()
        await initialize_with_retry(_coordination_agent, "Coordination Agent")
    return _coordination_agent

async def get_tiny_factory() -> TinyFactory:
    """Get or create tiny factory instance."""
    global _tiny_factory
    if _tiny_factory is None:
        _tiny_factory = TinyFactory()
        await initialize_with_retry(_tiny_factory, "Tiny Factory")
    return _tiny_factory

async def get_analytics_agent() -> AnalyticsAgent:
    """Get or create analytics agent instance."""
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = AnalyticsAgent()
        await initialize_with_retry(_analytics_agent, "Analytics Agent")
    return _analytics_agent

async def get_orchestration_agent() -> OrchestrationAgent:
    """Get or create orchestration agent instance."""
    global _orchestration_agent
    if _orchestration_agent is None:
        _orchestration_agent = OrchestrationAgent()
        await initialize_with_retry(_orchestration_agent, "Orchestration Agent")
    return _orchestration_agent

async def get_graph_store() -> GraphStore:
    """Get or create graph store instance."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
        await initialize_with_retry(_graph_store, "Graph Store")
    return _graph_store

async def get_agent_store() -> AgentStore:
    """Get or create agent store instance."""
    global _agent_store
    if _agent_store is None:
        _agent_store = AgentStore()
        await initialize_with_retry(_agent_store, "Agent Store")
    return _agent_store

async def get_profile_store() -> ProfileStore:
    """Get or create profile store instance."""
    global _profile_store
    if _profile_store is None:
        _profile_store = ProfileStore()
        await initialize_with_retry(_profile_store, "Profile Store")
    return _profile_store

async def get_thread_manager() -> ThreadManager:
    """Get or create thread manager instance."""
    global _thread_manager
    if _thread_manager is None:
        logger.debug("Creating new thread manager instance")
        try:
            # Get memory system with retries
            retry_count = 0
            max_retries = 5
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
                    await asyncio.sleep(1)
            
            if memory_system:
                _thread_manager = ThreadManager(memory_system)
                logger.debug("Thread manager created successfully")
            else:
                logger.warning("Creating thread manager without memory system")
                _thread_manager = ThreadManager(TwoLayerMemorySystem())
        except Exception as e:
            logger.error(f"Error creating thread manager: {str(e)}")
            # Don't raise - allow startup to continue
            logger.warning("Continuing without thread manager")
    return _thread_manager

# Core cognitive agent getters
async def get_belief_agent() -> BeliefAgent:
    """Get or create belief agent instance."""
    global _belief_agent
    if _belief_agent is None:
        _belief_agent = BeliefAgent()
        await initialize_with_retry(_belief_agent, "Belief Agent")
    return _belief_agent

async def get_desire_agent() -> DesireAgent:
    """Get or create desire agent instance."""
    global _desire_agent
    if _desire_agent is None:
        _desire_agent = DesireAgent()
        await initialize_with_retry(_desire_agent, "Desire Agent")
    return _desire_agent

async def get_emotion_agent() -> EmotionAgent:
    """Get or create emotion agent instance."""
    global _emotion_agent
    if _emotion_agent is None:
        _emotion_agent = EmotionAgent()
        await initialize_with_retry(_emotion_agent, "Emotion Agent")
    return _emotion_agent

async def get_reflection_agent() -> ReflectionAgent:
    """Get or create reflection agent instance."""
    global _reflection_agent
    if _reflection_agent is None:
        _reflection_agent = ReflectionAgent()
        await initialize_with_retry(_reflection_agent, "Reflection Agent")
    return _reflection_agent

async def get_meta_agent() -> MetaAgent:
    """Get or create meta agent instance."""
    global _meta_agent
    if _meta_agent is None:
        _meta_agent = MetaAgent()
        await initialize_with_retry(_meta_agent, "Meta Agent")
    return _meta_agent

async def get_self_model_agent() -> SelfModelAgent:
    """Get or create self model agent instance."""
    global _self_model_agent
    if _self_model_agent is None:
        _self_model_agent = SelfModelAgent()
        await initialize_with_retry(_self_model_agent, "Self Model Agent")
    return _self_model_agent

async def get_analysis_agent() -> AnalysisAgent:
    """Get or create analysis agent instance."""
    global _analysis_agent
    if _analysis_agent is None:
        _analysis_agent = AnalysisAgent()
        await initialize_with_retry(_analysis_agent, "Analysis Agent")
    return _analysis_agent

async def get_research_agent() -> ResearchAgent:
    """Get or create research agent instance."""
    global _research_agent
    if _research_agent is None:
        _research_agent = ResearchAgent()
        await initialize_with_retry(_research_agent, "Research Agent")
    return _research_agent

async def get_integration_agent() -> IntegrationAgent:
    """Get or create integration agent instance."""
    global _integration_agent
    if _integration_agent is None:
        _integration_agent = IntegrationAgent()
        await initialize_with_retry(_integration_agent, "Integration Agent")
    return _integration_agent

async def get_memory_agent() -> MemoryAgent:
    """Get or create memory agent instance."""
    global _memory_agent
    if _memory_agent is None:
        _memory_agent = MemoryAgent()
        await initialize_with_retry(_memory_agent, "Memory Agent")
    return _memory_agent

async def get_planning_agent() -> PlanningAgent:
    """Get or create planning agent instance."""
    global _planning_agent
    if _planning_agent is None:
        _planning_agent = PlanningAgent()
        await initialize_with_retry(_planning_agent, "Planning Agent")
    return _planning_agent

async def get_reasoning_agent() -> ReasoningAgent:
    """Get or create reasoning agent instance."""
    global _reasoning_agent
    if _reasoning_agent is None:
        _reasoning_agent = ReasoningAgent()
        await initialize_with_retry(_reasoning_agent, "Reasoning Agent")
    return _reasoning_agent

async def get_learning_agent() -> LearningAgent:
    """Get or create learning agent instance."""
    global _learning_agent
    if _learning_agent is None:
        _learning_agent = LearningAgent()
        await initialize_with_retry(_learning_agent, "Learning Agent")
    return _learning_agent

# Support agent getters
async def get_dialogue_agent() -> DialogueAgent:
    """Get or create dialogue agent instance."""
    global _dialogue_agent
    if _dialogue_agent is None:
        _dialogue_agent = DialogueAgent()
        await initialize_with_retry(_dialogue_agent, "Dialogue Agent")
    return _dialogue_agent

async def get_context_agent() -> ContextAgent:
    """Get or create context agent instance."""
    global _context_agent
    if _context_agent is None:
        _context_agent = ContextAgent()
        await initialize_with_retry(_context_agent, "Context Agent")
    return _context_agent

async def get_validation_agent() -> ValidationAgent:
    """Get or create validation agent instance."""
    global _validation_agent
    if _validation_agent is None:
        _validation_agent = ValidationAgent()
        await initialize_with_retry(_validation_agent, "Validation Agent")
    return _validation_agent

async def get_synthesis_agent() -> SynthesisAgent:
    """Get or create synthesis agent instance."""
    global _synthesis_agent
    if _synthesis_agent is None:
        _synthesis_agent = SynthesisAgent()
        await initialize_with_retry(_synthesis_agent, "Synthesis Agent")
    return _synthesis_agent

async def get_alerting_agent() -> AlertingAgent:
    """Get or create alerting agent instance."""
    global _alerting_agent
    if _alerting_agent is None:
        _alerting_agent = AlertingAgent()
        await initialize_with_retry(_alerting_agent, "Alerting Agent")
    return _alerting_agent

async def get_monitoring_agent() -> MonitoringAgent:
    """Get or create monitoring agent instance."""
    global _monitoring_agent
    if _monitoring_agent is None:
        _monitoring_agent = MonitoringAgent()
        await initialize_with_retry(_monitoring_agent, "Monitoring Agent")
    return _monitoring_agent

async def get_debugging_agent() -> DebuggingAgent:
    """Get or create debugging agent instance."""
    global _debugging_agent
    if _debugging_agent is None:
        _debugging_agent = DebuggingAgent()
        await initialize_with_retry(_debugging_agent, "Debugging Agent")
    return _debugging_agent

async def get_schema_agent() -> SchemaAgent:
    """Get or create schema agent instance."""
    global _schema_agent
    if _schema_agent is None:
        _schema_agent = SchemaAgent()
        await initialize_with_retry(_schema_agent, "Schema Agent")
    return _schema_agent

async def get_llm_interface() -> LLMInterface:
    """Get LLM interface instance."""
    return await get_llm()
