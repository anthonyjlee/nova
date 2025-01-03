"""Tests for the specialized ValidationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.validation_agent import ValidationAgent
from src.nia.nova.core.validation import ValidationResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def validation_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a ValidationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestValidation_{request.node.name}"
    
    # Update mock memory system for validation agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "is_valid": True,
        "validations": [{
            "rule": "test_rule",
            "passed": True,
            "confidence": 0.8,
            "description": "positive"
        }],
        "confidence": 0.8,
        "metadata": {"domain": "professional"},
        "issues": [{
            "type": "test_issue",
            "severity": "medium",
            "description": "Test issue"
        }]
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return ValidationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(validation_agent, mock_memory_system):
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
                "value": "Advanced Validation Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Ensure content quality",
                "secondary": ["Maintain validation standards", "Optimize validation processes"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_validation": "focused",
                "towards_quality": "committed",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "content_validation",
                "supporting": ["quality_assurance", "standard_enforcement"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "validation_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestValidation" in validation_agent.name
    assert validation_agent.domain == "professional"
    assert validation_agent.agent_type == "validation"
    
    # Verify attributes were initialized
    attributes = validation_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify validation-specific attributes
    assert "Ensure content quality" in attributes["desires"]
    assert "towards_validation" in attributes["emotions"]
    assert "content_validation" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(validation_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "medium"
        }
    }
    metadata = {
        "source": "test",
        "confidence": 0.9,
        "quality_metrics": {
            "completeness": 0.92,
            "consistency": 0.88,
            "relevance": 0.95
        }
    }
    
    # Configure mock LLM response with detailed processing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "type": "validation_state",
                "state": "optimal",
                "confidence": 0.9
            },
            {
                "type": "domain_state",
                "state": "aligned",
                "confidence": 0.95
            },
            {
                "type": "processing_state",
                "state": "complete",
                "metrics": {
                    "efficiency": 0.93,
                    "accuracy": 0.91
                }
            }
        ],
        "emotions": {
            "validation_state": "confident",
            "domain_state": "positive",
            "processing_state": "satisfied"
        },
        "desires": [
            "Address validation requirements",
            "Maintain domain integrity",
            "Optimize processing efficiency"
        ]
    })
    
    response = await validation_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "validation_state" in validation_agent.emotions
    assert "domain_state" in validation_agent.emotions
    assert any("Address" in desire for desire in validation_agent.desires)
    
    # Verify state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Optimal validation state achieved in professional domain",
        domain="professional"
    )
    
    # Verify domain reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain alignment confirmed in professional domain",
        domain="professional"
    )
    
    # Verify processing reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Processing completed with high efficiency in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Content quality metrics exceed thresholds in professional domain",
        domain="professional"
    )
    
    # Verify emotional reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Positive emotional state maintained in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_validate_and_store(validation_agent, mock_memory_system):
    """Test content validation with domain awareness."""
    content = {
        "content": "Content to validate",
        "type": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "medium"
        }
    }
    
    # Configure mock LLM response with detailed validation results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "is_valid": True,
        "validations": [{
            "rule": "test_rule",
            "passed": True,
            "confidence": 0.9,
            "description": "positive",
            "domain_relevance": 0.9,
            "importance": "high",
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.92,
                "coverage": 0.88
            }
        }],
        "confidence": 0.9,
        "metadata": {
            "domain": "professional",
            "quality_score": 0.93,
            "validation_metrics": {
                "completeness": 0.91,
                "consistency": 0.89,
                "reliability": 0.94
            }
        },
        "issues": [{
            "type": "minor_issue",
            "severity": "low",
            "description": "Minor optimization possible",
            "impact": "minimal",
            "suggestions": ["Review validation thresholds"]
        }]
    })
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ValidationResult)
    assert len(result.validations) > 0
    assert result.confidence > 0
    assert len(result.issues) > 0
    
    # Verify memory storage
    assert hasattr(validation_agent, "store_memory")
    
    # Verify success reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence validation completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation quality exceeds threshold in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High validation accuracy achieved in professional domain",
        domain="professional"
    )
    
    # Verify reliability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong validation reliability confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Minor validation optimizations identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(validation_agent, mock_memory_system):
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
    
    await validation_agent.validate_domain_access("professional")
    
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
        await validation_agent.validate_domain_access("restricted")
    
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
async def test_validate_with_different_domains(validation_agent, mock_memory_system):
    """Test validation with different domain configurations."""
    # Configure mock LLM response with detailed domain validation results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "status": "validated",
            "confidence": 0.95,
            "metrics": {
                "domain_compatibility": 0.92,
                "validation_coverage": 0.94,
                "cross_domain_integrity": 0.91
            }
        },
        "validation_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["domain_adaptability", "validation_consistency"],
            "areas_for_improvement": ["cross_domain_optimization"]
        },
        "impact_analysis": {
            "scope": "multi_domain",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test content with detailed configuration
    content = {
        "content": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "validation_requirements": {
                "strictness": "high",
                "coverage": "comprehensive",
                "domain_specific": True
            }
        },
        "validation_context": {
            "source": "cross_domain",
            "priority": "immediate",
            "quality_threshold": 0.9
        }
    }
    
    # Test professional domain
    prof_result = await validation_agent.validate_and_store(
        content,
        validation_type="structure",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Test personal domain (assuming access)
    pers_result = await validation_agent.validate_and_store(
        content,
        validation_type="structure",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify domain validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Multi-domain validation completed successfully in professional domain",
        domain="professional"
    )
    
    # Verify compatibility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain compatibility demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify coverage reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High validation coverage achieved in professional domain",
        domain="professional"
    )
    
    # Verify integrity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Cross-domain integrity maintained in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Cross-domain optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Long-term multi-domain impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(validation_agent, mock_memory_system):
    """Test error handling during validation."""
    content = {
        "content": "Content to validate",
        "type": "test"
    }
    
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify error handling
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.validations) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation needs retry with adjusted parameters in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation error impacts content quality in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_reflection_recording(validation_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {
        "content": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "immediate"
        }
    }
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "is_valid": True,
        "validations": [{
            "rule": "test_rule",
            "passed": True,
            "confidence": 0.9,
            "description": "positive",
            "domain_relevance": 0.9,
            "importance": "high"
        }],
        "confidence": 0.9,
        "metadata": {
            "domain": "professional",
            "quality_score": 0.95,
            "performance_metrics": {
                "accuracy": 0.92,
                "completeness": 0.88
            }
        },
        "issues": []
    })
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence validation completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Exceptional validation quality achieved in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High validation accuracy confirmed in professional domain",
        domain="professional"
    )
    
    # Verify completeness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation completeness meets standards in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case with detailed issues
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "is_valid": False,
        "validations": [{
            "rule": "test_rule",
            "passed": False,
            "confidence": 0.5,
            "description": "negative",
            "domain_relevance": 0.8,
            "impact": "significant"
        }],
        "confidence": 0.5,
        "metadata": {
            "domain": "professional",
            "quality_score": 0.45,
            "failure_analysis": {
                "primary_cause": "incomplete_validation",
                "affected_areas": ["data_quality", "structure"],
                "remediation_priority": "high"
            }
        },
        "issues": [{
            "type": "test_issue",
            "severity": "medium",
            "description": "Test issue",
            "impact_areas": ["content_quality", "domain_integrity"],
            "remediation_steps": ["review_validation_rules", "adjust_thresholds"]
        }]
    })
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify failure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation failed in professional domain",
        domain="professional"
    )
    
    # Verify quality impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation quality below threshold in professional domain",
        domain="professional"
    )
    
    # Verify remediation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation requires immediate remediation in professional domain",
        domain="professional"
    )
    
    # Verify integrity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain integrity requires attention in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_critical_issue_reflection(validation_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {
        "content": "Content to validate",
        "type": "test"
    }
    
    # Configure mock LLM response with critical issue
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "is_valid": False,
        "validations": [
            {
                "rule": "critical_check",
                "passed": False,
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "severity": "high"
            }
        ],
        "confidence": 0.9,
        "metadata": {"domain": "professional"},
        "issues": [
            {
                "type": "critical_issue",
                "severity": "high",
                "description": "Critical validation problem",
                "domain_impact": 0.9,
                "implications": [
                    "Content quality compromised",
                    "Immediate attention required"
                ]
            }
        ]
    })
    
    result = await validation_agent.validate_and_store(
        content,
        validation_type="structure"
    )
    
    # Verify critical issue reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Critical validation issues detected in professional domain",
        domain="professional"
    )
    
    # Verify severity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity validation issue requires immediate attention in professional domain",
        domain="professional"
    )
    
    # Verify domain impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation issue has significant domain impact in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Content quality compromised in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(validation_agent, mock_memory_system):
    """Test emotion updates based on validation results."""
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
            "validation_state": "confident",
            "domain_state": "aligned",
            "processing_state": "satisfied",
            "quality_state": "positive"
        },
        "emotional_metrics": {
            "confidence": 0.95,
            "satisfaction": 0.92,
            "stability": 0.88
        },
        "emotional_analysis": {
            "primary_state": "optimal",
            "contributing_factors": [
                "high_validation_quality",
                "strong_domain_alignment"
            ],
            "stability_indicators": {
                "trend": "improving",
                "volatility": "low"
            }
        }
    })
    
    await validation_agent.process(content)
    
    # Verify emotion updates
    assert "validation_state" in validation_agent.emotions
    assert "domain_state" in validation_agent.emotions
    
    # Verify emotional state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Confident emotional state achieved in professional domain",
        domain="professional"
    )
    
    # Verify satisfaction reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High emotional satisfaction maintained in professional domain",
        domain="professional"
    )
    
    # Verify stability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Emotional stability confirmed in professional domain",
        domain="professional"
    )
    
    # Verify trend reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Positive emotional trend identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_desire_updates(validation_agent, mock_memory_system):
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
                "type": "validation_requirement",
                "description": "Address validation completeness",
                "priority": 0.9,
                "urgency": "high"
            },
            {
                "type": "quality_improvement",
                "description": "Enhance validation precision",
                "priority": 0.85,
                "impact": "significant"
            }
        ],
        "desire_metrics": {
            "motivation": 0.92,
            "focus": 0.88,
            "commitment": 0.95
        },
        "desire_analysis": {
            "primary_focus": "validation_quality",
            "driving_factors": [
                "quality_requirements",
                "domain_standards"
            ],
            "priority_indicators": {
                "importance": "high",
                "urgency": "immediate"
            }
        }
    })
    
    await validation_agent.process(content)
    
    # Verify desire updates
    assert any("Address" in desire for desire in validation_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong validation motivation established in professional domain",
        domain="professional"
    )
    
    # Verify focus reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear validation focus maintained in professional domain",
        domain="professional"
    )
    
    # Verify priority reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High priority validation desires identified in professional domain",
        domain="professional"
    )
    
    # Verify commitment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong validation commitment demonstrated in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
