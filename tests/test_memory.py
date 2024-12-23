"""
Tests for memory system components.
"""

import pytest
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

@pytest.fixture
def use_mock(request):
    """Fixture to control mock vs real LMStudio usage.
    
    Add --use-mock flag to pytest command to use mocks instead of real LMStudio.
    Default is to use real LMStudio for integration testing.
    """
    return request.config.getoption("--use-mock", default=False)

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
from nia.memory.agents.task_agent import TaskAgent
from nia.memory.agents.dialogue_agent import DialogueAgent
from nia.memory.agents.context_agent import ContextAgent

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

class MockEmbeddingService(EmbeddingService):
    """Mock embedding service that returns consistent embeddings."""
    async def get_embedding(self, text: str) -> List[float]:
        """Return a consistent embedding for testing."""
        # Return a fixed-size vector of 384 dimensions (same as default)
        return [0.1] * 384

def setup_test_stores():
    """Set up test stores with mock embedding service."""
    embedding_service = MockEmbeddingService()
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

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_memory_system_separation(use_mock):
    """Test clean separation between memories and concepts."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_memory_consolidation(use_mock):
    """Test memory consolidation and concept extraction."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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
async def test_belief_agent_response(use_mock, lmstudio_available, capfd):
    """Test belief agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
    belief_agent = BeliefAgent(llm, store, vector_store)
    
    logger.debug(f"Test content: {TEST_CONTENT}")
    response = await belief_agent.process(TEST_CONTENT)
    
    # Print response for inspection
    logger.debug(f"Raw response: {response}")
    print("\nBelief Agent Response:")
    print(f"Response: {response.response}")
    print("\nConcepts:")
    for concept in response.concepts:
        print(f"- {concept['name']} ({concept['type']}): {concept['description']}")
    print("\nKey Points:", response.key_points)
    print("Implications:", response.implications)
    print("Uncertainties:", response.uncertainties)
    print("Reasoning:", response.reasoning)
    
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
    
    # Verify concept structure and content
    for concept in response.concepts:
        # Structure validation
        assert "name" in concept, "Concept missing name field"
        assert "type" in concept, "Concept missing type field"
        assert "description" in concept, "Concept missing description field"
        assert "related" in concept, "Concept missing related field"
        assert isinstance(concept["related"], list), "Related field must be a list"
        assert "validation" in concept, "Concept missing validation field"
        
        # Content validation
        assert len(concept["name"]) > 0, "Concept name cannot be empty"
        assert len(concept["description"]) > 0, "Concept description cannot be empty"
        assert concept["type"] in ["belief", "philosophical_concept", "theory", "understanding"], \
            f"Invalid concept type: {concept['type']}"
        
        # Validation field structure
        validation = concept["validation"]
        assert "confidence" in validation, "Validation missing confidence score"
        assert isinstance(validation["confidence"], (int, float)), "Confidence must be numeric"
        assert 0 <= validation["confidence"] <= 1, "Confidence must be between 0 and 1"
        assert "supported_by" in validation, "Validation missing supported_by field"
        assert "contradicted_by" in validation, "Validation missing contradicted_by field"
        assert "needs_verification" in validation, "Validation missing needs_verification field"

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_emotion_agent_response(use_mock):
    """Test emotion agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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
    
    # Verify concept structure and content
    for concept in response.concepts:
        # Structure validation
        assert "name" in concept, "Concept missing name field"
        assert "type" in concept, "Concept missing type field"
        assert "description" in concept, "Concept missing description field"
        assert "related" in concept, "Concept missing related field"
        assert isinstance(concept["related"], list), "Related field must be a list"
        assert "validation" in concept, "Concept missing validation field"
        
        # Content validation
        assert len(concept["name"]) > 0, "Concept name cannot be empty"
        assert len(concept["description"]) > 0, "Concept description cannot be empty"
        assert concept["type"] in ["emotion", "affect", "pattern", "response"], \
            f"Invalid concept type: {concept['type']}"
        
        # Validation field structure
        validation = concept["validation"]
        assert "confidence" in validation, "Validation missing confidence score"
        assert isinstance(validation["confidence"], (int, float)), "Confidence must be numeric"
        assert 0 <= validation["confidence"] <= 1, "Confidence must be between 0 and 1"
        assert "supported_by" in validation, "Validation missing supported_by field"
        assert "contradicted_by" in validation, "Validation missing contradicted_by field"
        assert "needs_verification" in validation, "Validation missing needs_verification field"
        
        # Emotion-specific validation
        if concept["type"] == "emotion":
            assert len(concept["related"]) > 0, "Emotion concept must have related terms"
            assert any("intensity" in field.lower() or 
                      "strength" in field.lower() or 
                      "valence" in field.lower() 
                      for field in concept["description"].split()), \
                "Emotion description should include intensity/strength/valence"

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_desire_agent_response(use_mock):
    """Test desire agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_reflection_agent_response(use_mock):
    """Test reflection agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_research_agent_response(use_mock):
    """Test research agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_task_agent_response(use_mock):
    """Test task agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
    task_agent = TaskAgent(llm, store, vector_store)
    
    response = await task_agent.process(TEST_CONTENT)
    
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
    
    # Verify task concepts
    valid_types = ["task", "step", "dependency", "milestone"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_dialogue_agent_response(use_mock):
    """Test dialogue agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
    dialogue_agent = DialogueAgent(llm, store, vector_store)
    
    response = await dialogue_agent.process(TEST_CONTENT)
    
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
    
    # Verify dialogue concepts
    valid_types = ["interaction", "flow", "exchange", "dynamic"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_context_agent_response(use_mock):
    """Test context agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
    context_agent = ContextAgent(llm, store, vector_store)
    
    response = await context_agent.process(TEST_CONTENT)
    
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
    
    # Verify context concepts
    valid_types = ["context", "situation", "environment", "condition"]
    for concept in response.concepts:
        assert concept["type"] in valid_types

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_meta_agent_synthesis(use_mock):
    """Test meta agent synthesis capabilities."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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

@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_memory_search(use_mock):
    """Test memory search across layers."""
    llm, store, vector_store = setup_test_llm()
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
@pytest.mark.requires_lmstudio
@pytest.mark.asyncio
async def test_parsing_agent_response(use_mock):
    """Test parsing agent response structure and content."""
    llm, store, vector_store = setup_test_llm(use_mock=use_mock)
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
