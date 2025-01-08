"""Tests for memory consolidation and pattern extraction in TinyTroupe."""

import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock
from tests.nova.test_utils import (
    with_vector_store_retry,
    TestContext
)

from nia.memory.types.memory_types import (
    Memory, MemoryType, EpisodicMemory, Concept, Relationship
)

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_importance_based_consolidation(nova):
    """Test consolidation triggered by importance."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="consolidation_agent",
            attributes={
                "skills": ["development"],
                "domain": domain
            }
        )
        
        # Create important memory
        memory = EpisodicMemory(
            content="Critical system update",
            type=MemoryType.EPISODIC,
            timestamp=datetime.now().isoformat(),
            importance=0.9,
            concepts=[
                Concept(
                    name="System Update",
                    type="Maintenance",
                    category="Maintenance",
                    description="Critical system maintenance update",
                    attributes={"priority": "high"},
                    confidence=0.9
                )
            ]
        )
        
        # Store memory
        memory_id = await agent.store_memory(
            content=memory.content,
            importance=memory.importance,
            context={
                "domain": domain,
                "agent_type": "worker"
            },
            concepts=memory.concepts
        )
        
        # Mock consolidation candidates
        mock_memory = nova.create_memory_mock(
            content=memory.content,
            context={"domain": domain},
            concepts=memory.concepts,
            importance=memory.importance
        )
        mock_memory.id = memory_id
        
        nova.memory_system.episodic.get_consolidation_candidates = AsyncMock(return_value=[mock_memory])
        
        # Trigger consolidation
        await agent.reflect()
        
        # Verify consolidation was triggered
        nova.memory_system.semantic.store_knowledge.assert_called_once()
        stored_knowledge = nova.memory_system.semantic.store_knowledge.call_args[0][0]
        
        # Verify concept was stored
        assert len(stored_knowledge["concepts"]) == 1
        concept = stored_knowledge["concepts"][0]
        assert concept["name"] == "System Update"
        assert concept["type"] == "Maintenance"
        assert concept["attributes"]["priority"] == "high"

@pytest.mark.asyncio
async def test_memory_consolidation_patterns(nova):
    """Test different memory consolidation patterns."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        worker = await nova.spawn_agent(
            agent_type="worker",
            name="worker_agent",
            attributes={
                "skills": ["task_execution"],
                "domain": domain
            }
        )
        
        # Store related memories that should form a pattern
        memories = [
            {
                "content": "Implemented user authentication",
                "concepts": [
                    {
                        "name": "Authentication",
                        "type": "Feature",
                        "category": "security",
                        "description": "User authentication system",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "content": "Added password hashing",
                "concepts": [
                    {
                        "name": "Password Hashing",
                        "type": "Component",
                        "category": "security",
                        "description": "Password security feature",
                        "confidence": 0.9
                    }
                ],
                "relationships": [
                    {
                        "from_concept": "Password Hashing",
                        "to_concept": "Authentication",
                        "type": "implements",
                        "properties": {"security_level": "high"}
                    }
                ]
            },
            {
                "content": "Implemented session management",
                "concepts": [
                    {
                        "name": "Session Management",
                        "type": "Component",
                        "category": "security",
                        "description": "User session handling",
                        "confidence": 0.9
                    }
                ],
                "relationships": [
                    {
                        "from_concept": "Session Management",
                        "to_concept": "Authentication",
                        "type": "implements",
                        "properties": {"type": "stateful"}
                    }
                ]
            }
        ]
        
        # Store memories
        memory_ids = []
        for memory in memories:
            memory_id = await worker.store_memory(
                content=memory["content"],
                importance=0.8,
                context={
                    "domain": domain,
                    "agent_type": "worker"
                },
                concepts=memory.get("concepts", []),
                relationships=memory.get("relationships", [])
            )
            memory_ids.append(memory_id)
        
        # Mock consolidation candidates
        mock_memories = []
        for i, memory in enumerate(memories):
            mock_memory = nova.create_memory_mock(
                content=memory["content"],
                context={"domain": domain},
                concepts=memory.get("concepts", []),
                relationships=memory.get("relationships", [])
            )
            mock_memory.id = memory_ids[i]
            mock_memories.append(mock_memory)
        
        nova.memory_system.episodic.get_consolidation_candidates = AsyncMock(return_value=mock_memories)
        
        # Trigger consolidation
        await worker.reflect()
        
        # Verify pattern extraction
        stored_knowledge = nova.memory_system.semantic.store_knowledge.call_args[0][0]
        
        # Verify security pattern was extracted
        security_concepts = [c for c in stored_knowledge["concepts"] 
                           if c["category"] == "security"]
        assert len(security_concepts) == 3
        
        # Verify concept types
        concept_types = {c["type"] for c in security_concepts}
        assert concept_types == {"Feature", "Component"}
        
        # Verify implementation relationships
        impl_relations = [r for r in stored_knowledge["relationships"]
                         if r["type"] == "implements"]
        assert len(impl_relations) == 2
        
        # Verify relationship properties
        hashing_rel = next(r for r in impl_relations 
                          if r["from"] == "Password Hashing")
        assert hashing_rel["properties"]["security_level"] == "high"
        
        session_rel = next(r for r in impl_relations 
                          if r["from"] == "Session Management")
        assert session_rel["properties"]["type"] == "stateful"

@pytest.mark.asyncio
async def test_complex_pattern_consolidation(nova):
    """Test consolidation of complex patterns with multiple relationships."""
    domain = "development"
    
    async with TestContext(nova.memory_system, domain):
        # Create agent
        agent = await nova.spawn_agent(
            agent_type="worker",
            name="pattern_agent",
            attributes={
                "skills": ["development"],
                "domain": domain
            }
        )
        
        # Create memories forming a complex pattern
        memories = [
            {
                "content": "Created API endpoint for user data",
                "concepts": [
                    {
                        "name": "User API",
                        "type": "Component",
                        "category": "api",
                        "description": "User data API endpoint",
                        "confidence": 0.9
                    }
                ]
            },
            {
                "content": "Implemented data validation",
                "concepts": [
                    {
                        "name": "Data Validation",
                        "type": "Feature",
                        "category": "security",
                        "description": "Input data validation",
                        "confidence": 0.9
                    }
                ],
                "relationships": [
                    {
                        "from_concept": "Data Validation",
                        "to_concept": "User API",
                        "type": "protects",
                        "properties": {"level": "input"}
                    }
                ]
            },
            {
                "content": "Added rate limiting",
                "concepts": [
                    {
                        "name": "Rate Limiting",
                        "type": "Feature",
                        "category": "security",
                        "description": "API rate limiting",
                        "confidence": 0.9
                    }
                ],
                "relationships": [
                    {
                        "from_concept": "Rate Limiting",
                        "to_concept": "User API",
                        "type": "protects",
                        "properties": {"level": "request"}
                    }
                ]
            }
        ]
        
        # Store memories
        memory_ids = []
        for memory in memories:
            memory_id = await agent.store_memory(
                content=memory["content"],
                importance=0.8,
                context={
                    "domain": domain,
                    "agent_type": "worker"
                },
                concepts=memory.get("concepts", []),
                relationships=memory.get("relationships", [])
            )
            memory_ids.append(memory_id)
        
        # Mock consolidation candidates
        mock_memories = []
        for i, memory in enumerate(memories):
            mock_memory = nova.create_memory_mock(
                content=memory["content"],
                context={"domain": domain},
                concepts=memory.get("concepts", []),
                relationships=memory.get("relationships", [])
            )
            mock_memory.id = memory_ids[i]
            mock_memories.append(mock_memory)
        
        nova.memory_system.episodic.get_consolidation_candidates = AsyncMock(return_value=mock_memories)
        
        # Trigger consolidation
        await agent.reflect()
        
        # Verify pattern extraction
        stored_knowledge = nova.memory_system.semantic.store_knowledge.call_args[0][0]
        
        # Verify concepts were extracted
        assert len(stored_knowledge["concepts"]) == 3
        
        # Verify protection relationships
        protect_relations = [r for r in stored_knowledge["relationships"]
                           if r["type"] == "protects"]
        assert len(protect_relations) == 2
        
        # Verify relationship properties
        input_protection = next(r for r in protect_relations
                              if r["properties"]["level"] == "input")
        assert input_protection["from"] == "Data Validation"
        assert input_protection["to"] == "User API"
        
        request_protection = next(r for r in protect_relations
                                if r["properties"]["level"] == "request")
        assert request_protection["from"] == "Rate Limiting"
        assert request_protection["to"] == "User API"
