#!/bin/bash

# Check if LM Studio is running
echo "Checking LM Studio..."
if ! curl --output /dev/null --silent --head --fail http://localhost:1234/v1/models; then
    echo "Error: LM Studio is not running!"
    echo "Please:"
    echo "1. Open LM Studio"
    echo "2. Load a model"
    echo "3. Start the local server"
    exit 1
fi

echo "LM Studio is running!"

# Start other services
echo "Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services to be ready..."
max_attempts=60

# Check Qdrant
echo "Checking Qdrant..."
attempt_counter=0
until curl -v http://localhost:6333/healthz; do
    if [ ${attempt_counter} -eq ${max_attempts} ]; then
        echo "Qdrant is not ready after ${max_attempts} attempts."
        docker compose down
        exit 1
    fi
    printf '.'
    attempt_counter=$(($attempt_counter+1))
    sleep 2
done
echo "Qdrant is ready!"

# Check Neo4j
echo "Checking Neo4j..."
attempt_counter=0
until curl -v http://localhost:7474/browser/; do
    if [ ${attempt_counter} -eq ${max_attempts} ]; then
        echo "Neo4j is not ready after ${max_attempts} attempts."
        docker compose down
        exit 1
    fi
    printf '.'
    attempt_counter=$(($attempt_counter+1))
    sleep 2
done
echo "Neo4j is ready!"

echo "All services are ready!"

# Run the integration tests
echo "Running LM Studio integration tests..."
pytest tests/nova/test_lmstudio_integration.py -v

# Cleanup
echo "Cleaning up..."
docker compose down
