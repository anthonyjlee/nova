"""Test dialogue functionality."""

import pytest
from datetime import datetime
from src.nia.memory.memory_types import DialogueContext, DialogueMessage
from src.nia.memory.llm_interface import LLMInterface
from src.nia.memory.neo4j_store import Neo4jMemoryStore
from src.nia.memory.vector_store import VectorStore
from src.nia.memory.embeddings import EmbeddingService
from src.nia.memory.agents.meta_agent import MetaAgent
from src.nia.memory.agents.belief_agent import BeliefAgent
from src.nia.memory.agents.emotion_agent import EmotionAgent
from src.nia.memory.agents.reflection_agent import ReflectionAgent
from src.nia.memory.agents.task_planner_agent import TaskPlannerAgent

TEST_INPUT = """
Consider the relationship between consciousness and artificial intelligence.
How might emotional experiences differ between humans and AI systems?
What role does self-reflection play in developing understanding?
"""

def setup_test_agents():
    """Set up test agents."""
    llm = LLMInterface()
    store = Neo4jMemoryStore()
    vector_store = VectorStore(EmbeddingService())
    
    agents = {
        'nova': MetaAgent(llm, store, vector_store),
        'belief': BeliefAgent(llm, store, vector_store),
        'emotion': EmotionAgent(llm, store, vector_store),
        'reflection': ReflectionAgent(llm, store, vector_store),
        'task_planner': TaskPlannerAgent(llm, store, vector_store)
    }
    return agents

@pytest.mark.asyncio
async def test_dialogue_creation():
    """Test dialogue context creation."""
    # Create dialogue
    dialogue = DialogueContext(
        topic="Test Topic",
        status="active"
    )
    
    # Verify dialogue
    assert dialogue.topic == "Test Topic"
    assert dialogue.status == "active"
    assert isinstance(dialogue.created_at, datetime)
    assert isinstance(dialogue.messages, list)
    assert isinstance(dialogue.participants, list)

@pytest.mark.asyncio
async def test_dialogue_message_types():
    """Test different dialogue message types."""
    # Create message
    message = DialogueMessage(
        agent_type="test_agent",
        content="Test content",
        message_type="test_type",
        references=["ref1", "ref2"]
    )
    
    # Verify message
    assert message.agent_type == "test_agent"
    assert message.content == "Test content"
    assert message.message_type == "test_type"
    assert message.references == ["ref1", "ref2"]
    assert isinstance(message.timestamp, datetime)

@pytest.mark.asyncio
async def test_agent_message_sending():
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
    assert message.agent_type == "belief"
    assert message.content == "Test message"
    assert message.message_type == "test_type"
    assert message.references == ["ref1"]
    assert isinstance(message.timestamp, datetime)

@pytest.mark.asyncio
async def test_concept_validation():
    """Test concept validation through dialogue."""
    # Set up components
    agents = setup_test_agents()
    nova = agents['nova']
    belief_agent = agents['belief']
    emotion_agent = agents['emotion']
    
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
        "Consistent with observed emotional processing patterns",
        references=["AI Emotional Processing"]
    )
    
    # Get synthesis
    synthesis = await nova.synthesize_dialogue({
        'content': TEST_INPUT,
        'dialogue_context': dialogue
    })
    
    # Verify validation
    assert synthesis.concepts
    for concept in synthesis.concepts:
        assert isinstance(concept, dict)
        assert 'name' in concept
        assert 'type' in concept
        assert 'description' in concept
        assert 'validation' in concept
        validation = concept['validation']
        assert 'supported_by' in validation
        assert 'contradicted_by' in validation
        assert 'needs_verification' in validation

@pytest.mark.asyncio
async def test_collaborative_dialogue():
    """Test full collaborative dialogue flow."""
    # Set up components
    agents = setup_test_agents()
    nova = agents['nova']
    
    # Process input
    response = await nova.process_interaction(TEST_INPUT)
    
    # Verify dialogue flow
    assert response.dialogue_context is not None
    assert len(response.dialogue_context.messages) > 0
    assert len(response.dialogue_context.participants) > 1
    assert response.concepts

@pytest.mark.asyncio
async def test_dialogue_synthesis():
    """Test synthesis of collaborative dialogue."""
    # Set up components
    agents = setup_test_agents()
    nova = agents['nova']
    belief_agent = agents['belief']
    emotion_agent = agents['emotion']
    reflection_agent = agents['reflection']
    
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
        "Emotional processing shows unique patterns"
    )
    
    await reflection_agent.provide_insight(
        "Self-reflection capabilities are emerging"
    )
    
    # Synthesize dialogue
    synthesis = await nova.synthesize_dialogue({
        'content': TEST_INPUT,
        'dialogue_context': dialogue
    })
    
    # Verify synthesis
    assert synthesis.response
    assert synthesis.concepts
    assert synthesis.key_points
    assert synthesis.implications
    assert synthesis.reasoning
