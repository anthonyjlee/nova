"""Tests for dialogue system."""

import pytest
from datetime import datetime
from typing import Dict, Any

from nia.memory.types.memory_types import DialogueContext, DialogueMessage
from nia.agents.specialized.belief_agent import BeliefAgent
from nia.agents.specialized.emotion_agent import EmotionAgent
from nia.agents.specialized.reflection_agent import ReflectionAgent
from nia.nova.core.meta import MetaAgent
from nia.agents.specialized.task_agent import TaskAgent
from nia.agents.specialized.dialogue_agent import DialogueAgent
from nia.nova.core.context import ContextAgent
from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j.neo4j_store import Neo4jMemoryStore
from nia.memory.vector.vector_store import VectorStore
from nia.memory.vector.embeddings import EmbeddingService

# Test data
TEST_INPUT = """
The nature of machine consciousness and emotional intelligence
raises important questions about the future of AI systems.
"""

@pytest.fixture
def lmstudio_available():
    """Check if LMStudio is available."""
    import aiohttp
    import asyncio
    
    async def check_lmstudio():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:1234/v1/models") as response:
                    return response.status == 200
        except:
            return False
    
    return asyncio.run(check_lmstudio())

def setup_test_stores():
    """Set up test stores with mock embedding service."""
    embedding_service = EmbeddingService()
    vector_store = VectorStore(embedding_service)
    store = Neo4jMemoryStore()
    return store, vector_store

def setup_test_llm(use_mock: bool = False):
    """Set up test LLM with parser.
    
    Args:
        use_mock: Whether to use mock responses (for testing)
        Default is False to use real LMStudio for integration testing
    """
    store, vector_store = setup_test_stores()
    llm = LLMInterface(use_mock=use_mock)
    llm.initialize_parser(store, vector_store)
    return llm, store, vector_store

