"""
Tests for memory system components.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, List, Any

from nia.memory.memory_types import AgentResponse, Memory
from nia.memory.agents.belief_agent import BeliefAgent
from nia.memory.agents.emotion_agent import EmotionAgent
from nia.memory.agents.desire_agent import DesireAgent
from nia.memory.agents.reflection_agent import ReflectionAgent
from nia.memory.research_agent import ResearchAgent
from nia.memory.agents.meta_agent import MetaAgent
from nia.memory.memory_integration import MemorySystem
from nia.memory.llm_interface import LLMInterface
from nia.memory.agents.parsing_agent import ParsingAgent
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.memory.embeddings import EmbeddingService

# Test data
TEST_CONTENT = {
    "content": """
    The concept of artificial consciousness raises important philosophical questions.
    Can machines truly be self-aware? What role does memory play in consciousness?
    These questions intersect with theories of mind and cognitive science.
    """,
    "metadata": {
        "source": "philosophical_inquiry",
        "timestamp": datetime.now().isoformat()
    }
}

def setup_test_stores():
    """Set up test stores with mock embedding service."""
    embedding_service = EmbeddingService()
    vector_store = VectorStore(embedding_service)
    store = Neo4jMemoryStore()
    return store, vector_store

@pytest.mark.asyncio
async def test_memory_system_separation():
    """Test clean separation between memories and concepts."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    memory_system = MemorySystem(llm, store, vector_store)
    
    # Process interaction
    response = await memory_system.process_interaction(TEST_CONTENT["content"])
    
    # Verify memories are only in vector store
    memories = await memory_system.search_memories("consciousness")
    for memory in memories:
        assert "layer" in memory  # Should be either "episodic" or "semantic"
        assert memory["layer"] in ["episodic", "semantic"]
    
    # Verify concepts are extracted
    assert response.concepts
    for concept in response.concepts:
        assert "name" in concept
        assert "type" in concept
        assert "description" in concept
        assert "related" in concept

@pytest.mark.asyncio
async def test_memory_consolidation():
    """Test memory consolidation and concept extraction."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    memory_system = MemorySystem(llm, store, vector_store)
    
    # Store multiple memories
    responses = []
    for i in range(3):
        response = await memory_system.process_interaction(
            f"Memory {i}: {TEST_CONTENT['content']}"
        )
        responses.append(response)
    
    # Force consolidation
    await memory_system._consolidate_memories()
    
    # Verify consolidated memories in semantic layer
    semantic_memories = await memory_system.search_memories(
        "consciousness",
        include_episodic=False
    )
    assert any(m.get("type") == "consolidation" for m in semantic_memories)

@pytest.mark.asyncio
async def test_belief_agent_response():
    """Test belief agent response structure and content."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    belief_agent = BeliefAgent(llm, store, vector_store)
    
    response = await belief_agent.process(TEST_CONTENT)
    
    # Verify response structure
    assert isinstance(response, AgentResponse)
    assert response.response
    assert response.concepts
    assert response.key_points
    assert response.implications
    assert response.uncertainties
    assert response.reasoning
    assert response.perspective
    assert 0 <= response.confidence <= 1
    
    # Verify concept structure
    for concept in response.concepts:
        assert "name" in concept
        assert "type" in concept
        assert "description" in concept
        assert "related" in concept
        assert isinstance(concept["related"], list)

