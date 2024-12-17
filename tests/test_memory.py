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
from nia.memory.llm_interface import LLMInterface, extract_structured_content

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

@pytest.mark.asyncio
async def test_memory_system_separation():
    """Test clean separation between memories and concepts."""
    llm = LLMInterface()
    memory_system = MemorySystem(llm, None, None)  # Mock stores
    
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
    memory_system = MemorySystem(llm, None, None)
    
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
    belief_agent = BeliefAgent(llm, None, None)
    
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
    emotion_agent = EmotionAgent(llm, None, None)
    
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
    for concept in response.concepts:
        assert concept["type"] in ["emotion", "affect", "pattern", "response"]

@pytest.mark.asyncio
async def test_desire_agent_response():
    """Test desire agent response structure and content."""
    llm = LLMInterface()
    desire_agent = DesireAgent(llm, None, None)
    
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
    for concept in response.concepts:
        assert concept["type"] in ["goal", "motivation", "aspiration", "desire"]

@pytest.mark.asyncio
async def test_reflection_agent_response():
    """Test reflection agent response structure and content."""
    llm = LLMInterface()
    reflection_agent = ReflectionAgent(llm, None, None)
    
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
    for concept in response.concepts:
        assert concept["type"] in ["pattern", "insight", "learning", "evolution"]

@pytest.mark.asyncio
async def test_research_agent_response():
    """Test research agent response structure and content."""
    llm = LLMInterface()
    research_agent = ResearchAgent(llm, None, None)
    
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
    for concept in response.concepts:
        assert concept["type"] in ["knowledge", "source", "connection", "gap"]

@pytest.mark.asyncio
async def test_meta_agent_synthesis():
    """Test meta agent synthesis capabilities."""
    llm = LLMInterface()
    meta_agent = MetaAgent(llm, None, None)
    
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
    synthesis = await meta_agent.synthesize_responses(
        {
            "belief": belief_response,
            "emotion": emotion_response
        },
        TEST_CONTENT
    )
    
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
    memory_system = MemorySystem(llm, None, None)
    
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

def test_structured_content_extraction():
    """Test extraction of structured content from LLM response."""
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
    
    content = extract_structured_content(test_response)
    
    # Verify structure
    assert "concepts" in content
    assert "key_points" in content
    assert "implications" in content
    assert "uncertainties" in content
    assert "reasoning" in content
    
    # Verify content
    assert len(content["concepts"]) > 0
    assert len(content["key_points"]) > 0
    assert len(content["implications"]) > 0
    assert len(content["uncertainties"]) > 0
    assert len(content["reasoning"]) > 0
    
    # Verify concept structure
    concept = content["concepts"][0]
    assert "name" in concept
    assert "type" in concept
    assert "description" in concept
    assert "related" in concept
