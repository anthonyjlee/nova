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

# 1. Check Docker installation
print_status "$YELLOW" "\n1. Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_status "$RED" "Docker not found. Please install Docker first:"
    print_status "$RED" "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
print_status "$GREEN" "Docker is installed"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    print_status "$RED" "Docker Compose not found. Please install Docker Compose first:"
    print_status "$RED" "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi
print_status "$GREEN" "Docker Compose is installed"

# 2. Run Python initialization script
print_status "$YELLOW" "\n2. Running main initialization script..."
python3 scripts/initialization/all.py
check_status

# 3. Verify Neo4j is running
print_status "$YELLOW" "\n3. Verifying Neo4j..."
curl -s http://localhost:7474 > /dev/null
check_status

# 4. Verify Qdrant is running
print_status "$YELLOW" "\n4. Verifying Qdrant..."
curl -s http://localhost:6333/collections > /dev/null
check_status

# 5. Verify Memory System
print_status "$YELLOW" "\n6. Verifying Memory System..."
curl -s http://localhost:6333/collections/memory > /dev/null
check_status


print_status "$GREEN" "\nInitialization complete! ✨"
echo "=================================="

print_status "$YELLOW" "\nYou can now:"
print_status "$GREEN" "1. Access Neo4j browser at http://localhost:7474"
print_status "$GREEN" "2. Connect using:"
print_status "$GREEN" "   - URL: bolt://localhost:7687"
print_status "$GREEN" "   - Username: neo4j"
print_status "$GREEN" "   - Password: password"
