"""Tests for the specialized AnalysisAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.analysis_agent import AnalysisAgent
from src.nia.nova.core.analysis import AnalysisResult

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "analysis": {
            "type": "text",
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
                "type": "pattern",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "importance": 0.7
            },
            {
                "type": "analysis_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "issues": [
            {
                "type": "missing_pattern",
                "severity": "medium",
                "description": "Missing pattern",
                "domain_impact": 0.3
            }
        ]
    })
    
    # Mock semantic store
    memory.semantic = MagicMock()
    memory.semantic.store = MagicMock()
    memory.semantic.store.record_reflection = AsyncMock()
    memory.semantic.store.get_domain_access = AsyncMock(return_value=True)
    
    # Mock episodic store
    memory.episodic = MagicMock()
    memory.episodic.store = MagicMock()
    memory.episodic.store.search = AsyncMock(return_value=[
        {
            "content": {"content": "Similar analysis"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    return MagicMock()

@pytest.fixture
def analysis_agent(mock_memory_system, mock_world, request):
    """Create an AnalysisAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestAnalysis_{request.node.name}"
    return AnalysisAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(analysis_agent, mock_memory_system):
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
                "value": "Advanced Analysis Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Extract meaningful insights",
                "secondary": ["Maintain analysis quality", "Optimize analysis processes"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_content": "focused",
                "towards_analysis": "analytical",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "content_analysis",
                "supporting": ["pattern_recognition", "insight_generation"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "analysis_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestAnalysis" in analysis_agent.name
    assert analysis_agent.domain == "professional"
    assert analysis_agent.agent_type == "analysis"
    
    # Verify attributes were initialized
    attributes = analysis_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify analysis-specific attributes
    assert "Extract meaningful insights" in attributes["desires"]
    assert "towards_content" in attributes["emotions"]
    assert "content_analysis" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(analysis_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "processing_requirements": "comprehensive"
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
        "quality_assessment": {
            "overall_score": 0.93,
            "strengths": [
                "content_structure",
                "processing_efficiency"
            ],
            "areas_for_improvement": [
                "context_integration"
            ]
        }
    })
    
    response = await analysis_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in analysis_agent.emotions
    assert "domain_state" in analysis_agent.emotions
    assert any("Investigate" in desire for desire in analysis_agent.desires)
    
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
        "Context integration enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_and_store(analysis_agent, mock_memory_system):
    """Test content analysis with domain awareness."""
    content = {
        "text": "Content to analyze",
        "type": "text",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "analysis_requirements": "comprehensive"
        }
    }
    
    # Configure mock LLM response with detailed analysis results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "analysis": {
            "type": "text",
            "components": {
                "main": {
                    "type": "section",
                    "importance": 0.92,
                    "description": "Main content",
                    "metrics": {
                        "clarity": 0.93,
                        "structure": 0.91,
                        "completeness": 0.94
                    }
                }
            },
            "quality_metrics": {
                "accuracy": 0.93,
                "precision": 0.92,
                "coverage": 0.94
            }
        },
        "insights": [
            {
                "type": "pattern",
                "description": "Key pattern identified",
                "confidence": 0.91,
                "domain_relevance": 0.95,
                "importance": 0.89,
                "metrics": {
                    "novelty": 0.88,
                    "applicability": 0.92,
                    "reliability": 0.93
                }
            }
        ],
        "analysis_metrics": {
            "depth": 0.92,
            "breadth": 0.90,
            "efficiency": 0.93,
            "reliability": 0.94
        },
        "quality_assessment": {
            "overall_score": 0.93,
            "strengths": [
                "pattern_recognition",
                "insight_generation"
            ],
            "areas_for_improvement": [
                "context_integration"
            ]
        }
    })
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text",
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, AnalysisResult)
    assert result.analysis["type"] == "text"
    assert len(result.analysis["components"]) == 1
    assert len(result.insights) > 0
    assert result.confidence > 0.9
    
    # Verify memory storage
    assert hasattr(analysis_agent, "store_memory")
    
    # Verify analysis completion reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality analysis completed in professional domain",
        domain="professional"
    )
    
    # Verify pattern recognition reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong pattern recognition achieved in professional domain",
        domain="professional"
    )
    
    # Verify insight generation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Effective insight generation demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify quality metrics reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High analysis quality metrics maintained in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Context integration enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(analysis_agent, mock_memory_system):
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
    
    await analysis_agent.validate_domain_access("professional")
    
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
        await analysis_agent.validate_domain_access("restricted")
    
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
async def test_analyze_with_different_domains(analysis_agent, mock_memory_system):
    """Test analysis with different domain configurations."""
    content = {
        "text": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "domain_requirements": "cross_domain"
        }
    }
    
    # Configure mock LLM response for professional domain
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "domain_analysis": {
            "domain": "professional",
            "confidence": 0.95,
            "relevance": 0.94,
            "metrics": {
                "domain_alignment": 0.92,
                "content_fit": 0.93,
                "analysis_quality": 0.91
            }
        },
        "analysis_metrics": {
            "accuracy": 0.92,
            "completeness": 0.94,
            "reliability": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.93,
            "strengths": ["domain_specific_analysis", "content_structure"],
            "areas_for_improvement": ["cross_domain_integration"]
        }
    })
    
    # Test professional domain
    prof_result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text",
        target_domain="professional"
    )
    assert prof_result.metadata["domain"] == "professional"
    
    # Verify professional domain reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain alignment achieved in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High analysis quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong analysis accuracy demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Cross domain integration enhancement identified in professional domain",
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
                "analysis_quality": 0.89
            }
        },
        "analysis_metrics": {
            "accuracy": 0.90,
            "completeness": 0.92,
            "reliability": 0.91
        },
        "quality_assessment": {
            "overall_score": 0.91,
            "strengths": ["personal_context_awareness", "informal_analysis"],
            "areas_for_improvement": ["formality_calibration"]
        }
    })
    
    # Test personal domain
    pers_result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text",
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify personal domain reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain context awareness confirmed in personal domain",
        domain="personal"
    )
    
    # Verify analysis style reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Informal analysis style adapted in personal domain",
        domain="personal"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good analysis quality maintained in personal domain",
        domain="personal"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Formality calibration enhancement identified in personal domain",
        domain="personal"
    )

