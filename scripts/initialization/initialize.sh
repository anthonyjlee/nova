#!/bin/bash

# Initialize colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored status messages
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        print_status "$GREEN" "✓ Success"
    else
        print_status "$RED" "✗ Failed"
        exit 1
    fi
}

# Print banner
echo "=================================="
print_status "$YELLOW" "NIA System Initialization"
echo "=================================="

# 1. Run Python initialization script
print_status "$YELLOW" "\n1. Running main initialization script..."
python3 scripts/initialize_all.py
check_status

# 2. Verify Neo4j is running
print_status "$YELLOW" "\n2. Verifying Neo4j..."
curl -s http://localhost:7474 > /dev/null
check_status

# 3. Verify Qdrant is running
print_status "$YELLOW" "\n3. Verifying Qdrant..."
curl -s http://localhost:6333/collections > /dev/null
check_status

# 4. Verify WebSocket server
print_status "$YELLOW" "\n4. Verifying WebSocket server..."
curl -s http://localhost:8000/ws > /dev/null
check_status

print_status "$GREEN" "\nInitialization complete! ✨"
echo "=================================="
