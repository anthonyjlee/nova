"""Tests for the specialized SchemaAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from pydantic import BaseModel

from src.nia.agents.specialized.schema_agent import SchemaAgent
from src.nia.nova.core.schema import SchemaResult

@pytest.fixture
def schema_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a SchemaAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestSchema_{request.node.name}"
    
    # Update mock memory system for schema agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True,
                    "description": "User's name"
                },
                "age": {
                    "type": "integer",
                    "default": 0
                }
            }
        },
        "validations": [
            {
                "rule": "has_fields",
                "passed": True,
                "confidence": 0.8,
                "description": "positive",
                "domain_relevance": 0.9,
                "severity": "low"
            },
            {
                "rule": "schema_need",
                "passed": False,
                "confidence": 0.7,
                "description": "requires attention"
            }
        ],
        "issues": [
            {
                "type": "missing_validation",
                "severity": "medium",
                "description": "Missing validation",
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
    
    return SchemaAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(schema_agent, mock_memory_system):
    """Test agent initialization with enhanced attributes."""
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
                "value": "Advanced Schema Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Maintain schema integrity",
                "secondary": ["Optimize schema validation", "Ensure data quality"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_schema": "analytical",
                "towards_validation": "focused",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "schema_analysis",
                "supporting": ["validation_optimization", "model_generation"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "schema_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestSchema" in schema_agent.name
    assert schema_agent.domain == "professional"
    assert schema_agent.agent_type == "schema"
    
    # Verify attributes were initialized
    attributes = schema_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify schema-specific attributes
    assert "Maintain schema integrity" in attributes["desires"]
    assert "towards_schema" in attributes["emotions"]
    assert "schema_analysis" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(schema_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "schema_requirements": "comprehensive"
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
                "schema_structure",
                "processing_efficiency"
            ],
            "areas_for_improvement": [
                "validation_coverage"
            ]
        }
    })
    
    response = await schema_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "schema_state" in schema_agent.emotions
    assert "domain_state" in schema_agent.emotions
    assert any("Improve" in desire for desire in schema_agent.desires)
    
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
        "Good schema structure maintained in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High processing efficiency demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation coverage enhancement identified in professional domain",
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
        "Good schema coherence demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_and_store(schema_agent, mock_memory_system):
    """Test schema analysis with domain awareness."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": False}
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "analysis_requirements": {
                "validation_depth": "comprehensive",
                "quality_threshold": 0.9,
                "performance_target": "optimal"
            }
        }
    }
    
    # Configure mock LLM response with detailed analysis results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "analysis_state": {
            "status": "completed",
            "confidence": 0.95,
            "quality_metrics": {
                "accuracy": 0.93,
                "completeness": 0.91,
                "reliability": 0.94
            }
        },
        "schema_analysis": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True,
                    "validation": {
                        "quality": 0.95,
                        "coverage": 0.92,
                        "consistency": 0.94
                    }
                },
                "age": {
                    "type": "integer",
                    "required": False,
                    "validation": {
                        "quality": 0.93,
                        "coverage": 0.90,
                        "consistency": 0.92
                    }
                }
            },
            "metrics": {
                "field_quality": 0.94,
                "structure_integrity": 0.92,
                "validation_coverage": 0.93
            }
        },
        "validation_metrics": {
            "execution_time": 0.15,
            "resource_usage": 0.45,
            "optimization_level": 0.92
        },
        "quality_assessment": {
            "overall_score": 0.93,
            "strengths": [
                "field_validation",
                "schema_structure"
            ],
            "areas_for_improvement": [
                "constraint_coverage"
            ]
        }
    })
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, SchemaResult)
    assert result.schema["type"] == "data"
    assert len(result.schema["fields"]) == 2
    assert result.confidence > 0
    assert len(result.issues) > 0
    
    # Verify memory storage
    assert hasattr(schema_agent, "store_memory")
    
    # Verify analysis completion reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality schema analysis completed in professional domain",
        domain="professional"
    )
    
    # Verify field validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong field validation achieved in professional domain",
        domain="professional"
    )
    
    # Verify structure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good schema structure maintained in professional domain",
        domain="professional"
    )
    
    # Verify coverage reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High validation coverage confirmed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong quality metrics achieved in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Constraint coverage enhancement identified in professional domain",
        domain="professional"
    )
    
    # Verify performance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Optimal validation performance maintained in professional domain",
        domain="professional"
    )
    
    # Verify consistency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High schema consistency demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(schema_agent, mock_memory_system):
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
    
    # Test allowed domain
    await schema_agent.validate_domain_access("professional")
    
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
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await schema_agent.validate_domain_access("restricted")
    
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