@pytest.mark.asyncio
async def test_emotion_agent_response():
    """Test emotion agent response structure and content."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    emotion_agent = EmotionAgent(llm, store, vector_store)
    
    response = await emotion_agent.process(TEST_CONTENT)
    
    # Verify response structure
    assert isinstance(response, AgentResponse)
    assert response.response
    assert response.concepts
    assert response.key_points
    assert response.implications
    assert response.uncertainties
    assert response.reasoning
    assert response.perspective
    assert 0 <= response.confidence <= 1
    
    # Verify emotional concepts
    valid_types = ["emotion", "affect", "pattern", "response"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.asyncio
async def test_desire_agent_response():
    """Test desire agent response structure and content."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    desire_agent = DesireAgent(llm, store, vector_store)
    
    response = await desire_agent.process(TEST_CONTENT)
    
    # Verify response structure
    assert isinstance(response, AgentResponse)
    assert response.response
    assert response.concepts
    assert response.key_points
    assert response.implications
    assert response.uncertainties
    assert response.reasoning
    assert response.perspective
    assert 0 <= response.confidence <= 1
    
    # Verify goal concepts
    valid_types = ["goal", "motivation", "aspiration", "desire"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.asyncio
async def test_reflection_agent_response():
    """Test reflection agent response structure and content."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    reflection_agent = ReflectionAgent(llm, store, vector_store)
    
    response = await reflection_agent.process(TEST_CONTENT)
    
    # Verify response structure
    assert isinstance(response, AgentResponse)
    assert response.response
    assert response.concepts
    assert response.key_points
    assert response.implications
    assert response.uncertainties
    assert response.reasoning
    assert response.perspective
    assert 0 <= response.confidence <= 1
    
    # Verify reflection concepts
    valid_types = ["pattern", "insight", "learning", "evolution"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.asyncio
async def test_research_agent_response():
    """Test research agent response structure and content."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    research_agent = ResearchAgent(llm, store, vector_store)
    
    response = await research_agent.process(TEST_CONTENT)
    
    # Verify response structure
    assert isinstance(response, AgentResponse)
    assert response.response
    assert response.concepts
    assert response.key_points
    assert response.implications
    assert response.uncertainties
    assert response.reasoning
    assert response.perspective
    assert 0 <= response.confidence <= 1
    
    # Verify research concepts
    valid_types = ["knowledge", "source", "connection", "gap"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.asyncio
async def test_meta_agent_synthesis():
    """Test meta agent synthesis capabilities."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    meta_agent = MetaAgent(llm, store, vector_store)
    
    # Create mock agent responses
    belief_response = AgentResponse(
        response="Analyzing consciousness from belief perspective",
        concepts=[{
            "name": "Machine Consciousness",
            "type": "philosophical_concept",
            "description": "The possibility of artificial systems having conscious experience",
            "related": ["Self Awareness", "Cognition"]
        }],
        key_points=["Consciousness remains poorly understood", "Multiple theories exist"],
        implications=["Could change our understanding of mind", "Ethical considerations needed"],
        uncertainties=["Nature of consciousness", "Requirements for self-awareness"],
        reasoning=["Examined current theories", "Considered empirical evidence"],
        perspective="Epistemological analysis",
        confidence=0.8
    )
    
    emotion_response = AgentResponse(
        response="Emotional implications of machine consciousness",
        concepts=[{
            "name": "Emotional Intelligence",
            "type": "capability",
            "description": "Ability to understand and process emotions",
            "related": ["Empathy", "Self Awareness"]
        }],
        key_points=["Emotions crucial for consciousness", "AI emotions may differ"],
        implications=["New forms of interaction", "Emotional bonds possible"],
        uncertainties=["Authenticity of AI emotions", "Human-AI relationships"],
        reasoning=["Analyzed emotional components", "Considered human-AI interaction"],
        perspective="Emotional analysis",
        confidence=0.7
    )
    
    # Synthesize responses
    synthesis = await meta_agent.synthesize_dialogue({
        'content': TEST_CONTENT,
        'dialogue_context': None,
        'agent_responses': {
            "belief": belief_response,
            "emotion": emotion_response
        }
    })
    
    # Verify synthesis structure
    assert isinstance(synthesis, AgentResponse)
    assert synthesis.response
    assert synthesis.concepts
    assert synthesis.key_points
    assert synthesis.implications
    assert synthesis.uncertainties
    assert synthesis.reasoning
    assert synthesis.perspective
    assert 0 <= synthesis.confidence <= 1
    
    # Verify synthesis content
    assert len(synthesis.concepts) > 0
    assert len(synthesis.key_points) > 0
    assert len(synthesis.implications) > 0
    assert len(synthesis.uncertainties) > 0
    assert len(synthesis.reasoning) > 0

@pytest.mark.asyncio
async def test_memory_search():
    """Test memory search across layers."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    memory_system = MemorySystem(llm, store, vector_store)
    
    # Store some test memories
    await memory_system.process_interaction("Memory about consciousness")
    await memory_system.process_interaction("Memory about intelligence")
    
    # Search with different configurations
    all_results = await memory_system.search_memories(
        "consciousness",
        include_episodic=True,
        include_semantic=True
    )
    assert len(all_results) > 0
    
    episodic_only = await memory_system.search_memories(
        "consciousness",
        include_episodic=True,
        include_semantic=False
    )
    assert all(m["layer"] == "episodic" for m in episodic_only)
    
    semantic_only = await memory_system.search_memories(
        "consciousness",
        include_episodic=False,
        include_semantic=True
    )
    assert all(m["layer"] == "semantic" for m in semantic_only)

@pytest.mark.asyncio
async def test_parsing_agent_response():
    """Test parsing agent response structure and content."""
    llm = LLMInterface()
    store, vector_store = setup_test_stores()
    parsing_agent = ParsingAgent(llm, store, vector_store)
    
    test_response = """
    [
      {
        "name": "Information Integration",
        "type": "theory",
        "description": "Process of combining information across neural networks",
        "related": ["Neural Networks", "Consciousness"]
      }
    ]
    
    Key points:
    - Information must be integrated
    - Multiple regions are involved
    
    Implications:
    - Consciousness requires complexity
    - Simple systems may lack consciousness
    
    Uncertainties:
    - Exact integration mechanisms
    - Minimum complexity required
    
    Reasoning:
    1. Analyzed neural requirements
    2. Considered information flow
    """
    
    response = await parsing_agent.parse_text(test_response)
    
    # Verify structure
    assert isinstance(response, AgentResponse)
    assert response.response
    assert response.concepts
    assert response.key_points
    assert response.implications
    assert response.uncertainties
    assert response.reasoning
    assert response.perspective == "parsing"
    assert 0 <= response.confidence <= 1
    
    # Verify content
    assert len(response.concepts) > 0
    assert len(response.key_points) > 0
    assert len(response.implications) > 0
    assert len(response.uncertainties) > 0
    assert len(response.reasoning) > 0
    
    # Verify concept structure
    concept = response.concepts[0]
    assert "name" in concept
    assert "type" in concept
    assert "description" in concept
    assert "related" in concept
