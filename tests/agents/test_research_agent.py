"""Tests for the specialized ResearchAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.research_agent import ResearchAgent
from src.nia.nova.core.research import ResearchResult

@pytest.fixture
def research_agent(mock_memory_system, mock_world, base_agent_config, request):
    """Create a ResearchAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestResearch_{request.node.name}"
    
    # Update mock memory system for research agent
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "findings": [
            {
                "statement": "Key finding",
                "type": "finding",
                "description": "positive",
                "confidence": 0.8,
                "domain_relevance": 0.9,
                "novelty": 0.9
            },
            {
                "statement": "Need more data",
                "type": "research_need",
                "description": "requires attention",
                "confidence": 0.7
            }
        ],
        "sources": {
            "similar_memories": [
                {
                    "content": "Related finding",
                    "similarity": 0.85,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "references": ["ref1"]
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
    
    return ResearchAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain=config["domain"]
    )

@pytest.mark.asyncio
async def test_initialization(research_agent, mock_memory_system):
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
                "value": "Advanced Research Specialist",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Conduct thorough research",
                "secondary": ["Maintain research quality", "Drive research innovation"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_research": "focused",
                "towards_discovery": "curious",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "research_analysis",
                "supporting": ["pattern_discovery", "insight_generation"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "research_rules": {"status": "ready", "confidence": 0.95},
                "quality_metrics": {"status": "ready", "confidence": 0.94},
                "domain_standards": {"status": "ready", "confidence": 0.93}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestResearch" in research_agent.name
    assert research_agent.domain == "professional"
    assert research_agent.agent_type == "research"
    
    # Verify attributes were initialized
    attributes = research_agent.get_attributes()
    assert "occupation" in attributes
    assert "desires" in attributes
    assert "emotions" in attributes
    assert "capabilities" in attributes
    assert attributes["domain"] == "professional"
    
    # Verify research-specific attributes
    assert "Conduct thorough research" in attributes["desires"]
    assert "towards_research" in attributes["emotions"]
    assert "research_analysis" in attributes["capabilities"]
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_content(research_agent, mock_memory_system):
    """Test content processing with domain awareness."""
    content = {
        "text": "Test content",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "research_context": "exploratory"
        }
    }
    metadata = {
        "source": "test",
        "confidence": 0.9,
        "research_metrics": {
            "completeness": 0.92,
            "consistency": 0.88,
            "relevance": 0.95
        }
    }
    
    # Configure mock LLM response with detailed processing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "type": "research_state",
                "state": "active",
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
        "research_progress": {
            "stage": "initial_analysis",
            "completion": 0.45,
            "quality_indicators": {
                "methodology": "sound",
                "data_quality": "high",
                "analysis_depth": "thorough"
            }
        },
        "domain_analysis": {
            "relevance": 0.95,
            "alignment": 0.92,
            "potential_impact": 0.88
        }
    })
    
    response = await research_agent.process(content, metadata)
    
    # Verify domain was added to metadata
    assert "domain" in metadata
    assert metadata["domain"] == "professional"
    
    # Verify TinyTroupe state updates
    assert "analysis_state" in research_agent.emotions
    assert "domain_state" in research_agent.emotions
    assert any("Investigate" in desire for desire in research_agent.desires)
    
    # Verify research state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Active research state established in professional domain",
        domain="professional"
    )
    
    # Verify domain alignment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong domain alignment confirmed in professional domain",
        domain="professional"
    )
    
    # Verify methodology reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Sound research methodology identified in professional domain",
        domain="professional"
    )
    
    # Verify progress reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research progress tracking initiated in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant research impact potential noted in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_and_store(research_agent, mock_memory_system):
    """Test research analysis with domain awareness."""
    content = {
        "content": "Research content to analyze",
        "type": "research",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "medium"
        }
    }
    
    # Configure mock LLM response with detailed research results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "findings": [{
            "statement": "Key research finding",
            "type": "finding",
            "confidence": 0.9,
            "domain_relevance": 0.95,
            "novelty": 0.88,
            "metrics": {
                "accuracy": 0.92,
                "precision": 0.94,
                "coverage": 0.88
            }
        }],
        "sources": {
            "similar_memories": [{
                "content": "Related research",
                "similarity": 0.85,
                "timestamp": "2024-01-01T00:00:00Z"
            }],
            "references": ["ref1", "ref2"],
            "research_metrics": {
                "completeness": 0.91,
                "consistency": 0.89,
                "reliability": 0.94
            }
        },
        "research_quality": {
            "score": 0.93,
            "confidence": 0.9,
            "validation_metrics": {
                "methodology": 0.92,
                "data_quality": 0.89,
                "analysis_depth": 0.94
            }
        }
    })
    
    result = await research_agent.analyze_and_store(
        content,
        target_domain="professional"
    )
    
    # Verify result structure
    assert isinstance(result, ResearchResult)
    assert len(result.findings) > 0
    assert result.confidence > 0
    assert result.sources is not None
    
    # Verify memory storage
    assert hasattr(research_agent, "store_memory")
    
    # Verify success reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence research completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research quality exceeds threshold in professional domain",
        domain="professional"
    )
    
    # Verify methodology reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong research methodology demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify depth reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Deep research analysis achieved in professional domain",
        domain="professional"
    )
    
    # Verify reliability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High research reliability confirmed in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_access_validation(research_agent, mock_memory_system):
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
        "research_context": {
            "domain_relevance": 0.95,
            "research_alignment": 0.92,
            "scope_coverage": 0.94
        }
    })
    
    # Test allowed domain with detailed content
    content = {
        "type": "research",
        "metadata": {
            "importance": "high",
            "security_level": "standard",
            "validation_requirements": "strict"
        }
    }
    
    await research_agent.validate_domain_access("professional")
    
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
    
    # Verify research context reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research context validated in professional domain",
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
        },
        "research_impact": {
            "severity": "high",
            "scope": "significant",
            "mitigation_required": true
        }
    })
    
    # Test denied domain
    mock_memory_system.semantic.store.get_domain_access.return_value = False
    with pytest.raises(PermissionError):
        await research_agent.validate_domain_access("restricted")
    
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
    
    # Verify research impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research impact assessment triggered by access violation",
        domain="professional"
    )
    
    # Verify mitigation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research access mitigation procedures activated",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_analyze_with_different_domains(research_agent, mock_memory_system):
    """Test analysis with different domain configurations."""
    content = {
        "content": "test",
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
                "research_fit": 0.93,
                "analysis_quality": 0.91
            }
        },
        "research_metrics": {
            "accuracy": 0.92,
            "completeness": 0.94,
            "reliability": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.93,
            "strengths": ["domain_specific_research", "methodology_rigor"],
            "areas_for_improvement": ["cross_domain_synthesis"]
        }
    })
    
    # Test professional domain
    prof_result = await research_agent.analyze_and_store(
        content,
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
        "High research quality confirmed in professional domain",
        domain="professional"
    )
    
    # Verify methodology reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Rigorous research methodology demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Cross domain synthesis enhancement identified in professional domain",
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
                "research_fit": 0.91,
                "analysis_quality": 0.89
            }
        },
        "research_metrics": {
            "accuracy": 0.90,
            "completeness": 0.92,
            "reliability": 0.91
        },
        "quality_assessment": {
            "overall_score": 0.91,
            "strengths": ["personal_context_awareness", "informal_research"],
            "areas_for_improvement": ["formality_calibration"]
        }
    })
    
    # Test personal domain
    pers_result = await research_agent.analyze_and_store(
        content,
        target_domain="personal"
    )
    assert pers_result.metadata["domain"] == "personal"
    
    # Verify personal domain reflections
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Domain context awareness confirmed in personal domain",
        domain="personal"
    )
    
    # Verify research style reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Informal research style adapted in personal domain",
        domain="personal"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Good research quality maintained in personal domain",
        domain="personal"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Formality calibration enhancement identified in personal domain",
        domain="personal"
    )

