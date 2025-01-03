"""Tests for the specialized BeliefAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.belief_agent import BeliefAgent
from src.nia.nova.core.belief import BeliefResult

@pytest.fixture
def belief_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a BeliefAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestBelief_{request.node.name}"
    
    # Update mock memory system for belief agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "beliefs": [{
            "statement": "This is important",
            "type": "belief",
            "confidence": 0.9
        }],
        "confidence": 0.9,
        "evidence": {
            "sources": ["document1"],
            "supporting_facts": ["fact1"],
            "contradictions": []
        }
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Configure memory storage
    mock_memory_system.semantic.store.store_memory = AsyncMock()
    mock_memory_system.semantic.store.record_reflection = AsyncMock()
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return BeliefAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(belief_agent, mock_memory_system):
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
                "value": "Advanced Belief Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Maintain domain boundaries",
                "secondary": ["Ensure belief consistency", "Validate belief foundations"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_domain": "mindful",
                "towards_beliefs": "analytical",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "domain_validation",
                "supporting": ["belief_analysis", "consistency_checking"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "belief_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestBelief" in belief_agent.name
    assert belief_agent.domain == "professional"
    assert belief_agent.agent_type == "belief"
    
    # Verify attributes were initialized
    attributes = belief_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify domain-specific attributes
    assert "Maintain domain boundaries" in attributes["desires"]
    assert "towards_domain" in attributes["emotions"]
    assert "domain_validation" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Belief agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Belief capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Belief tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Belief agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(belief_agent, mock_memory_system):
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
        "belief_analysis": {
            "complexity_level": "moderate",
            "belief_quality": 0.92,
            "domain_relevance": 0.95,
            "metrics": {
                "consistency": 0.90,
                "coherence": 0.89,
                "foundation": 0.93
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
                "belief_structure",
                "processing_efficiency"
            ],
            "areas_for_improvement": [
                "evidence_integration"
            ]
        }
    })
    
    # Process content
    response = await belief_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert belief_agent.emotions["towards_analysis"] == "focused"
    assert belief_agent.emotions["towards_domain"] == "mindful"
    
    # Verify processing state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality belief processing completed in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong belief accuracy achieved in professional domain",
        domain="professional"
    )
    
    # Verify structure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good belief structure maintained in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High processing efficiency demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Evidence integration enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_and_store(belief_agent, mock_memory_system):
    """Test belief analysis with domain awareness."""
    content = {
        "content": "I believe this is important",
        "type": "statement",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "analysis_requirements": "comprehensive"
        }
    }
    
    # Configure mock LLM response with detailed analysis results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "beliefs": [{
            "statement": "This is important",
            "type": "belief",
            "confidence": 0.92,
            "domain_relevance": 0.95,
            "impact_assessment": {
                "scope": "broad",
                "significance": "high",
                "duration": "long-term"
            }
        }],
        "confidence": 0.93,
        "evidence": {
            "sources": ["document1", "document2"],
            "supporting_facts": ["fact1", "fact2", "fact3"],
            "contradictions": [],
            "quality_metrics": {
                "source_reliability": 0.94,
                "fact_verification": 0.92,
                "consistency": 0.95
            }
        },
        "analysis_metrics": {
            "depth": 0.91,
            "coverage": 0.93,
            "precision": 0.94,
            "recall": 0.92
        },
        "quality_assessment": {
            "overall_score": 0.93,
            "strengths": [
                "evidence_quality",
                "belief_foundation"
            ],
            "areas_for_improvement": [
                "source_diversity"
            ]
        }
    })
    
    # Call analyze_and_store
    result = await belief_agent.analyze_and_store(content, target_domain="professional")
    
    # Verify result structure
    assert isinstance(result, BeliefResult)
    assert result.confidence > 0.9
    assert result.metadata["domain"] == "professional"
    
    # Verify memory storage was called
    assert belief_agent._memory_system.semantic.store.store_memory.call_count == 1
    call_args = belief_agent._memory_system.semantic.store.store_memory.call_args[0]
    
    # Verify content structure without timestamp
    expected_content = {
        "type": "belief_analysis",
        "content": content,
        "analysis": {
            "beliefs": result.beliefs,
            "confidence": result.confidence,
            "evidence": result.evidence,
            "timestamp": result.timestamp
        }
    }
    assert call_args[0] == expected_content
    
    # Verify context
    expected_context = {
        "type": "belief",
        "domain": "professional"
    }
    assert call_args[1] == expected_context
    
    # Verify analysis completion reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality belief analysis completed in professional domain",
        domain="professional"
    )
    
    # Verify evidence quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong evidence foundation established in professional domain",
        domain="professional"
    )
    
    # Verify precision reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High analysis precision achieved in professional domain",
        domain="professional"
    )
    
    # Verify coverage reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Comprehensive analysis coverage maintained in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Source diversity enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(belief_agent, mock_memory_system):
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
        "validation_metrics": {
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
            "validation_requirements": "strict"
        }
    }
    
    await belief_agent.validate_domain_access("professional")
    
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
    
    # Configure mock LLM response for denied access
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
    
    # Set up domain access validation to fail
    belief_agent.get_domain_access = AsyncMock(return_value=False)
    
    # Test denied domain
    with pytest.raises(PermissionError):
        await belief_agent.validate_domain_access("restricted")
    
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
async def test_analyze_with_different_domains(belief_agent, mock_memory_system):
    """Test analysis with different domain configurations."""
    content = {
        "content": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "domain_requirements": "cross_domain"
        }
    }
    
    # Configure mock LLM response for professional domain attempt
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "domain": "professional",
            "access_level": "restricted",
            "validation_metrics": {
                "permission_strength": 0.2,
                "access_scope": 0.1,
                "security_level": 0.9
            }
        },
        "security_analysis": {
            "overall_score": 0.92,
            "compliance_level": "high",
            "risk_assessment": {
                "level": "high",
                "factors": ["unauthorized_access", "scope_violation"]
            }
        }
    })
    
    # Set up domain access validation to fail for professional domain
    belief_agent.get_domain_access = AsyncMock(return_value=False)
    
    # Test professional domain (should fail)
    with pytest.raises(PermissionError):
        await belief_agent.analyze_and_store(content, target_domain="professional")
    
    # Verify access denial reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain access denied for professional domain",
        domain="professional"
    )
    
    # Verify security reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Security compliance enforced for unauthorized access attempt",
        domain="professional"
    )
    
    # Configure mock LLM response for personal domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "domain": "personal",
            "access_level": "full",
            "validation_metrics": {
                "permission_strength": 0.95,
                "access_scope": 0.94,
                "security_level": 0.92
            }
        },
        "beliefs": [{
            "statement": "Personal belief",
            "type": "belief",
            "confidence": 0.93,
            "domain_relevance": 0.95
        }],
        "confidence": 0.92,
        "evidence": {
            "sources": ["personal_doc1"],
            "supporting_facts": ["personal_fact1"],
            "quality_metrics": {
                "reliability": 0.91,
                "relevance": 0.93,
                "completeness": 0.90
            }
        }
    })
    
    # Reset mock for personal domain
    belief_agent.get_domain_access = AsyncMock(return_value=True)
    belief_agent.validate_domain_access = AsyncMock()
    
    # Test personal domain (should succeed)
    pers_result = await belief_agent.analyze_and_store(content, target_domain="personal")
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify access success reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain access validated successfully in personal domain",
        domain="personal"
    )
    
    # Verify permission reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong permission validation achieved in personal domain",
        domain="personal"
    )
    
    # Verify analysis reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality belief analysis completed in personal domain",
        domain="personal"
    )
    
    # Verify evidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong evidence foundation established in personal domain",
        domain="personal"
    )

@pytest.mark.asyncio
async def test_error_handling(belief_agent, mock_memory_system):
    """Test error handling during analysis."""
    content = {
        "content": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "error_handling": "strict"
        }
    }
    
    # Configure mock LLM response with error details
    error_message = "Test error during belief analysis"
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception(error_message))
    
    # Call analyze_and_store
    result = await belief_agent.analyze_and_store(content)
    
    # Verify error handling
    assert isinstance(result, BeliefResult)
    assert result.confidence == 0.0
    assert len(result.beliefs) == 0
    assert "error" in result.metadata
    assert result.metadata["error"]["message"] == error_message
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis error encountered in professional domain",
        domain="professional"
    )
    
    # Verify error handling reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Error handling protocol activated in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Recovery procedures initiated in professional domain",
        domain="professional"
    )
    
    # Verify state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis state reset in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for recovery attempt
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "error_recovery": {
            "status": "completed",
            "confidence": 0.0,
            "recovery_metrics": {
                "success": False,
                "completeness": 0.0,
                "reliability": 0.0
            }
        },
        "recovery_analysis": {
            "error_type": "analysis_failure",
            "severity": "high",
            "impact_assessment": {
                "scope": "local",
                "duration": "temporary"
            }
        }
    })
    
    # Verify recovery attempt reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Recovery attempt completed in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Error impact assessed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_reflection_recording(belief_agent):
    """Test reflection recording with domain awareness."""
    content = {"content": "test"}
    
    # Configure mock LLM response for high confidence case
    belief_agent._memory_system.llm.analyze = AsyncMock(return_value={
        "beliefs": [
            {
                "statement": "Important belief",
                "type": "belief",
                "confidence": 0.9,
                "domain_relevance": 0.9
            }
        ],
        "confidence": 0.9,
        "evidence": {
            "sources": ["document1"],
            "supporting_facts": ["fact1"],
            "contradictions": []
        }
    })
    
    result = await belief_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    belief_agent._memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence belief analysis completed in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case
    belief_agent._memory_system.llm.analyze = AsyncMock(return_value={
        "beliefs": [
            {
                "statement": "Uncertain belief",
                "type": "belief",
                "confidence": 0.2,
                "domain_relevance": 0.5
            }
        ],
        "confidence": 0.2,
        "evidence": {
            "sources": [],
            "supporting_facts": [],
            "contradictions": []
        }
    })
    
    result = await belief_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    belief_agent._memory_system.semantic.store.record_reflection.assert_any_call(
        "Low confidence belief analysis in professional domain - needs more evidence",
        domain="professional"
    )
    
    # Verify evidence reflection
    belief_agent._memory_system.semantic.store.record_reflection.assert_any_call(
        "Insufficient evidence found in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(belief_agent, mock_memory_system):
    """Test emotion updates based on analysis."""
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
            "belief_state": "confident",
            "analysis_state": "focused",
            "domain_state": "aligned",
            "quality_state": "positive"
        },
        "emotional_metrics": {
            "confidence": 0.95,
            "satisfaction": 0.92,
            "engagement": 0.94,
            "stability": 0.96
        },
        "emotional_analysis": {
            "primary_state": "optimal",
            "contributing_factors": [
                "strong_belief_foundation",
                "clear_domain_alignment"
            ],
            "stability_indicators": {
                "trend": "improving",
                "depth": "high",
                "sustainability": "strong"
            }
        }
    })
    
    await belief_agent.process(content)
    
    # Verify emotion updates
    assert belief_agent.emotions["towards_analysis"] == "focused"
    assert belief_agent.emotions["towards_domain"] == "aligned"
    
    # Verify emotional state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Confident belief state achieved in professional domain",
        domain="professional"
    )
    
    # Verify alignment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain alignment maintained in professional domain",
        domain="professional"
    )
    
    # Verify engagement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Deep belief engagement confirmed in professional domain",
        domain="professional"
    )
    
    # Verify stability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High emotional stability demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_desire_updates(belief_agent, mock_memory_system):
    """Test desire updates based on belief needs."""
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
                "type": "belief_requirement",
                "description": "Validate belief foundation",
                "priority": 0.9,
                "urgency": "high",
                "domain_relevance": 0.95
            },
            {
                "type": "quality_drive",
                "description": "Enhance belief accuracy",
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
            "primary_focus": "belief_quality",
            "driving_factors": [
                "accuracy_requirements",
                "foundation_validation"
            ],
            "priority_indicators": {
                "importance": "high",
                "urgency": "immediate",
                "sustainability": "strong"
            }
        }
    })
    
    await belief_agent.process(content)
    
    # Verify desire updates
    assert any("Validate" in desire for desire in belief_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong belief motivation established in professional domain",
        domain="professional"
    )
    
    # Verify focus reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear belief focus maintained in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High belief quality commitment identified in professional domain",
        domain="professional"
    )
    
    # Verify precision reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong belief precision demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_contradiction_reflection(belief_agent):
    """Test reflection recording for contradictions."""
    content = {"content": "test"}
    
    # Configure mock LLM response with contradictions
    belief_agent._memory_system.llm.analyze = AsyncMock(return_value={
        "beliefs": [
            {
                "statement": "Contradictory belief",
                "type": "belief",
                "confidence": 0.9,
                "domain_relevance": 0.9
            }
        ],
        "confidence": 0.9,
        "evidence": {
            "sources": ["document1", "document2"],
            "supporting_facts": ["fact1", "fact2"],
            "contradictions": [
                {
                    "statement": "Opposing view",
                    "source": "document2",
                    "severity": "high"
                }
            ]
        }
    })
    
    result = await belief_agent.analyze_and_store(content)
    
    # Verify contradiction reflection
    belief_agent._memory_system.semantic.store.record_reflection.assert_any_call(
        "Contradictory evidence found in professional domain - further investigation needed",
        domain="professional"
    )
    
    # Verify severity reflection
    belief_agent._memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity contradiction detected in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