@pytest.mark.asyncio
async def test_error_handling(analysis_agent, mock_memory_system):
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
    error_message = "Test error during analysis"
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception(error_message))
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify error handling
    assert isinstance(result, AnalysisResult)
    assert result.is_valid is False
    assert result.confidence == 0.0
    assert len(result.insights) == 0
    assert len(result.issues) == 1
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
async def test_reflection_recording(analysis_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {
        "text": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "immediate"
        }
    }
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "insights": [{
            "type": "test_insight",
            "confidence": 0.9,
            "importance": 0.9,
            "domain_relevance": 0.95,
            "description": "Important pattern detected",
            "metrics": {
                "accuracy": 0.92,
                "precision": 0.94,
                "coverage": 0.88
            }
        }],
        "analysis": {
            "type": "text",
            "quality_score": 0.93,
            "analysis_metrics": {
                "completeness": 0.91,
                "consistency": 0.89,
                "reliability": 0.94
            }
        },
        "issues": []
    })
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence analysis completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Exceptional analysis quality achieved in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High analysis accuracy confirmed in professional domain",
        domain="professional"
    )
    
    # Verify reliability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong analysis reliability demonstrated in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case with detailed issues
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "insights": [{
            "type": "test_insight",
            "confidence": 0.5,
            "importance": 0.5,
            "domain_relevance": 0.4,
            "description": "Weak pattern detected",
            "metrics": {
                "accuracy": 0.45,
                "precision": 0.48,
                "coverage": 0.42
            }
        }],
        "analysis": {
            "type": "text",
            "quality_score": 0.45,
            "failure_analysis": {
                "primary_cause": "incomplete_analysis",
                "affected_areas": ["pattern_detection", "insight_generation"],
                "remediation_priority": "high"
            }
        },
        "issues": [{
            "type": "analysis_issue",
            "severity": "medium",
            "description": "Analysis quality concerns",
            "impact_areas": ["insight_quality", "domain_relevance"],
            "remediation_steps": ["review_analysis_methods", "adjust_thresholds"]
        }]
    })
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify failure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis failed in professional domain",
        domain="professional"
    )
    
    # Verify quality impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis quality below threshold in professional domain",
        domain="professional"
    )
    
    # Verify remediation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis requires immediate remediation in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis issues impact insight quality in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_critical_issue_reflection(analysis_agent, mock_memory_system):
    """Test reflection recording for critical issues."""
    content = {
        "text": "test",
        "metadata": {
            "importance": "critical",
            "impact": "severe",
            "urgency": "immediate"
        }
    }
    
    # Configure mock LLM response with critical issue
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "insights": [],
        "analysis": {
            "type": "text",
            "quality_score": 0.3,
            "critical_analysis": {
                "severity": "high",
                "impact_scope": "widespread",
                "urgency_level": "immediate",
                "affected_areas": [
                    "core_functionality",
                    "data_integrity"
                ]
            }
        },
        "issues": [{
            "type": "critical_issue",
            "severity": "high",
            "description": "Critical analysis problem",
            "domain_impact": 0.9,
            "implications": [
                "Analysis integrity compromised",
                "Immediate intervention required"
            ],
            "risk_assessment": {
                "likelihood": "high",
                "impact": "severe",
                "mitigation_priority": "urgent"
            }
        }]
    })
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify critical issue reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Critical analysis issues detected in professional domain",
        domain="professional"
    )
    
    # Verify severity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High severity analysis issue requires immediate attention in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis issue has severe domain impact in professional domain",
        domain="professional"
    )
    
    # Verify integrity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Analysis integrity requires immediate intervention in professional domain",
        domain="professional"
    )
    
    # Verify risk reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High risk analysis situation identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_important_insight_reflection(analysis_agent, mock_memory_system):
    """Test reflection recording for important insights."""
    content = {
        "text": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "domain_relevance": "critical"
        }
    }
    
    # Configure mock LLM response with important insight
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "insights": [{
            "type": "important_insight",
            "confidence": 0.95,
            "importance": 0.9,
            "domain_relevance": 0.95,
            "description": "Critical insight discovered",
            "metrics": {
                "novelty": 0.92,
                "impact": 0.94,
                "applicability": 0.88
            },
            "implications": [
                "Significant process improvement",
                "Enhanced efficiency potential"
            ],
            "value_assessment": {
                "business_value": "high",
                "implementation_feasibility": "medium",
                "roi_potential": "significant"
            }
        }],
        "analysis": {
            "type": "text",
            "quality_score": 0.93,
            "insight_metrics": {
                "depth": 0.91,
                "breadth": 0.89,
                "actionability": 0.94
            }
        },
        "issues": []
    })
    
    result = await analysis_agent.analyze_and_store(
        content,
        analysis_type="text"
    )
    
    # Verify insight discovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Important insights discovered in professional domain",
        domain="professional"
    )
    
    # Verify confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence insights generated in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant insight impact identified in professional domain",
        domain="professional"
    )
    
    # Verify value reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High business value insights confirmed in professional domain",
        domain="professional"
    )
    
    # Verify actionability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong insight actionability demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(analysis_agent, mock_memory_system):
    """Test emotion updates based on analysis results."""
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
            "analysis_state": "confident",
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
                "high_analysis_quality",
                "strong_domain_alignment"
            ],
            "stability_indicators": {
                "trend": "improving",
                "volatility": "low"
            }
        }
    })
    
    await analysis_agent.process(content)
    
    # Verify emotion updates
    assert "analysis_state" in analysis_agent.emotions
    assert "domain_state" in analysis_agent.emotions
    
    # Verify emotional state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Confident analysis state achieved in professional domain",
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
async def test_desire_updates(analysis_agent, mock_memory_system):
    """Test desire updates based on analysis needs."""
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
                "type": "analysis_requirement",
                "description": "Investigate analysis patterns",
                "priority": 0.9,
                "urgency": "high"
            },
            {
                "type": "quality_improvement",
                "description": "Enhance analysis precision",
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
            "primary_focus": "analysis_quality",
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
    
    await analysis_agent.process(content)
    
    # Verify desire updates
    assert any("Investigate" in desire for desire in analysis_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong analysis motivation established in professional domain",
        domain="professional"
    )
    
    # Verify focus reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear analysis focus maintained in professional domain",
        domain="professional"
    )
    
    # Verify priority reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High priority analysis desires identified in professional domain",
        domain="professional"
    )
    
    # Verify commitment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong analysis commitment demonstrated in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
