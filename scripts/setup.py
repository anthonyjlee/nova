"""
Setup script for NIA with Neo4j support.
"""

import subprocess
import sys
import os
from pathlib import Path
import platform
import time

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

def check_neo4j():
    """Check Neo4j installation."""
    print("\nChecking Neo4j installation...")
    
    system = platform.system().lower()
    if system == "darwin":  # macOS
        try:
            result = subprocess.run(["brew", "list", "neo4j"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Neo4j not found, installing via Homebrew...")
                subprocess.run(["brew", "install", "neo4j"], check=True)
                print("Neo4j installed successfully")
            else:
                print("Neo4j already installed")
        except subprocess.CalledProcessError as e:
            print(f"Error managing Neo4j installation: {e}")
            sys.exit(1)
    elif system == "linux":
        # Add Linux-specific installation steps
        print("Please install Neo4j using your distribution's package manager")
        print("For Ubuntu: sudo apt install neo4j")
        print("For other distributions, visit: https://neo4j.com/docs/operations-manual/current/installation/")
    elif system == "windows":
        # Add Windows-specific installation steps
        print("Please download and install Neo4j from: https://neo4j.com/download/")
    else:
        print(f"Unsupported operating system: {system}")
        sys.exit(1)

def setup_neo4j():
    """Set up Neo4j configuration."""
    print("\nSetting up Neo4j...")
    
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
    
    # Start Neo4j service
    system = platform.system().lower()
    if system == "darwin":  # macOS
        try:
            print("Starting Neo4j service...")
            subprocess.run(["brew", "services", "start", "neo4j"], check=True)
            
            # Wait for Neo4j to start
            print("Waiting for Neo4j to start...")
            time.sleep(10)
            
            # Set initial password
            try:
                subprocess.run(["neo4j-admin", "set-initial-password", "password"], check=True)
                print("Neo4j password set")
            except subprocess.CalledProcessError:
                print("Password might already be set (this is okay)")
            
            print("Neo4j service started")
        except subprocess.CalledProcessError as e:
            print(f"Error starting Neo4j service: {e}")
            sys.exit(1)
    else:
        print("Please start Neo4j service manually:")
        print("- Linux: sudo systemctl start neo4j")
        print("- Windows: Start Neo4j Desktop application")

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
    check_neo4j()
    setup_neo4j()
    create_directories()
    
    print("\nSetup complete! You can now run the examples:")
    print("1. python examples/test_neo4j_memory.py")
    print("2. python examples/test_memory_dag.py")
    
    print("\nTo view the Neo4j browser interface:")
    print("1. Open http://localhost:7474 in your web browser")
    print("2. Connect using:")
    print("   - URL: bolt://localhost:7687")
    print("   - Username: neo4j")
    print("   - Password: password (or the one you set)")

if __name__ == "__main__":
    main()
