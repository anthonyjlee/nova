"""Tests for the specialized IntegrationAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.integration_agent import IntegrationAgent
from src.nia.nova.core.integration import IntegrationResult

@pytest.fixture
def integration_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create an IntegrationAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestIntegration_{request.node.name}"
    
    # Update mock memory system for integration agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.8,
                    "description": "Main content"
                }
            }
        },
        "insights": [
            {
                "type": "connection",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "integration_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_connection",
                "severity": "medium",
                "description": "Missing connection",
                "domain_impact": 0.3
            }
        ]
    })
    
    # Configure domain access
    mock_memory_system.semantic.store.get_domain_access = AsyncMock(
        side_effect=lambda agent, domain: domain == "professional"
    )
    
    # Create agent with updated config
    config = base_agent_config.copy()
    config["name"] = agent_name
    config["domain"] = "professional"
    
    return IntegrationAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(integration_agent, mock_memory_system):
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
                "value": "Advanced Integration Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Connect insights meaningfully",
                "secondary": ["Maintain integration quality", "Optimize integration processes"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_content": "focused",
                "towards_integration": "analytical",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "content_integration",
                "supporting": ["pattern_recognition", "insight_synthesis"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "integration_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestIntegration" in integration_agent.name
    assert integration_agent.domain == "professional"
    assert integration_agent.agent_type == "integration"
    
    # Verify attributes were initialized
    attributes = integration_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify integration-specific attributes
    assert "Connect insights meaningfully" in attributes["desires"]
    assert "towards_content" in attributes["emotions"]
    assert "content_integration" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Integration agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Integration capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Integration tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Integration agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(integration_agent, mock_memory_system):
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
        }
    })
    
    response = await integration_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "integration_state" in integration_agent.emotions
    assert "domain_state" in integration_agent.emotions
    assert any("Connect" in desire for desire in integration_agent.desires)
    
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
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong quality metrics achieved in professional domain",
        domain="professional"
    )
    
    # Verify reliability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High reliability standards maintained in professional domain",
        domain="professional"
    )
    
    # Verify coherence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good content coherence demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_integrate_and_store(integration_agent, mock_memory_system):
    """Test content integration with domain awareness."""
    content = {
        "text": "Content to integrate",
        "type": "synthesis",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "integration_requirements": {
                "accuracy": 0.9,
                "completeness": 0.85,
                "reliability": 0.92
            }
        }
    }
    
    # Configure mock LLM response with detailed integration results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "integration_state": {
            "status": "completed",
            "confidence": 0.95,
            "quality_metrics": {
                "accuracy": 0.93,
                "completeness": 0.91,
                "reliability": 0.94
            }
        },
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.9,
                    "description": "Main content",
                    "metrics": {
                        "coherence": 0.92,
                        "relevance": 0.94,
                        "structure": 0.91
                    }
                }
            },
            "metrics": {
                "component_quality": 0.93,
                "integration_depth": 0.92,
                "synthesis_strength": 0.94
            }
        },
        "insights": [
            {
                "type": "connection",
                "description": "Strong pattern identified",
                "confidence": 0.92,
                "domain_relevance": 0.95,
                "importance": 0.9,
                "metrics": {
                    "clarity": 0.93,
                    "support": 0.91,
                    "impact": 0.94
                }
            }
        ],
        "processing_metrics": {
            "execution_time": 0.15,
            "resource_usage": 0.45,
            "optimization_level": 0.92
        },
        "quality_analysis": {
            "overall_score": 0.93,
            "strengths": [
                "pattern_recognition",
                "synthesis_quality"
            ],
            "areas_for_improvement": [
                "edge_case_coverage"
            ]
        }
    })
    
    result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, IntegrationResult)
    assert result.integration["type"] == "synthesis"
    assert len(result.integration["components"]) == 1
    assert len(result.insights) > 0
    assert result.confidence > 0
    
    # Verify memory storage
    assert hasattr(integration_agent, "store_memory")
    
    # Verify completion reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality integration completed in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong integration accuracy achieved in professional domain",
        domain="professional"
    )
    
    # Verify component reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High component quality maintained in professional domain",
        domain="professional"
    )
    
    # Verify synthesis reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong synthesis strength demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify pattern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear pattern recognition achieved in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High synthesis quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Edge case coverage enhancement identified in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong optimization level maintained in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(integration_agent, mock_memory_system):
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
                "factors": ["validated_access", "proper_scope"],
                "metrics": {
                    "threat_level": 0.15,
                    "vulnerability_score": 0.12,
                    "impact_potential": 0.18
                }
            }
        },
        "validation_metrics": {
            "validation_time": 0.15,
            "permission_depth": 0.92,
            "scope_coverage": 0.94,
            "verification_quality": {
                "accuracy": 0.93,
                "completeness": 0.91,
                "reliability": 0.94
            }
        },
        "access_analysis": {
            "status": "granted",
            "confidence": 0.95,
            "metrics": {
                "authorization_strength": 0.92,
                "permission_granularity": 0.94,
                "access_stability": 0.91
            },
            "security_context": {
                "encryption_level": "high",
                "authentication_quality": 0.93,
                "integrity_checks": "passed"
            }
        }
    })
    
    # Test allowed domain
    await integration_agent.validate_domain_access("professional")
    
    # Verify validation reflection
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
                "factors": ["unauthorized_access", "scope_violation"],
                "metrics": {
                    "threat_level": 0.85,
                    "vulnerability_score": 0.78,
                    "impact_potential": 0.82
                }
            }
        },
        "validation_metrics": {
            "validation_time": 0.15,
            "permission_depth": 0.0,
            "scope_coverage": 0.0,
            "verification_quality": {
                "accuracy": 0.93,
                "completeness": 0.91,
                "reliability": 0.94
            }
        }
    })
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await integration_agent.validate_domain_access("restricted")
    
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
    
    # Verify threat reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Elevated threat level detected in professional domain",
        domain="professional"
    )
    
    # Verify protection reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Access protection measures activated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_integrate_with_different_domains(integration_agent, mock_memory_system):
    """Test integration with different domain configurations."""
    content = {
        "text": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "cross_domain": True,
            "integration_requirements": {
                "domain_coverage": 0.9,
                "consistency": 0.85,
                "adaptability": 0.92
            }
        }
    }
    
    # Configure mock LLM response for professional domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "status": "validated",
            "confidence": 0.95,
            "metrics": {
                "domain_compatibility": 0.92,
                "integration_coverage": 0.94,
                "cross_domain_integrity": 0.91
            }
        },
        "integration_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["domain_adaptability", "integration_consistency"],
            "areas_for_improvement": ["cross_domain_optimization"]
        },
        "impact_analysis": {
            "scope": "multi_domain",
            "duration": "long_term",
            "confidence": 0.94,
            "metrics": {
                "effectiveness": 0.92,
                "sustainability": 0.89,
                "scalability": 0.91
            }
        }
    })
    
    # Test professional domain
    prof_result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Verify domain validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Multi-domain integration completed successfully in professional domain",
        domain="professional"
    )
    
    # Verify compatibility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain compatibility demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify coverage reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High integration coverage achieved in professional domain",
        domain="professional"
    )
    
    # Verify integrity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Cross-domain integrity maintained in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for personal domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "status": "validated",
            "confidence": 0.93,
            "metrics": {
                "domain_compatibility": 0.90,
                "integration_coverage": 0.92,
                "cross_domain_integrity": 0.89
            }
        },
        "integration_metrics": {
            "current_efficiency": 0.86,
            "target_efficiency": 0.93,
            "optimization_potential": 0.91
        },
        "quality_assessment": {
            "overall_score": 0.90,
            "strengths": ["personal_context_awareness", "informal_integration"],
            "areas_for_improvement": ["formality_balance"]
        },
        "impact_analysis": {
            "scope": "domain_specific",
            "duration": "medium_term",
            "confidence": 0.92,
            "metrics": {
                "effectiveness": 0.90,
                "sustainability": 0.87,
                "scalability": 0.89
            }
        }
    })
    
    # Test personal domain
    pers_result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify personal domain reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain-specific integration completed in personal domain",
        domain="personal"
    )
    
    # Verify context reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Personal context awareness confirmed in personal domain",
        domain="personal"
    )
    
    # Verify style reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Informal integration style adapted in personal domain",
        domain="personal"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Formality balance enhancement identified in personal domain",
        domain="personal"
    )
    
    # Verify effectiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good integration effectiveness maintained in personal domain",
        domain="personal"
    )

@pytest.mark.asyncio
async def test_error_handling(integration_agent, mock_memory_system):
    """Test error handling during integration."""
    content = {
        "text": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "error_handling_requirements": {
                "recovery_priority": "high",
                "fallback_enabled": True,
                "logging_level": "detailed"
            }
        }
    }
    
    # Configure mock LLM response with detailed error analysis
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "error_analysis": {
            "type": "integration_failure",
            "severity": "high",
            "confidence": 0.95,
            "metrics": {
                "impact_severity": 0.92,
                "recovery_potential": 0.85,
                "system_stability": 0.88
            }
        },
        "failure_context": {
            "error_type": "content_processing",
            "affected_components": ["integrator", "analyzer"],
            "state_integrity": "maintained",
            "metrics": {
                "component_health": 0.90,
                "data_integrity": 0.95,
                "system_responsiveness": 0.87
            }
        },
        "recovery_assessment": {
            "automated_recovery": "possible",
            "required_actions": ["reset_integrator", "validate_state"],
            "estimated_effort": "medium",
            "success_probability": 0.82,
            "metrics": {
                "recovery_time": 0.15,
                "resource_cost": 0.45,
                "stability_impact": 0.25
            }
        },
        "impact_analysis": {
            "scope": "localized",
            "duration": "temporary",
            "affected_operations": ["integration", "analysis"],
            "mitigation_potential": "high",
            "metrics": {
                "operational_impact": 0.75,
                "user_experience": 0.60,
                "data_quality": 0.85
            }
        }
    })
    
    # Make LLM raise an error for the actual operation
    mock_memory_system.llm.analyze.side_effect = Exception("Test error")
    
    result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis"
    )
    
    # Verify error handling
    assert isinstance(result, IntegrationResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Integration failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify severity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity integration error detected in professional domain",
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
    
    # Verify component reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Affected components identified in professional domain",
        domain="professional"
    )
    
    # Verify mitigation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High mitigation potential confirmed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_reflection_recording(integration_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {"text": "test"}
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.9,
                    "description": "Main content"
                }
            }
        },
        "insights": [
            {
                "type": "connection",
                "description": "Strong connection found",
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": 0.9
            }
        ],
        "issues": []
    })
    
    result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis"
    )
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence integration completed in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.5,
                    "description": "Main content"
                }
            }
        },
        "insights": [
            {
                "type": "connection",
                "description": "Weak connection found",
                "confidence": 0.2,
                "domain_relevance": 0.5,
                "importance": 0.3
            }
        ],
        "issues": [
            {
                "type": "weak_connection",
                "severity": "medium",
                "description": "Connection needs strengthening"
            }
        ]
    })
    
    result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis"
    )
    
    # Verify low confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Low confidence integration in professional domain - needs improvement",
        domain="professional"
    )
    
    # Verify connection reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Weak connections identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_critical_issue_reflection(integration_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {"text": "test"}
    
    # Configure mock LLM response with critical issue
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.9,
                    "description": "Main content with critical issue"
                }
            }
        },
        "insights": [
            {
                "type": "critical_insight",
                "description": "Critical connection issue",
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "importance": 0.9
            }
        ],
        "issues": [
            {
                "type": "critical_issue",
                "severity": "high",
                "description": "Critical integration problem",
                "domain_impact": 0.9
            }
        ]
    })
    
    result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis"
    )
    
    # Verify critical issue reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Critical integration issues detected in professional domain",
        domain="professional"
    )
    
    # Verify severity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity integration issue requires immediate attention in professional domain",
        domain="professional"
    )
    
    # Verify domain impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Integration issue has significant domain impact in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_important_insight_reflection(integration_agent, mock_memory_system):
    """Test reflection recording for important insights."""
    content = {"text": "test"}
    
    # Configure mock LLM response with important insight
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "integration": {
            "type": "synthesis",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.9,
                    "description": "Main content with important insight"
                }
            }
        },
        "insights": [
            {
                "type": "important_insight",
                "confidence": 0.9,
                "importance": 0.9,
                "description": "Critical insight",
                "domain_relevance": 0.9,
                "implications": [
                    "Major impact on integration",
                    "Requires immediate attention"
                ]
            }
        ],
        "issues": []
    })
    
    result = await integration_agent.integrate_and_store(
        content,
        integration_type="synthesis"
    )
    
    # Verify important insight reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Important connections discovered in professional domain",
        domain="professional"
    )
    
    # Verify importance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High importance insight requires attention in professional domain",
        domain="professional"
    )
    
    # Verify domain relevance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Insight has significant domain relevance in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(integration_agent, mock_memory_system):
    """Test emotion updates based on integration results."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "emotional_context": {
                "intensity": "moderate",
                "valence": "positive",
                "arousal": "medium"
            }
        }
    }
    
    # Configure mock LLM response with detailed emotional states
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "emotions": {
            "integration_state": "confident",
            "domain_state": "aligned",
            "processing_state": "satisfied",
            "quality_state": "positive"
        },
        "emotional_metrics": {
            "confidence": 0.95,
            "satisfaction": 0.92,
            "engagement": 0.94,
            "stability": 0.91
        },
        "emotional_analysis": {
            "primary_state": "optimal",
            "contributing_factors": [
                "high_integration_quality",
                "strong_domain_alignment"
            ],
            "stability_indicators": {
                "trend": "improving",
                "volatility": "low",
                "sustainability": "high"
            }
        },
        "impact_assessment": {
            "emotional_depth": 0.93,
            "response_appropriateness": 0.92,
            "adaptation_quality": 0.94,
            "balance_metrics": {
                "cognitive_emotional": 0.91,
                "intensity_control": 0.93,
                "response_calibration": 0.92
            }
        }
    })
    
    await integration_agent.process(content)
    
    # Verify emotion updates
    assert "integration_state" in integration_agent.emotions
    assert "domain_state" in integration_agent.emotions
    assert integration_agent.emotions["integration_state"] == "confident"
    assert integration_agent.emotions["domain_state"] == "aligned"
    
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
        "Strong emotional stability confirmed in professional domain",
        domain="professional"
    )
    
    # Verify trend reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Positive emotional trend identified in professional domain",
        domain="professional"
    )
    
    # Verify depth reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High emotional depth demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify balance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good cognitive-emotional balance maintained in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_desire_updates(integration_agent, mock_memory_system):
    """Test desire updates based on integration needs."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "motivation_context": {
                "priority": "high",
                "urgency": "medium",
                "sustainability": "long_term"
            }
        }
    }
    
    # Configure mock LLM response with detailed desire states
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "desires": [
            {
                "type": "integration_requirement",
                "description": "Enhance integration quality",
                "priority": 0.9,
                "urgency": "high",
                "metrics": {
                    "importance": 0.92,
                    "feasibility": 0.88,
                    "impact": 0.94
                }
            },
            {
                "type": "quality_drive",
                "description": "Maintain high standards",
                "priority": 0.85,
                "sustainability": "long_term",
                "metrics": {
                    "commitment": 0.91,
                    "achievability": 0.89,
                    "value": 0.93
                }
            }
        ],
        "desire_metrics": {
            "motivation": 0.92,
            "focus": 0.88,
            "commitment": 0.95,
            "drive_strength": 0.91
        },
        "desire_analysis": {
            "primary_focus": "quality_enhancement",
            "driving_factors": [
                "integration_excellence",
                "standard_maintenance"
            ],
            "priority_indicators": {
                "importance": "high",
                "urgency": "medium",
                "sustainability": "strong"
            }
        },
        "impact_assessment": {
            "motivation_quality": 0.93,
            "goal_alignment": 0.92,
            "drive_sustainability": 0.94,
            "balance_metrics": {
                "short_long_term": 0.91,
                "effort_impact": 0.93,
                "priority_distribution": 0.92
            }
        }
    })
    
    await integration_agent.process(content)
    
    # Verify desire updates
    assert any("Enhance" in desire for desire in integration_agent.desires)
    assert any("Maintain" in desire for desire in integration_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong integration motivation established in professional domain",
        domain="professional"
    )
    
    # Verify focus reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear quality enhancement focus maintained in professional domain",
        domain="professional"
    )
    
    # Verify commitment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High standard maintenance commitment demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify priority reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Balanced priority distribution achieved in professional domain",
        domain="professional"
    )
    
    # Verify sustainability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong drive sustainability confirmed in professional domain",
        domain="professional"
    )
    
    # Verify alignment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High goal alignment maintained in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
