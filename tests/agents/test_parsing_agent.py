"""Tests for the specialized ParsingAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.parsing_agent import ParsingAgent
from src.nia.nova.core.parsing import ParseResult

@pytest.fixture
def parsing_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a ParsingAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestParsing_{request.node.name}"
    
    # Update mock memory system for parsing agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "statement": "Key concept",
                "type": "concept",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "complexity": 0.7
            },
            {
                "statement": "Need validation",
                "type": "validation_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "key_points": [
            {
                "statement": "Main point",
                "type": "key_point",
                "confidence": 0.8,
                "importance": 0.9
            }
        ],
        "structure": {
            "similar_parses": [
                {
                    "content": "Related parse",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "complexity_factors": [
                {
                    "factor": "readability",
                    "weight": 0.8
                }
            ]
        }
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return ParsingAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"],
        llm_type="generic"  # Add default llm_type for tests
    )

@pytest.mark.asyncio
async def test_initialization(parsing_agent, mock_memory_system):
    """Test agent initialization."""
    # Configure mock LLM response with detailed initialization results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "initialization_state": {
            "status": "completed",
            "confidence": 0.95,
            "metrics": {
                "setup_quality": 0.93,
                "attribute_completeness": 0.94,
                "capability_readiness": 0.92
            }
        },
        "attribute_validation": {
            "occupation": {
                "value": "Advanced Parsing Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Extract structured information",
                "secondary": ["Maintain parsing accuracy", "Optimize parsing processes"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_content": "focused",
                "towards_structure": "analytical",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "text_parsing",
                "supporting": ["structure_analysis", "content_organization"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "parsing_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Process empty content to trigger initialization reflections
    await parsing_agent.process({"text": "Initialize"})
    
    # Verify basic attributes
    assert "TestParsing" in parsing_agent.name
    assert parsing_agent.domain == "professional"
    assert parsing_agent.agent_type == "parsing"
    
    # Verify attributes were initialized
    attributes = parsing_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify parsing-specific attributes
    assert "Extract structured information" in attributes["desires"]
    assert attributes["emotions"]["towards_content"] == "focused"
    assert "text_parsing" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Parsing agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Parsing capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Parsing tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Parsing agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(parsing_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "complexity": "moderate"
        }
    }
    metadata = {
        "source": "test",
        "quality_requirements": {
            "accuracy": 0.9,
            "completeness": 0.85,
            "reliability": 0.92
        }
    }
    
    # Configure mock LLM response with detailed processing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "processing_state": {
            "status": "completed",
            "confidence": 0.95,
            "quality_metrics": {
                "accuracy": 0.93,
                "completeness": 0.91,
                "reliability": 0.94
            }
        },
        "content_analysis": {
            "complexity_level": "moderate",
            "structure_quality": 0.92,
            "domain_relevance": 0.95,
            "metrics": {
                "readability": 0.90,
                "coherence": 0.89,
                "consistency": 0.93
            }
        },
        "processing_metrics": {
            "execution_time": 0.15,
            "resource_usage": 0.45,
            "optimization_level": 0.92
        },
        "quality_analysis": {
            "overall_score": 0.93,
            "strengths": [
                "content_structure",
                "processing_efficiency"
            ],
            "areas_for_improvement": [
                "edge_case_handling"
            ]
        },
        "reflections": [
            {
                "content": "High confidence parsing completed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing motivation established in professional domain",
                "domain": "professional"
            },
            {
                "content": "Edge case handling improvements identified in professional domain",
                "domain": "professional"
            },
            {
                "content": "High quality processing completed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong processing accuracy achieved in professional domain",
                "domain": "professional"
            },
            {
                "content": "Good content structure maintained in professional domain",
                "domain": "professional"
            },
            {
                "content": "High processing efficiency demonstrated in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    response = await parsing_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "content_complexity" in parsing_agent.emotions
    assert any("Validate" in desire for desire in parsing_agent.desires)
    
    # Verify processing state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality processing completed in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong processing accuracy achieved in professional domain",
        domain="professional"
    )
    
    # Verify structure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good content structure maintained in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High processing efficiency demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Edge case handling improvements identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_parse_and_store(parsing_agent, mock_memory_system):
    """Test text parsing with domain awareness."""
    text = "Text content to parse"
    context = {
        "setting": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "parsing_requirements": "strict"
        }
    }
    
    # Configure mock LLM response with detailed parsing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "parsing_state": {
            "status": "completed",
            "confidence": 0.95,
            "quality_metrics": {
                "accuracy": 0.93,
                "completeness": 0.91,
                "reliability": 0.94
            }
        },
        "concepts": [
            {
                "statement": "Key concept",
                "type": "concept",
                "description": "positive",
                "confidence": 0.92,
                "domain_relevance": 0.95,
                "complexity": 0.85
            }
        ],
        "key_points": [
            {
                "statement": "Main point",
                "type": "key_point",
                "confidence": 0.91,
                "importance": 0.94
            }
        ],
        "structure": {
            "complexity": "moderate",
            "readability": "high",
            "coherence": 0.92,
            "metrics": {
                "structure_quality": 0.93,
                "organization": 0.91,
                "flow": 0.94
            }
        },
        "quality_analysis": {
            "overall_score": 0.93,
            "strengths": [
                "concept_extraction",
                "structural_analysis"
            ],
            "areas_for_improvement": [
                "context_integration"
            ]
        },
        "reflections": [
            {
                "content": "High confidence parsing completed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Edge case handling improvements identified in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing motivation established in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    result = await parsing_agent.parse_and_store(text, context)
    
    # Verify result structure
    assert isinstance(result, ParseResult)
    assert len(result.concepts) > 0
    assert len(result.key_points) > 0
    assert result.confidence > 0
    assert result.structure is not None
    
    # Verify memory storage was attempted
    mock_memory_system.episodic.store.store_memory.assert_called_once()
    
    # Verify parsing completion reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence parsing completed in professional domain",
        domain="professional"
    )
    
    # Verify concept extraction reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong concept extraction achieved in professional domain",
        domain="professional"
    )
    
    # Verify structure quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High structural quality maintained in professional domain",
        domain="professional"
    )
    
    # Verify readability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good readability level confirmed in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Context integration enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(parsing_agent, mock_memory_system):
    """Test domain access validation."""
    # Configure mock LLM response with detailed validation results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_validation": {
            "access_level": "full",
            "confidence": 0.95,
            "validation_metrics": {
                "permission_strength": 0.92,
                "access_scope": 0.94,
                "security_level": 0.91
            }
        },
        "security_analysis": {
            "overall_score": 0.93,
            "compliance_level": "high",
            "risk_assessment": {
                "level": "low",
                "factors": ["validated_access", "proper_scope"]
            }
        },
        "parsing_metrics": {
            "validation_time": 0.15,
            "permission_depth": 0.92,
            "scope_coverage": 0.94
        }
    })
    
    # Test allowed domain with detailed content
    content = {
        "type": "test",
        "metadata": {
            "importance": "high",
            "security_level": "standard",
            "parsing_requirements": "strict"
        }
    }
    
    await parsing_agent.validate_domain_access("professional")
    
    # Verify domain validation reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain access validated successfully in professional domain",
        domain="professional"
    )
    
    # Verify security reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High security compliance confirmed in professional domain",
        domain="professional"
    )
    
    # Verify permission reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong permission validation achieved in professional domain",
        domain="professional"
    )
    
    # Verify scope reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Full access scope verified in professional domain",
        domain="professional"
    )
    
    # Test denied domain with detailed error response
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_validation": {
            "access_level": "none",
            "confidence": 0.95,
            "validation_metrics": {
                "permission_strength": 0.0,
                "access_scope": 0.0,
                "security_level": 0.92
            }
        },
        "security_analysis": {
            "overall_score": 0.93,
            "compliance_level": "high",
            "risk_assessment": {
                "level": "high",
                "factors": ["unauthorized_access", "scope_violation"]
            }
        }
    })
    
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await parsing_agent.validate_domain_access("restricted")
    
    # Verify access denial reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain access denied for restricted domain",
        domain="professional"
    )
    
    # Verify security violation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Security compliance enforced for unauthorized access attempt",
        domain="professional"
    )
    
    # Verify risk reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High security risk prevented in professional domain",
        domain="professional"
    )
    
    # Verify scope violation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Access scope violation blocked in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_parse_with_different_domains(parsing_agent, mock_memory_system):
    """Test parsing with different domain configurations."""
    text = "test content"
    
    # Configure mock LLM response for professional domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "domain": "professional",
            "confidence": 0.95,
            "relevance": 0.94,
            "metrics": {
                "domain_alignment": 0.92,
                "content_fit": 0.93,
                "parsing_quality": 0.91
            }
        },
        "parsing_metrics": {
            "accuracy": 0.92,
            "completeness": 0.94,
            "reliability": 0.93
        },
        "quality_analysis": {
            "overall_score": 0.93,
            "strengths": ["domain_specific_parsing", "content_structure"],
            "areas_for_improvement": ["edge_cases"]
        },
        "reflections": [
            {
                "content": "High confidence parsing completed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Edge case handling improvements identified in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing motivation established in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    # Test professional domain
    prof_result = await parsing_agent.parse_and_store(
        text,
        {"domain": "professional"}
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Verify professional domain reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain alignment achieved in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High parsing quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong parsing accuracy demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Edge case handling improvements identified in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for personal domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "domain": "personal",
            "confidence": 0.93,
            "relevance": 0.92,
            "metrics": {
                "domain_alignment": 0.90,
                "content_fit": 0.91,
                "parsing_quality": 0.89
            }
        },
        "parsing_metrics": {
            "accuracy": 0.90,
            "completeness": 0.92,
            "reliability": 0.91
        },
        "quality_analysis": {
            "overall_score": 0.91,
            "strengths": ["personal_context_awareness", "informal_parsing"],
            "areas_for_improvement": ["formality_detection"]
        }
    })
    
    # Test personal domain
    parsing_agent.domain = "personal"
    pers_result = await parsing_agent.parse_and_store(
        text,
        {
            "domain": "personal",
            "type": "test",
            "metadata": {
                "importance": "high",
                "security_level": "standard",
                "parsing_requirements": "strict"
            }
        }
    )
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify personal domain reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain context awareness confirmed in personal domain",
        domain="personal"
    )
    
    # Verify parsing style reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Informal parsing style adapted in personal domain",
        domain="personal"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good parsing quality maintained in personal domain",
        domain="personal"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Formality detection enhancement identified in personal domain",
        domain="personal"
    )

@pytest.mark.asyncio
async def test_error_handling(parsing_agent, mock_memory_system):
    """Test error handling during parsing."""
    # Configure mock LLM response with detailed error analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "statement": "Error occurred during parsing",
                "type": "error",
                "description": "parsing_failure",
                "confidence": 0.0
            }
        ],
        "key_points": [
            {
                "statement": "Error occurred during parsing",
                "type": "error",
                "confidence": 0.0
            }
        ],
        "error_analysis": {
            "type": "parsing_failure",
            "severity": "high",
            "confidence": 0.0,
            "metrics": {
                "impact_severity": 0.92,
                "recovery_potential": 0.85,
                "system_stability": 0.88
            }
        },
        "failure_context": {
            "error_type": "content_processing",
            "affected_components": ["parser", "analyzer"],
            "state_integrity": "maintained",
            "metrics": {
                "component_health": 0.90,
                "data_integrity": 0.95,
                "system_responsiveness": 0.87
            }
        },
        "recovery_assessment": {
            "automated_recovery": "possible",
            "required_actions": ["reset_parser", "validate_state"],
            "estimated_effort": "medium",
            "success_probability": 0.82
        },
        "impact_analysis": {
            "scope": "localized",
            "duration": "temporary",
            "affected_operations": ["parsing", "analysis"],
            "mitigation_potential": "high"
        },
        "reflections": [
            {
                "content": "Parsing failed - error encountered in professional domain",
                "domain": "professional"
            },
            {
                "content": "High severity parsing error detected in professional domain",
                "domain": "professional"
            },
            {
                "content": "Localized error impact identified in professional domain",
                "domain": "professional"
            },
            {
                "content": "System stability maintained despite error in professional domain",
                "domain": "professional"
            },
            {
                "content": "Automated recovery possible with medium effort in professional domain",
                "domain": "professional"
            },
            {
                "content": "Data integrity preserved during error in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    result = await parsing_agent.parse_and_store("test")
    
    # Verify error handling
    assert isinstance(result, ParseResult)
    assert result.confidence == 0.0
    assert len(result.concepts) == 1
    assert result.concepts[0]["type"] == "error"
    assert len(result.key_points) == 1
    assert result.key_points[0]["type"] == "error"
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Parsing failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify severity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity parsing error detected in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Localized error impact identified in professional domain",
        domain="professional"
    )
    
    # Verify stability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "System stability maintained despite error in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Automated recovery possible with medium effort in professional domain",
        domain="professional"
    )
    
    # Verify integrity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Data integrity preserved during error in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_reflection_recording(parsing_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    text = "test content"
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "statement": "Key concept",
                "type": "concept",
                "description": "positive",
                "confidence": 0.9,
                "domain_relevance": 0.9
            }
        ],
        "key_points": [
            {
                "statement": "Main point",
                "confidence": 0.9
            }
        ],
        "structure": {
            "complexity": "low",
            "readability": "high"
        },
        "reflections": [
            {
                "content": "High confidence parsing completed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Confident parsing state achieved in professional domain",
                "domain": "professional"
            },
            {
                "content": "High content clarity maintained in professional domain",
                "domain": "professional"
            },
            {
                "content": "Deep parsing engagement confirmed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing confidence demonstrated in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong domain alignment achieved in professional domain",
                "domain": "professional"
            },
            {
                "content": "High parsing quality confirmed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing accuracy demonstrated in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    result = await parsing_agent.parse_and_store(text)
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence parsing completed in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "statement": "Unclear concept",
                "type": "concept",
                "description": "negative",
                "confidence": 0.2,
                "domain_relevance": 0.5
            }
        ],
        "key_points": [],
        "structure": {
            "complexity": "high",
            "readability": "low"
        }
    })
    
    result = await parsing_agent.parse_and_store(text)
    
    # Verify low confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Low confidence parsing in professional domain",
        domain="professional"
    )
    
    # Verify complexity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High complexity content detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(parsing_agent, mock_memory_system):
    """Test emotion updates based on content complexity."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "emotional_context": "positive"
        }
    }
    
    # Configure mock LLM response with detailed emotional states
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "emotions": {
            "parsing_state": "confident",
            "content_state": "clear",
            "complexity_state": "manageable",
            "quality_state": "positive"
        },
        "emotional_metrics": {
            "confidence": 0.95,
            "satisfaction": 0.92,
            "engagement": 0.94,
            "clarity": 0.96
        },
        "emotional_analysis": {
            "primary_state": "optimal",
            "contributing_factors": [
                "clear_content_structure",
                "strong_parsing_confidence"
            ],
            "engagement_indicators": {
                "trend": "increasing",
                "depth": "high",
                "sustainability": "strong"
            }
        },
        "reflections": [
            {
                "content": "Confident parsing state achieved in professional domain",
                "domain": "professional"
            },
            {
                "content": "High content clarity maintained in professional domain",
                "domain": "professional"
            },
            {
                "content": "Deep parsing engagement confirmed in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing confidence demonstrated in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    await parsing_agent.process(content)
    
    # Verify emotion updates
    assert "content_complexity" in parsing_agent.emotions
    assert parsing_agent.emotions["parsing_state"] == "confident"
    assert parsing_agent.emotions["content_state"] == "clear"
    
    # Verify emotional state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Confident parsing state achieved in professional domain",
        domain="professional"
    )
    
    # Verify clarity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High content clarity maintained in professional domain",
        domain="professional"
    )
    
    # Verify engagement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Deep parsing engagement confirmed in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong parsing confidence demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_desire_updates(parsing_agent, mock_memory_system):
    """Test desire updates based on validation needs."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "priority": "immediate"
        }
    }
    
    # Configure mock LLM response with detailed desire states
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "type": "parsing_requirement",
                "description": "Validate content structure",
                "priority": 0.9,
                "urgency": "high",
                "domain_relevance": 0.95
            },
            {
                "type": "quality_drive",
                "description": "Ensure parsing accuracy",
                "priority": 0.85,
                "impact": "significant",
                "potential": "high"
            }
        ],
        "desire_metrics": {
            "motivation": 0.92,
            "focus": 0.88,
            "commitment": 0.95,
            "precision": 0.94
        },
        "desire_analysis": {
            "primary_focus": "parsing_quality",
            "driving_factors": [
                "accuracy_requirements",
                "structure_validation"
            ],
            "priority_indicators": {
                "importance": "high",
                "urgency": "immediate",
                "sustainability": "strong"
            }
        },
        "reflections": [
            {
                "content": "Strong parsing motivation established in professional domain",
                "domain": "professional"
            },
            {
                "content": "Clear parsing focus maintained in professional domain",
                "domain": "professional"
            },
            {
                "content": "High parsing quality commitment identified in professional domain",
                "domain": "professional"
            },
            {
                "content": "Strong parsing precision demonstrated in professional domain",
                "domain": "professional"
            }
        ]
    })
    
    await parsing_agent.process(content)
    
    # Verify desire updates
    assert any("Validate" in desire for desire in parsing_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong parsing motivation established in professional domain",
        domain="professional"
    )
    
    # Verify focus reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear parsing focus maintained in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High parsing quality commitment identified in professional domain",
        domain="professional"
    )
    
    # Verify precision reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong parsing precision demonstrated in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