@pytest.mark.asyncio
async def test_error_handling(research_agent, mock_memory_system):
    """Test error handling during analysis."""
    content = {"content": "test"}
    
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify error handling
    assert isinstance(result, ResearchResult)
    assert result.confidence == 0.0
    assert len(result.findings) == 0
    assert "error" in result.metadata
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research analysis failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research analysis needs retry with adjusted parameters in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_reflection_recording(research_agent, mock_memory_system):
    """Test reflection recording with domain awareness."""
    content = {
        "content": "test",
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "research_requirements": "comprehensive"
        }
    }
    
    # Configure mock LLM response for high confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "findings": [{
            "statement": "Key finding",
            "type": "finding",
            "confidence": 0.9,
            "domain_relevance": 0.9,
            "novelty": 0.8,
            "metrics": {
                "accuracy": 0.92,
                "precision": 0.94,
                "reliability": 0.91
            },
            "quality_indicators": {
                "methodology": "robust",
                "data_quality": "high",
                "analysis_depth": "thorough"
            }
        }],
        "sources": {
            "similar_memories": [],
            "references": [],
            "research_metrics": {
                "completeness": 0.93,
                "consistency": 0.92,
                "validation": 0.94
            }
        },
        "research_quality": {
            "overall_score": 0.92,
            "confidence_metrics": {
                "data_confidence": 0.93,
                "method_confidence": 0.91,
                "result_confidence": 0.92
            }
        }
    })
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify high confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence research completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong research quality demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify methodology reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Robust research methodology confirmed in professional domain",
        domain="professional"
    )
    
    # Verify data quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High data quality maintained in professional domain",
        domain="professional"
    )
    
    # Configure mock LLM response for low confidence case
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "findings": [{
            "statement": "Uncertain finding",
            "type": "finding",
            "confidence": 0.2,
            "domain_relevance": 0.5,
            "novelty": 0.3,
            "metrics": {
                "accuracy": 0.45,
                "precision": 0.48,
                "reliability": 0.42
            },
            "quality_indicators": {
                "methodology": "weak",
                "data_quality": "low",
                "analysis_depth": "shallow"
            }
        }],
        "sources": {
            "similar_memories": [],
            "references": [],
            "research_metrics": {
                "completeness": 0.45,
                "consistency": 0.48,
                "validation": 0.42
            }
        },
        "research_quality": {
            "overall_score": 0.44,
            "confidence_metrics": {
                "data_confidence": 0.45,
                "method_confidence": 0.42,
                "result_confidence": 0.43
            },
            "improvement_needs": {
                "primary_areas": [
                    "methodology_refinement",
                    "data_quality_enhancement",
                    "validation_strengthening"
                ],
                "priority": "high"
            }
        }
    })
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify low confidence reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Low confidence research results in professional domain",
        domain="professional"
    )
    
    # Verify methodology concern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Research methodology needs improvement in professional domain",
        domain="professional"
    )
    
    # Verify data quality concern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Data quality enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify validation concern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Validation process requires strengthening in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_emotion_updates(research_agent, mock_memory_system):
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
            "research_state": "confident",
            "domain_state": "aligned",
            "discovery_state": "excited",
            "quality_state": "positive"
        },
        "emotional_metrics": {
            "confidence": 0.95,
            "satisfaction": 0.92,
            "enthusiasm": 0.94,
            "curiosity": 0.96
        },
        "emotional_analysis": {
            "primary_state": "optimal",
            "contributing_factors": [
                "promising_findings",
                "strong_domain_alignment"
            ],
            "engagement_indicators": {
                "trend": "increasing",
                "depth": "high",
                "sustainability": "strong"
            }
        }
    })
    
    await research_agent.process(content)
    
    # Verify emotion updates
    assert research_agent.emotions["analysis_state"] == "positive"
    assert research_agent.emotions["domain_state"] == "highly_relevant"
    
    # Verify emotional state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Confident research state achieved in professional domain",
        domain="professional"
    )
    
    # Verify enthusiasm reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High research enthusiasm maintained in professional domain",
        domain="professional"
    )
    
    # Verify engagement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Deep research engagement confirmed in professional domain",
        domain="professional"
    )
    
    # Verify curiosity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong research curiosity demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_desire_updates(research_agent, mock_memory_system):
    """Test desire updates based on research needs."""
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
                "type": "research_requirement",
                "description": "Investigate research patterns",
                "priority": 0.9,
                "urgency": "high",
                "domain_relevance": 0.95
            },
            {
                "type": "discovery_drive",
                "description": "Explore novel findings",
                "priority": 0.85,
                "impact": "significant",
                "potential": "high"
            }
        ],
        "desire_metrics": {
            "motivation": 0.92,
            "focus": 0.88,
            "commitment": 0.95,
            "curiosity": 0.94
        },
        "desire_analysis": {
            "primary_focus": "knowledge_expansion",
            "driving_factors": [
                "discovery_potential",
                "domain_advancement"
            ],
            "priority_indicators": {
                "importance": "high",
                "urgency": "immediate",
                "sustainability": "strong"
            }
        }
    })
    
    await research_agent.process(content)
    
    # Verify desire updates
    assert any("Investigate" in desire for desire in research_agent.desires)
    
    # Verify motivation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong research motivation established in professional domain",
        domain="professional"
    )
    
    # Verify focus reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Clear research focus maintained in professional domain",
        domain="professional"
    )
    
    # Verify discovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High discovery potential identified in professional domain",
        domain="professional"
    )
    
    # Verify commitment reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong research commitment demonstrated in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_novelty_reflection(research_agent, mock_memory_system):
    """Test reflection recording for novel findings."""
    content = {"content": "test"}
    
    # Configure mock LLM response with novel findings
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "findings": [
            {
                "statement": "Novel finding",
                "type": "finding",
                "confidence": 0.9,
                "domain_relevance": 0.9,
                "novelty": 0.95,
                "implications": [
                    "Major research impact",
                    "New research direction needed"
                ]
            }
        ],
        "sources": {
            "similar_memories": [],
            "references": [],
            "novelty_metrics": {
                "uniqueness": 0.95,
                "originality": 0.9,
                "potential_impact": 0.9
            }
        }
    })
    
    result = await research_agent.analyze_and_store(content)
    
    # Verify novelty reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Novel research findings discovered in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High impact research findings require attention in professional domain",
        domain="professional"
    )
    
    # Verify uniqueness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Highly unique research findings identified in professional domain",
        domain="professional"
    )
    
    # Verify direction reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "New research direction emerging in professional domain",
        domain="professional"
    )

if __name__ == "__main__":
    pytest.main([__file__])
