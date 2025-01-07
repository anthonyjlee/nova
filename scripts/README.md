# NIA Scripts

This directory contains various utility scripts for the NIA project:

## Core Scripts

### manage.py
Service management script that:
- Starts/stops all required services in the correct order
- Checks service health and status
- Provides easy restart functionality
- Monitors service availability

Usage:
```bash
# Start all services
python scripts/manage.py start

# Check service status
python scripts/manage.py status

# Stop all services
python scripts/manage.py stop

# Restart all services
python scripts/manage.py restart
```

### initialize.py (formerly setup.py)
Project initialization script that:
- Verifies Python version
- Sets up Docker containers (Neo4j, Qdrant)
- Creates necessary directories
- Initializes environment variables

### run_server.py
Starts the FastAPI server with:
- WebSocket support
- Memory system integration
- Agent coordination

### run_tests.sh
Test execution script with:
- Pytest configuration
- Coverage reporting
- Performance metrics

## Docker Scripts (To Be Organized)
Currently in root directory, should be moved to scripts/docker/:
- docker-compose.yml
- Dockerfile.neo4j
- Dockerfile.qdrant

## Test Scripts
- run_performance_tests.py: Load and performance testing
- test_lmstudio.sh: LMStudio integration testing

## Utility Scripts
- fix_imports.py: Import statement organization
- demo.py: Example usage demonstrations

## Organization TODO
1. Create subdirectories:
   ```
   scripts/
   ├── docker/          # Docker-related files
   │   ├── compose/     # Docker compose files
   │   └── dockerfiles/ # Dockerfile definitions
   ├── test/           # Test-related scripts
   └── utils/          # Utility scripts
   ```

2. Move files to appropriate directories
3. Update import paths and references
4. Add documentation for each script
