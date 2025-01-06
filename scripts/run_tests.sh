#!/bin/bash

# Run tests in specific order to validate components incrementally

echo "Running Agent Tests..."

# Run all agent tests in a single command for proper fixture sharing
pytest tests/agents/ -v --tb=short

echo "Running Nova Core Tests..."
# Run swarm integration tests first to ensure core functionality
pytest tests/nova/test_swarm_integration.py -v --tb=short
# Then run remaining Nova tests
pytest tests/nova/ -v --tb=short --ignore=tests/nova/test_swarm_integration.py

echo "Running Integration Tests..."
pytest tests/memory/ tests/test_consolidation.py -v --tb=short

echo "Test Execution Complete"