@pytest.mark.asyncio
async def test_analyze_with_different_domains(schema_agent, mock_memory_system):
    """Test schema analysis with different domain configurations."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "cross_domain": True,
            "analysis_requirements": {
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
                "analysis_coverage": 0.94,
                "cross_domain_integrity": 0.91
            }
        },
        "analysis_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["domain_adaptability", "analysis_consistency"],
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
    prof_result = await schema_agent.analyze_and_store(
        content,
        schema_type="data",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Verify domain validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Multi-domain analysis completed successfully in professional domain",
        domain="professional"
    )
    
    # Verify compatibility reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain compatibility demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify coverage reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High analysis coverage achieved in professional domain",
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
                "analysis_coverage": 0.92,
                "cross_domain_integrity": 0.89
            }
        },
        "analysis_metrics": {
            "current_efficiency": 0.86,
            "target_efficiency": 0.93,
            "optimization_potential": 0.91
        },
        "quality_assessment": {
            "overall_score": 0.90,
            "strengths": ["personal_context_awareness", "informal_analysis"],
            "areas_for_improvement": ["formality_calibration"]
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
    pers_result = await schema_agent.analyze_and_store(
        content,
        schema_type="data",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify personal domain reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain-specific analysis completed in personal domain",
        domain="personal"
    )
    
    # Verify context reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Personal context awareness confirmed in personal domain",
        domain="personal"
    )
    
    # Verify style reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Informal analysis style adapted in personal domain",
        domain="personal"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Formality calibration enhancement identified in personal domain",
        domain="personal"
    )
    
    # Verify effectiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good analysis effectiveness maintained in personal domain",
        domain="personal"
    )

@pytest.mark.asyncio
async def test_error_handling(schema_agent, mock_memory_system):
    """Test error handling during schema analysis."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        }
    }
    
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify error handling
    assert isinstance(result, SchemaResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.validations) == 0
    assert len(result.issues) == 1
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema analysis failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema validation needs retry with adjusted parameters in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_reflection_recording(schema_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        }
    }
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True
                }
            }
        },
        "validations": [
            {
                "rule": "test_rule",
                "passed": True,
                "confidence": 0.9
            }
        ],
        "issues": []
    })
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence schema validation completed in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True
                }
            }
        },
        "validations": [
            {
                "rule": "test_rule",
                "passed": False,
                "confidence": 0.5
            }
        ],
        "issues": [
            {
                "type": "validation_failed",
                "severity": "medium",
                "description": "Schema validation failed"
            }
        ]
    })
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify failure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema validation failed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_critical_issue_reflection(schema_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {
        "fields": {
            "name": {"type": "string", "required": True}
        }
    }
    
    # Configure mock LLM response with critical issue
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True
                }
            }
        },
        "validations": [
            {
                "rule": "field_type",
                "passed": False,
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "severity": "high"
            }
        ],
        "issues": [
            {
                "type": "critical_issue",
                "severity": "high",
                "description": "Critical schema problem",
                "domain_impact": 0.9,
                "implications": [
                    "Data integrity at risk",
                    "Validation failures likely"
                ]
            }
        ]
    })
    
    result = await schema_agent.analyze_and_store(
        content,
        schema_type="data"
    )
    
    # Verify critical issue reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Critical schema issues detected in professional domain",
        domain="professional"
    )
    
    # Verify severity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity schema issue requires immediate attention in professional domain",
        domain="professional"
    )
    
    # Verify domain impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema issue has significant domain impact in professional domain",
        domain="professional"
    )
    
    # Verify implications reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema validation failures expected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_generate_model(schema_agent, mock_memory_system):
    """Test Pydantic model generation with domain awareness."""
    content = {
        "fields": {
            "name": {
                "type": "string",
                "required": True
            },
            "age": {
                "type": "integer",
                "default": 0
            }
        }
    }
    
    # Configure mock LLM response for valid schema
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "string",
                    "required": True
                },
                "age": {
                    "type": "integer",
                    "default": 0
                }
            }
        },
        "validations": [
            {
                "rule": "test_rule",
                "passed": True,
                "confidence": 0.9
            }
        ],
        "issues": []
    })
    
    model = await schema_agent.generate_model(
        content,
        "TestModel",
        target_domain="professional"
    )
    
    # Verify model structure
    assert issubclass(model, BaseModel)
    assert "name" in model.__fields__
    assert "age" in model.__fields__
    assert model.__fields__["name"].required is True
    assert model.__fields__["age"].default == 0
    
    # Verify reflection was recorded
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Generated Pydantic model in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_generate_model_with_invalid_schema(schema_agent, mock_memory_system):
    """Test model generation with invalid schema."""
    content = {
        "fields": {
            "name": {"type": "invalid"}
        }
    }
    
    # Configure mock LLM response for invalid schema
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "schema": {
            "type": "data",
            "fields": {
                "name": {
                    "type": "invalid",
                    "required": True
                }
            }
        },
        "validations": [
            {
                "rule": "field_type",
                "passed": False,
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "severity": "high"
            }
        ],
        "issues": [
            {
                "type": "invalid_type",
                "severity": "high",
                "description": "Invalid field type",
                "domain_impact": 0.9,
                "implications": [
                    "Model generation will fail",
                    "Data validation impossible"
                ]
            }
        ]
    })
    
    with pytest.raises(ValueError):
        await schema_agent.generate_model(
            content,
            "TestModel",
            target_domain="professional"
        )
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema model generation failed in professional domain",
        domain="professional"
    )
    
    # Verify validation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Invalid field type prevents model generation in professional domain",
        domain="professional"
    )
    
    # Verify implications reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schema validation impossible due to invalid type in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(schema_agent, mock_memory_system):
    """Test emotion updates based on schema results."""
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
            "schema_state": "confident",
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
                "high_schema_quality",
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
    
    await schema_agent.process(content)
    
    # Verify emotion updates
    assert "schema_state" in schema_agent.emotions
    assert "domain_state" in schema_agent.emotions
    assert schema_agent.emotions["schema_state"] == "confident"
    assert schema_agent.emotions["domain_state"] == "aligned"
    
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
async def test_desire_updates(schema_agent, mock_memory_system):
    """Test desire updates based on schema needs."""
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
                "type": "schema_requirement",
                "description": "Enhance schema quality",
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
                "schema_excellence",
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
    
    await schema_agent.process(content)
    
    # Verify desire updates
    assert any("Enhance" in desire for desire in schema_agent.desires)
    assert any("Maintain" in desire for desire in schema_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong schema motivation established in professional domain",
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
