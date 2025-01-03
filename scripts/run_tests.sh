#!/bin/bash

# Run tests in specific order to validate components incrementally

echo "Running Core Agent Tests..."

# 1. Core Processing Agents
pytest tests/agents/test_parsing_agent.py -v
pytest tests/agents/test_analysis_agent.py -v
pytest tests/agents/test_validation_agent.py -v
pytest tests/agents/test_schema_agent.py -v

# 2. Cognitive Agents
pytest tests/agents/test_belief_agent.py -v
pytest tests/agents/test_desire_agent.py -v
pytest tests/agents/test_emotion_agent.py -v
pytest tests/agents/test_reflection_agent.py -v
pytest tests/agents/test_meta_agent.py -v

# 3. Task Management
pytest tests/agents/test_task_agent.py -v
pytest tests/agents/test_execution_agent.py -v
pytest tests/agents/test_orchestration_agent.py -v
pytest tests/agents/test_coordination_agent.py -v

# 4. Communication
pytest tests/agents/test_dialogue_agent.py -v
pytest tests/agents/test_response_agent.py -v
pytest tests/agents/test_integration_agent.py -v

# 5. System Operations
pytest tests/agents/test_monitoring_agent.py -v
pytest tests/agents/test_alerting_agent.py -v
pytest tests/agents/test_logging_agent.py -v
pytest tests/agents/test_metrics_agent.py -v
pytest tests/agents/test_analytics_agent.py -v
pytest tests/agents/test_visualization_agent.py -v

echo "Running Nova Core Tests..."

# 6. Nova Core
pytest tests/nova/test_initialization.py -v
pytest tests/nova/test_orchestration.py -v
pytest tests/nova/test_coordination.py -v
pytest tests/nova/test_memory_operations.py -v

echo "Running Integration Tests..."

# 7. Integration Tests
pytest tests/nova/test_integration.py -v
pytest tests/nova/test_server.py -v

echo "Running Memory Tests..."

# 8. Memory System
pytest tests/memory/test_two_layer.py -v
pytest tests/test_consolidation.py -v

echo "Test Execution Complete"
