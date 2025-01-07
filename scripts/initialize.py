"""
Setup script for NIA with Neo4j support using Docker.
"""

import subprocess
import sys
import os
from pathlib import Path
import platform
import time
import json

def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required")
        sys.exit(1)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def check_docker():
    """Check Docker installation."""
    print("\nChecking Docker installation...")
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("Docker is installed")
    except FileNotFoundError:
        print("Docker not found. Please install Docker first:")
        print("Visit: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    print("\nChecking Docker Compose installation...")
    try:
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
        print("Docker Compose is installed")
    except subprocess.CalledProcessError:
        print("Docker Compose not found. Please install Docker Compose first:")
        print("Visit: https://docs.docker.com/compose/install/")
        sys.exit(1)

def setup_neo4j():
    """Set up Neo4j using Docker."""
    print("\nSetting up Neo4j...")
    
    # Create data and logs directories
    data_dir = Path("data/neo4j")
    logs_dir = Path("logs/neo4j")
    
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    print("Created data and logs directories")
    
    # Create .env file with Neo4j credentials
    env_path = Path(".env")
    if not env_path.exists():
        print("Creating .env file with Neo4j credentials...")
        with open(env_path, "w") as f:
            f.write("""# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password  # Change this in production
""")
        print(".env file created")
    else:
        print(".env file already exists")
    
    # Start Neo4j container
    print("\nStarting Neo4j container...")
    try:
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        print("Neo4j container started")
        
        # Wait for Neo4j to be ready
        print("Waiting for Neo4j to be ready...")
        max_retries = 30
        retry = 0
        while retry < max_retries:
            try:
                result = subprocess.run(
                    ["docker", "compose", "ps", "--format", "json"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                services = json.loads(result.stdout)
                if any(s["State"] == "running" and "neo4j" in s["Service"] for s in services):
                    print("Neo4j is ready!")
                    break
            except:
                pass
            
            retry += 1
            time.sleep(1)
            
        if retry == max_retries:
            print("Warning: Neo4j container might not be ready yet")
    
    except subprocess.CalledProcessError as e:
        print(f"Error starting Neo4j container: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    print("\nCreating directories...")
    directories = [
        "logs",
        "data",
        "visualizations"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

def main():
    """Run setup process."""
    print("Setting up NIA with Neo4j support...\n")
    
    check_python_version()
    install_dependencies()
    check_docker()
    setup_neo4j()
    create_directories()
    
    print("\nSetup complete! You can now:")
    print("1. Access Neo4j browser at http://localhost:7474")
    print("2. Connect using:")
    print("   - URL: bolt://localhost:7687")
    print("   - Username: neo4j")
    print("   - Password: password")
    print("\n3. Run the examples:")
    print("   python examples/test_neo4j_memory.py")
    print("   python examples/test_memory_dag.py")
    
    print("\nTo stop Neo4j:")
    print("docker compose down")

if __name__ == "__main__":
    main()
