#!/bin/bash

# Run tests in specific order to validate components incrementally

echo "Running Memory Integration Tests..."
# Run memory tests first since they're blocking frontend development
pytest tests/memory/integration/test_memory_basic.py -v --tb=short
pytest tests/memory/integration/test_memory_domains.py -v --tb=short
pytest tests/memory/integration/test_memory_consolidation.py -v --tb=short
pytest tests/memory/integration/test_memory_lifecycle.py -v --tb=short
pytest tests/memory/integration/test_memory_errors.py -v --tb=short
pytest tests/memory/integration/test_memory_integration.py -v --tb=short

echo "Running Profile Integration Tests..."
# Test profile-based task adaptations
pytest tests/core/profiles/ -v --tb=short

echo "Running Agent Tests..."
# Run all agent tests in a single command for proper fixture sharing
pytest tests/agents/ -v --tb=short

echo "Running Nova Core Tests..."
# Run swarm integration tests first to ensure core functionality
pytest tests/nova/test_swarm_integration.py -v --tb=short
# Then run remaining Nova tests
pytest tests/nova/ -v --tb=short --ignore=tests/nova/test_swarm_integration.py

echo "Running Other Integration Tests..."
pytest tests/test_consolidation.py -v --tb=short

echo "Test Execution Complete"
