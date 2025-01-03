"""Tests for the enhanced ExecutionAgent implementation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.nia.agents.specialized.execution_agent import ExecutionAgent
from src.nia.nova.core.execution import ExecutionResult
from src.nia.memory.memory_types import AgentResponse

@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    memory = MagicMock()
    # Mock LLM
    memory.llm = MagicMock()
    memory.llm.analyze = AsyncMock(return_value={
        "execution": {
            "type": "sequential",
            "steps": {
                "step1": {
                    "type": "task",
                    "priority": 0.8,
                    "actions": ["action1"]
                }
            },
            "actions": {
                "action1": {
                    "type": "process",
                    "parameters": {"value": 10}
                }
            }
        },
        "actions": [
            {
                "type": "step_execution",
                "description": "Execute step1",
                "confidence": 0.8,
                "importance": 0.9
            }
        ],
        "issues": []
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
            "content": {"content": "Previous execution"},
            "similarity": 0.9,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ])
    
    return memory

@pytest.fixture
def mock_world():
    """Create a mock world environment."""
    world = MagicMock()
    world.notify_agent = AsyncMock()
    return world

@pytest.fixture
def execution_agent(mock_memory_system, mock_world, request):
    """Create an ExecutionAgent instance with mock dependencies."""
    # Use test name to create unique agent name
    agent_name = f"TestExecution_{request.node.name}"
    return ExecutionAgent(
        name=agent_name,
        memory_system=mock_memory_system,
        world=mock_world,
        domain="professional"
    )

@pytest.mark.asyncio
async def test_initialization(execution_agent, mock_memory_system):
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
                "value": "Advanced Action Executor",
                "confidence": 0.95,
                "domain_relevance": 0.94
            },
            "desires": {
                "primary": "Optimize resource usage",
                "secondary": ["Maintain execution quality", "Ensure reliability"],
                "confidence": 0.93
            },
            "emotions": {
                "towards_sequences": "focused",
                "towards_resources": "efficient",
                "confidence": 0.92
            },
            "capabilities": {
                "primary": "error_recovery",
                "supporting": ["resource_optimization", "sequence_management"],
                "confidence": 0.94
            }
        },
        "state_validation": {
            "tracking_systems": {
                "active_sequences": {"status": "ready", "confidence": 0.95},
                "execution_patterns": {"status": "ready", "confidence": 0.94},
                "resource_usage": {"status": "ready", "confidence": 0.93},
                "error_recovery": {"status": "ready", "confidence": 0.92},
                "retry_states": {"status": "ready", "confidence": 0.91},
                "schedule_queue": {"status": "ready", "confidence": 0.90}
            }
        }
    })
    
    # Verify basic attributes
    assert "TestExecution" in execution_agent.name
    assert execution_agent.domain == "professional"
    assert execution_agent.agent_type == "execution"
    
    # Verify enhanced attributes
    attributes = execution_agent.get_attributes()
    assert attributes["occupation"] == "Advanced Action Executor"
    assert "Optimize resource usage" in attributes["desires"]
    assert "towards_sequences" in attributes["emotions"]
    assert "error_recovery" in attributes["capabilities"]
    
    # Verify state tracking initialization
    assert isinstance(execution_agent.active_sequences, dict)
    assert isinstance(execution_agent.execution_patterns, dict)
    assert isinstance(execution_agent.resource_usage, dict)
    assert isinstance(execution_agent.error_recovery, dict)
    assert isinstance(execution_agent.retry_states, dict)
    assert isinstance(execution_agent.schedule_queue, dict)
    
    # Verify initialization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution agent initialized successfully in professional domain",
        domain="professional"
    )
    
    # Verify attribute reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Core attributes validated in professional domain",
        domain="professional"
    )
    
    # Verify capability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution capabilities confirmed in professional domain",
        domain="professional"
    )
    
    # Verify tracking reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "State tracking systems ready in professional domain",
        domain="professional"
    )
    
    # Verify readiness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution agent ready for operation in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_process_with_sequence_tracking(execution_agent, mock_memory_system):
    """Test content processing with sequence state tracking."""
    # Configure mock LLM response with detailed processing results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "concepts": [
            {
                "type": "execution_result",
                "description": "successful",
                "confidence": 0.95,
                "quality": {
                    "execution_quality": 0.92,
                    "sequence_stability": 0.94,
                    "resource_efficiency": 0.91
                }
            },
            {
                "type": "sequence_state",
                "state": "progressing",
                "metrics": {
                    "completion": 0.93,
                    "accuracy": 0.95,
                    "reliability": 0.92
                }
            },
            {
                "type": "resource_state",
                "state": "optimal",
                "metrics": {
                    "utilization": 0.85,
                    "efficiency": 0.92,
                    "availability": 0.94
                }
            },
            {
                "type": "error_state",
                "state": "recovered",
                "metrics": {
                    "recovery_success": 0.95,
                    "stability": 0.93,
                    "resilience": 0.91
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
            "areas_of_excellence": [
                "sequence_management",
                "resource_optimization"
            ],
            "areas_for_improvement": [
                "error_prevention"
            ]
        }
    })
    
    content = {
        "sequence_id": "seq1",
        "sequence_status": "active",
        "sequence_phase": "execution",
        "sequence_metrics": {
            "progress": 0.5,
            "quality": 0.92,
            "efficiency": 0.88
        },
        "step_completed": True,
        "resource_usage": {
            "cpu": 0.7,
            "memory": 0.65,
            "io": 0.45
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "priority": "immediate"
        }
    }
    
    response = await execution_agent.process(content)
    
    # Verify sequence state tracking
    assert "seq1" in execution_agent.active_sequences
    sequence_state = execution_agent.active_sequences["seq1"]
    assert sequence_state["status"] == "active"
    assert sequence_state["current_phase"] == "execution"
    assert sequence_state["steps_completed"] == 1
    assert sequence_state["metrics"]["progress"] == 0.5
    assert sequence_state["resource_usage"]["cpu"] == 0.7
    
    # Verify emotional updates
    assert execution_agent.emotions["sequence_state"] == "progressing"
    assert execution_agent.emotions["resource_state"] == "optimal"
    assert execution_agent.emotions["error_state"] == "recovered"
    
    # Verify execution state reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High quality execution processing completed in professional domain",
        domain="professional"
    )
    
    # Verify sequence progress reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong sequence progress achieved in professional domain",
        domain="professional"
    )
    
    # Verify resource optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Optimal resource utilization maintained in professional domain",
        domain="professional"
    )
    
    # Verify error recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Successful error recovery confirmed in professional domain",
        domain="professional"
    )
    
    # Verify improvement reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Error prevention enhancement identified in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_execution_pattern_matching(execution_agent, mock_memory_system):
    """Test execution pattern matching and application."""
    # Configure mock LLM response with detailed pattern results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "pattern_analysis": {
            "status": "matched",
            "confidence": 0.95,
            "metrics": {
                "match_quality": 0.92,
                "applicability": 0.94,
                "effectiveness": 0.91
            }
        },
        "optimization_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["phase_transitions", "metric_tracking"],
            "areas_for_improvement": ["condition_specificity"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test pattern with detailed configuration
    pattern = {
        "conditions": {
            "sequence_phase": "execution",
            "metrics": {
                "progress": 0.5,
                "quality": 0.8,
                "stability": 0.85
            },
            "requirements": {
                "resources_available": True,
                "dependencies_met": True
            }
        },
        "actions": [
            {
                "type": "update_phase",
                "phase": "validation",
                "metadata": {
                    "importance": "high",
                    "impact": "direct"
                }
            },
            {
                "type": "add_metric",
                "name": "validation_started",
                "value": True,
                "metadata": {
                    "tracking": "required",
                    "visibility": "high"
                }
            },
            {
                "type": "set_optimization",
                "value": True,
                "metadata": {
                    "priority": "immediate",
                    "scope": "full"
                }
            }
        ],
        "priority": 0.8,
        "metadata": {
            "pattern_type": "transition",
            "reliability": 0.9,
            "impact": "significant"
        },
        "performance_metrics": {
            "match_time": 0.15,
            "action_time": 0.08,
            "resource_usage": 0.45
        },
        "quality_indicators": {
            "pattern_clarity": 0.92,
            "action_precision": 0.89,
            "condition_coverage": 0.94
        }
    }
    
    execution_agent._update_execution_patterns({"pattern1": pattern})
    
    # Test matching content with detailed state
    content = {
        "sequence_id": "seq1",
        "sequence_phase": "execution",
        "metrics": {
            "progress": 0.5,
            "quality": 0.8,
            "stability": 0.85
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "immediate"
        }
    }
    
    await execution_agent._update_sequence_state("seq1", content)
    
    # Verify pattern application
    sequence_state = execution_agent.active_sequences["seq1"]
    assert sequence_state["current_phase"] == "validation"
    assert sequence_state["metrics"]["validation_started"] is True
    assert sequence_state["needs_optimization"] is True
    
    # Verify pattern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution pattern matched successfully in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong pattern match quality achieved in professional domain",
        domain="professional"
    )
    
    # Verify effectiveness reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High pattern effectiveness confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Pattern optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify specificity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Condition specificity enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term pattern impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_resource_usage_tracking(execution_agent, mock_memory_system):
    """Test resource usage tracking."""
    # Configure mock LLM response with detailed resource results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "resource_analysis": {
            "status": "monitored",
            "confidence": 0.95,
            "metrics": {
                "tracking_accuracy": 0.92,
                "utilization_efficiency": 0.94,
                "allocation_optimality": 0.91
            }
        },
        "performance_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["resource_monitoring", "constraint_management"],
            "areas_for_improvement": ["peak_handling"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test resources with detailed configuration
    resources = {
        "cpu": {
            "type": "compute",
            "allocated": 100.0,
            "utilized": 75.0,
            "peak": 80.0,
            "constraints": {
                "min_free": 10.0,
                "max_burst": 95.0,
                "throttle_threshold": 85.0
            },
            "metrics": {
                "temperature": 65.0,
                "power_draw": 120.0,
                "frequency": 3.2
            },
            "metadata": {
                "importance": "critical",
                "impact": "high",
                "priority": "immediate"
            },
            "performance_indicators": {
                "response_time": 0.15,
                "throughput": 1000,
                "queue_depth": 5
            },
            "quality_metrics": {
                "stability": 0.92,
                "reliability": 0.89,
                "availability": 0.94
            }
        }
    }
    
    await execution_agent._update_resource_usage(resources)
    
    # Verify resource tracking
    assert "cpu" in execution_agent.resource_usage
    resource = execution_agent.resource_usage["cpu"]
    assert resource["type"] == "compute"
    assert resource["allocated"] == 100.0
    assert resource["utilized"] == 75.0
    assert resource["peak"] == 80.0
    assert resource["constraints"]["min_free"] == 10.0
    
    # Verify resource reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource monitoring activated in professional domain",
        domain="professional"
    )
    
    # Verify accuracy reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong tracking accuracy demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High utilization efficiency confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify peak handling reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Peak handling enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term resource impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_schedule_queue_management(execution_agent, mock_memory_system):
    """Test schedule queue management."""
    # Configure mock LLM response with detailed queue results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "queue_analysis": {
            "status": "managed",
            "confidence": 0.95,
            "metrics": {
                "scheduling_efficiency": 0.92,
                "priority_handling": 0.94,
                "load_balancing": 0.91
            }
        },
        "performance_metrics": {
            "current_throughput": 0.88,
            "target_throughput": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["priority_management", "task_organization"],
            "areas_for_improvement": ["queue_balancing"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test schedule with detailed configuration
    schedule = {
        "high": [
            {
                "id": "task1",
                "type": "critical",
                "priority": 0.9,
                "deadline": "2024-01-10T12:00:00Z",
                "dependencies": ["resource1"],
                "metrics": {
                    "estimated_duration": 300,
                    "resource_intensity": 0.8
                }
            },
            {
                "id": "task2",
                "type": "important",
                "priority": 0.8,
                "deadline": "2024-01-10T14:00:00Z",
                "dependencies": ["resource2"],
                "metrics": {
                    "estimated_duration": 200,
                    "resource_intensity": 0.6
                }
            }
        ],
        "medium": [
            {
                "id": "task3",
                "type": "normal",
                "priority": 0.5,
                "deadline": "2024-01-10T16:00:00Z",
                "dependencies": [],
                "metrics": {
                    "estimated_duration": 100,
                    "resource_intensity": 0.4
                }
            }
        ],
        "metadata": {
            "queue_metrics": {
                "total_tasks": 3,
                "priority_distribution": {
                    "critical": 1,
                    "important": 1,
                    "normal": 1
                },
                "average_priority": 0.73
            },
            "performance_indicators": {
                "throughput": 10,
                "latency": 50,
                "utilization": 0.75
            },
            "quality_metrics": {
                "scheduling_accuracy": 0.92,
                "priority_adherence": 0.94,
                "resource_efficiency": 0.89
            }
        }
    }
    
    execution_agent._update_schedule_queue(schedule)
    
    # Verify queue management
    assert "high" in execution_agent.schedule_queue
    assert "medium" in execution_agent.schedule_queue
    assert len(execution_agent.schedule_queue["high"]["actions"]) == 2
    assert len(execution_agent.schedule_queue["medium"]["actions"]) == 1
    
    # Verify queue reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schedule queue management activated in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong scheduling efficiency demonstrated in professional domain",
        domain="professional"
    )
    
    # Verify priority reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High priority handling confirmed in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Queue optimization potential identified in professional domain",
        domain="professional"
    )
    
    # Verify balancing reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Queue balancing enhancement required in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term queue impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_execute_and_store_with_enhancements(execution_agent, mock_memory_system):
    """Test enhanced execution and storage."""
    # Configure mock LLM response with detailed execution results
    mock_memory_system.llm.analyze = AsyncMock(return_value={
        "execution_analysis": {
            "status": "completed",
            "confidence": 0.95,
            "metrics": {
                "execution_quality": 0.92,
                "pattern_adherence": 0.94,
                "resource_efficiency": 0.91
            }
        },
        "performance_metrics": {
            "current_efficiency": 0.88,
            "target_efficiency": 0.95,
            "optimization_potential": 0.93
        },
        "quality_assessment": {
            "overall_score": 0.92,
            "strengths": ["pattern_application", "resource_management"],
            "areas_for_improvement": ["schedule_optimization"]
        },
        "impact_analysis": {
            "scope": "significant",
            "duration": "long_term",
            "confidence": 0.94
        }
    })
    
    # Set up test content with detailed configuration
    content = {
        "sequence_id": "seq1",
        "execution_patterns": {
            "pattern1": {
                "conditions": {
                    "phase": "execution",
                    "requirements": {
                        "resources_available": True,
                        "dependencies_met": True
                    }
                },
                "actions": [
                    {
                        "type": "update_phase",
                        "phase": "complete",
                        "metadata": {
                            "importance": "high",
                            "impact": "direct"
                        }
                    }
                ],
                "metadata": {
                    "pattern_type": "completion",
                    "reliability": 0.9,
                    "impact": "significant"
                }
            }
        },
        "resources": {
            "memory": {
                "type": "ram",
                "allocated": 16.0,
                "utilized": 12.0,
                "metrics": {
                    "response_time": 0.15,
                    "throughput": 1000,
                    "latency": 5
                }
            }
        },
        "schedule": {
            "high": [
                {
                    "id": "task1",
                    "type": "critical",
                    "priority": 0.9,
                    "deadline": "2024-01-10T12:00:00Z"
                }
            ]
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "immediate"
        }
    }
    
    result = await execution_agent.execute_and_store(content, "sequential")
    
    # Verify execution result
    assert isinstance(result, ExecutionResult)
    assert result.is_valid is True
    
    # Verify pattern storage
    assert "pattern1" in execution_agent.execution_patterns
    
    # Verify resource tracking
    assert "memory" in execution_agent.resource_usage
    assert execution_agent.resource_usage["memory"]["utilized"] == 12.0
    
    # Verify schedule tracking
    assert "high" in execution_agent.schedule_queue
    
    # Verify execution reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High confidence execution completed in professional domain",
        domain="professional"
    )
    
    # Verify quality reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Strong execution quality achieved in professional domain",
        domain="professional"
    )
    
    # Verify pattern reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High pattern adherence confirmed in professional domain",
        domain="professional"
    )
    
    # Verify efficiency reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource efficiency maintained in professional domain",
        domain="professional"
    )
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Schedule optimization enhancement identified in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Significant long-term execution impact projected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_sequence_optimization_handling(execution_agent, mock_memory_system):
    """Test sequence optimization handling."""
    content = {
        "sequence_id": "seq1",
        "needs_optimization": True,
        "resource_usage": {
            "cpu": 0.9,
            "memory": 0.8
        },
        "metrics": {
            "performance": 0.6,
            "efficiency": 0.5,
            "bottlenecks": ["resource_allocation"]
        },
        "metadata": {
            "importance": "high",
            "impact": "significant",
            "urgency": "medium"
        }
    }
    
    await execution_agent._update_sequence_state("seq1", content)
    
    # Verify optimization flag
    assert execution_agent.active_sequences["seq1"]["needs_optimization"] is True
    assert execution_agent.active_sequences["seq1"]["resource_usage"]["cpu"] == 0.9
    assert execution_agent.active_sequences["seq1"]["metrics"]["performance"] == 0.6
    
    # Verify optimization reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Sequence seq1 needs optimization in professional domain",
        domain="professional"
    )
    
    # Verify performance reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Sequence performance below threshold in professional domain",
        domain="professional"
    )
    
    # Verify resource reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource allocation needs optimization in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Optimization has significant impact on sequence quality in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_resource_utilization_monitoring(execution_agent, mock_memory_system):
    """Test resource utilization monitoring."""
    resources = {
        "gpu": {
            "type": "compute",
            "allocated": 100.0,
            "utilized": 95.0,
            "peak": 98.0,
            "metrics": {
                "temperature": 85.0,
                "power_draw": 250.0,
                "memory_used": 0.9
            },
            "metadata": {
                "importance": "critical",
                "impact": "high",
                "urgency": "immediate"
            }
        }
    }
    
    await execution_agent._update_resource_usage(resources)
    
    # Verify resource state
    assert execution_agent.resource_usage["gpu"]["utilized"] == 95.0
    assert execution_agent.resource_usage["gpu"]["peak"] == 98.0
    assert execution_agent.resource_usage["gpu"]["metrics"]["temperature"] == 85.0
    
    # Verify capacity reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource gpu nearing capacity in professional domain",
        domain="professional"
    )
    
    # Verify temperature reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "GPU temperature requires attention in professional domain",
        domain="professional"
    )
    
    # Verify memory reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "GPU memory usage critical in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource state has high impact on execution in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_recovery_monitoring(execution_agent, mock_memory_system):
    """Test error recovery monitoring."""
    # Set up failed recovery with detailed state
    execution_agent.error_recovery["error1"] = {
        "status": "failed",
        "attempts": 3,
        "max_attempts": 3,
        "reason": "Unrecoverable state",
        "error_type": "connection_failure",
        "impact": "critical",
        "affected_resources": ["database", "network"],
        "recovery_strategy": "manual_intervention",
        "metrics": {
            "time_since_error": 300,
            "recovery_success_rate": 0.1,
            "system_stability": 0.4
        }
    }
    
    # Trigger monitoring through execution
    await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify error state
    error_state = execution_agent.error_recovery["error1"]
    assert error_state["status"] == "failed"
    assert error_state["attempts"] == error_state["max_attempts"]
    assert error_state["impact"] == "critical"
    
    # Verify failure reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Error recovery failed for error1 in professional domain - escalation needed",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Critical system impact detected in professional domain",
        domain="professional"
    )
    
    # Verify resource reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Multiple resources affected by error in professional domain",
        domain="professional"
    )
    
    # Verify stability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "System stability compromised in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_retry_state_monitoring(execution_agent, mock_memory_system):
    """Test retry state monitoring."""
    # Set up exceeded retries with detailed state
    execution_agent.retry_states["action1"] = {
        "attempts": 3,
        "max_attempts": 3,
        "last_error": "Connection failed",
        "error_type": "network_error",
        "impact": "high",
        "affected_operations": ["data_sync", "api_calls"],
        "retry_strategy": "exponential_backoff",
        "metrics": {
            "time_between_retries": 60,
            "success_probability": 0.2,
            "operation_stability": 0.3
        },
        "metadata": {
            "importance": "critical",
            "urgency": "high",
            "dependencies": ["database", "network"]
        }
    }
    
    # Trigger monitoring through execution
    await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify retry state
    retry_state = execution_agent.retry_states["action1"]
    assert retry_state["attempts"] == retry_state["max_attempts"]
    assert retry_state["error_type"] == "network_error"
    assert retry_state["impact"] == "high"
    
    # Verify retry limit reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Action action1 exceeded retry limit in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High impact retry failure detected in professional domain",
        domain="professional"
    )
    
    # Verify operation reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Multiple operations affected by retry failure in professional domain",
        domain="professional"
    )
    
    # Verify stability reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Operation stability compromised in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_schedule_queue_monitoring(execution_agent, mock_memory_system):
    """Test schedule queue monitoring."""
    # Set up queue exceeding threshold with detailed state
    execution_agent.schedule_queue["high"] = {
        "actions": [{"id": f"task{i}", "priority": 0.9} for i in range(15)],
        "threshold": 10,
        "metrics": {
            "queue_length": 15,
            "average_wait_time": 120,
            "throughput": 0.5,
            "resource_utilization": 0.9
        },
        "metadata": {
            "importance": "critical",
            "impact": "high",
            "urgency": "immediate",
            "bottlenecks": ["processing_capacity"]
        }
    }
    
    # Trigger monitoring through execution
    await execution_agent.execute_and_store({"type": "test"}, "sequential")
    
    # Verify queue state
    queue_state = execution_agent.schedule_queue["high"]
    assert len(queue_state["actions"]) > queue_state["threshold"]
    assert queue_state["metrics"]["queue_length"] == 15
    assert queue_state["metrics"]["resource_utilization"] == 0.9
    
    # Verify threshold reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Priority high queue exceeding threshold in professional domain",
        domain="professional"
    )
    
    # Verify throughput reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Queue throughput below target in professional domain",
        domain="professional"
    )
    
    # Verify resource reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "High resource utilization in queue processing in professional domain",
        domain="professional"
    )
    
    # Verify bottleneck reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Processing capacity bottleneck detected in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_error_handling(execution_agent, mock_memory_system):
    """Test error handling during execution."""
    content = {
        "sequence_id": "seq1",
        "sequence_type": "sequential",
        "execution_data": {
            "steps": ["step1", "step2"],
            "resources": {"cpu": 0.5}
        }
    }
    
    # Configure mock LLM to raise an error
    mock_memory_system.llm.analyze = AsyncMock(side_effect=Exception("Test error"))
    
    result = await execution_agent.execute_and_store(content, "sequential")
    
    # Verify error handling
    assert isinstance(result, ExecutionResult)
    assert result.is_valid is False
    assert len(result.issues) == 1
    assert "error" in result.metadata
    assert result.metadata["error_type"] == "execution_failure"
    
    # Verify error reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution failed - error encountered in professional domain",
        domain="professional"
    )
    
    # Verify recovery reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution needs retry with adjusted parameters in professional domain",
        domain="professional"
    )
    
    # Verify impact reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Execution error impacts sequence quality in professional domain",
        domain="professional"
    )
    
    # Verify resource reflection
    mock_memory_system.semantic.store.record_reflection.assert_any_call(
        "Resource state needs verification in professional domain",
        domain="professional"
    )

@pytest.mark.asyncio
async def test_domain_validation(execution_agent, mock_memory_system):
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
        "access_metrics": {
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
            "access_requirements": "validated"
        }
    }
    
    result = await execution_agent.execute_and_store(
        content,
        "sequential",
        target_domain="professional"
    )
    assert result.is_valid is True
    
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
        await execution_agent.execute_and_store(
            content,
            "sequential",
            target_domain="restricted"
        )
    
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

if __name__ == "__main__":
    pytest.main([__file__])