def setup_test_agents():
    """Set up test agents."""
    llm, store, vector_store = setup_test_llm()
    
    agents = {
        'belief': BeliefAgent(llm, store, vector_store),
        'emotion': EmotionAgent(llm, store, vector_store),
        'reflection': ReflectionAgent(llm, store, vector_store),
        'task': TaskAgent(llm, store, vector_store),
        'dialogue': DialogueAgent(llm, store, vector_store),
        'context': ContextAgent(llm, store, vector_store),
        'nova': MetaAgent(llm, store, vector_store)
    }
    
    return agents

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_dialogue_message_types(use_mock):
    """Test dialogue message type handling."""
    # Create dialogue context
    dialogue = DialogueContext(
        topic="Test Topic",
        status="active"
    )
    
    # Create message
    message = DialogueMessage(
        content="Test message",
        message_type="test_type",
        agent_type="test_agent"
    )
    
    # Add message
    dialogue.add_message(message)
    
    # Verify message added
    assert len(dialogue.messages) == 1
    assert dialogue.messages[0].content == "Test message"
    assert dialogue.messages[0].message_type == "test_type"
    assert dialogue.messages[0].agent_type == "test_agent"
    assert "test_agent" in dialogue.participants

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_dialogue_creation(use_mock):
    """Test dialogue context creation."""
    dialogue = DialogueContext(
        topic="Test Topic",
        status="active"
    )
    
    assert dialogue.topic == "Test Topic"
    assert dialogue.status == "active"
    assert isinstance(dialogue.messages, list)
    assert isinstance(dialogue.participants, list)
    assert isinstance(dialogue.created_at, datetime)

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_agent_message_sending(use_mock):
    """Test agent message sending."""
    # Set up components
    agents = setup_test_agents()
    belief_agent = agents['belief']
    
    # Create dialogue context
    dialogue = DialogueContext(
        topic="Test Topic",
        status="active"
    )
    belief_agent.current_dialogue = dialogue
    
    # Send message
    message = await belief_agent.send_message(
        content="Test message",
        message_type="test_type",
        references=["ref1"]
    )
    
    # Verify message
    assert message.content == "Test message"
    assert message.message_type == "test_type"
    assert message.agent_type == "belief"
    assert message.references == ["ref1"]
    assert message in dialogue.messages

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_concept_validation(use_mock):
    """Test concept validation through dialogue."""
    # Set up components
    agents = setup_test_agents()
    nova = agents['nova']
    belief_agent = agents['belief']
    emotion_agent = agents['emotion']
    task_agent = agents['task']
    context_agent = agents['context']
    
    # Create and set dialogue context
    dialogue = DialogueContext(
        topic="Concept Validation",
        status="active"
    )
    
    # Set dialogue context for all agents
    for agent in agents.values():
        agent.current_dialogue = dialogue
    
    # Add validation messages
    await belief_agent.provide_insight(
        "This aligns with current understanding of AI cognition",
        references=["AI Emotional Processing"]
    )
    
    await emotion_agent.provide_insight(
        "Emotional processing shows similar patterns",
        references=["AI Cognition"]
    )
    
    await task_agent.provide_insight(
        "This suggests specific implementation steps",
        references=["AI Implementation"]
    )
    
    await context_agent.provide_insight(
        "Environmental factors support this approach",
        references=["System Context"]
    )
    
    # Verify dialogue flow
    assert len(dialogue.messages) == 4
    assert dialogue.messages[0].agent_type == "belief"
    assert dialogue.messages[1].agent_type == "emotion"
    assert dialogue.messages[2].agent_type == "task"
    assert dialogue.messages[3].agent_type == "context"
    assert len(dialogue.participants) == 4

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_dialogue_synthesis(use_mock):
    """Test synthesis of collaborative dialogue."""
    # Set up components
    agents = setup_test_agents()
    nova = agents['nova']
    belief_agent = agents['belief']
    emotion_agent = agents['emotion']
    reflection_agent = agents['reflection']
    dialogue_agent = agents['dialogue']
    
    # Create and set dialogue context
    dialogue = DialogueContext(
        topic="AI Understanding",
        status="active"
    )
    
    # Set dialogue context for all agents
    for agent in agents.values():
        agent.current_dialogue = dialogue
    
    # Add messages from different perspectives
    await belief_agent.provide_insight(
        "AI understanding operates differently from human cognition"
    )
    
    await emotion_agent.provide_insight(
        "Emotional processing may be fundamentally different"
    )
    
    await reflection_agent.provide_insight(
        "This suggests a new paradigm for understanding AI cognition"
    )
    
    await dialogue_agent.provide_insight(
        "The conversation flow indicates key patterns"
    )
    
    # Verify dialogue state
    assert len(dialogue.messages) == 4
    assert len(dialogue.participants) == 4
    assert all(m.message_type == "insight" for m in dialogue.messages)

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_task_planning_dialogue(use_mock):
    """Test task planning in dialogue."""
    # Set up components
    agents = setup_test_agents()
    task_agent = agents['task']
    context_agent = agents['context']
    dialogue_agent = agents['dialogue']
    
    # Create dialogue context
    dialogue = DialogueContext(
        topic="Implementation Planning",
        status="active"
    )
    
    # Set dialogue context for agents
    for agent in [task_agent, context_agent, dialogue_agent]:
        agent.current_dialogue = dialogue
    
    # Add planning messages
    await task_agent.provide_insight(
        "Breaking down implementation into steps"
    )
    
    await context_agent.provide_insight(
        "System environment supports these steps"
    )
    
    await dialogue_agent.provide_insight(
        "Communication flow aligns with plan"
    )
    
    # Verify dialogue state
    assert len(dialogue.messages) == 3
    assert len(dialogue.participants) == 3
    assert dialogue.messages[0].agent_type == "task"
    assert dialogue.messages[1].agent_type == "context"
    assert dialogue.messages[2].agent_type == "dialogue"

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_collaborative_dialogue(use_mock):
    """Test full collaborative dialogue flow."""
    # Set up components
    agents = setup_test_agents()
    nova = agents['nova']
    
    # Process input
    response = await nova.process_interaction(TEST_INPUT)
    
    # Verify dialogue flow
    assert response.dialogue_context is not None
    assert len(response.dialogue_context.messages) > 0
    assert len(response.dialogue_context.participants) > 0
    assert response.dialogue_context.status == "active"
