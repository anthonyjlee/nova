#!/bin/bash

# Run tests in specific order to validate components incrementally

echo "Running Agent Tests..."

# Run all agent tests in a single command for proper fixture sharing
pytest tests/agents/ -v --tb=short

echo "Running Nova Core Tests..."
pytest tests/nova/ -v --tb=short

echo "Running Integration Tests..."
pytest tests/memory/ tests/test_consolidation.py -v --tb=short

echo "Test Execution Complete"
