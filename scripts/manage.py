#!/usr/bin/env python3
"""Service management script for NIA."""

import argparse
import subprocess
import sys
import time
import requests
import os
from pathlib import Path

class ServiceManager:
    """Manages NIA services."""
    
    def __init__(self):
        """Initialize service manager."""
        self.docker_compose_file = "scripts/docker/docker-compose.yml"
        self.services = {
            "neo4j": {
                "port": 7474,
                "health_url": "http://localhost:7474",
                "startup_time": 10
            },
            "qdrant": {
                "port": 6333,
                "health_url": "http://localhost:6333/dashboard",
                "startup_time": 5
            },
            "lmstudio": {
                "port": 1234,
                "health_url": "http://localhost:1234/v1/models",
                "startup_time": 2
            },
            "fastapi": {
                "port": 8000,
                "health_url": "http://localhost:8000/docs",
                "startup_time": 3
            }
        }
    
    def check_service(self, name: str, url: str) -> bool:
        """Check if a service is responding."""
        try:
            response = requests.get(url)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def check_docker(self):
        """Check if Docker is running."""
        try:
            subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            print("❌ Docker is not running")
            print("Please start Docker Desktop")
            return False

    def start_docker_services(self):
        """Start Neo4j and Qdrant containers."""
        print("\n🐳 Starting Docker services...")
        
        # Check Docker first
        if not self.check_docker():
            sys.exit(1)
            
        try:
            # Start containers
            subprocess.run(
                ["docker", "compose", "-f", self.docker_compose_file, "up", "-d"],
                check=True
            )
            
            # Wait for services with longer timeout
            services_ready = True
            for service in ["neo4j", "qdrant"]:
                if not self.wait_for_service(service, timeout=60):
                    services_ready = False
            
            if not services_ready:
                print("❌ Some Docker services failed to start")
                self.stop_services()
                sys.exit(1)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error starting Docker services: {e}")
            sys.exit(1)
    
    def check_lmstudio(self):
        """Check if LMStudio is running."""
        print("\n🤖 Checking LMStudio...")
        if self.check_service("lmstudio", self.services["lmstudio"]["health_url"]):
            print("✅ LMStudio is running")
        else:
            print("❌ LMStudio is not running")
            print("Please:")
            print("1. Open LMStudio application")
            print("2. Load your preferred model")
            print("3. Start the local server")
            sys.exit(1)
    
    def check_dependencies(self):
        """Check if required Python packages are installed."""
        try:
            import uvicorn
            import fastapi
            import tinytroupe
            return True
        except ImportError as e:
            print(f"❌ Missing dependencies: {e}")
            print("Please run: pdm install")
            return False

    def check_tinytroupe_config(self):
        """Check TinyTroupe configuration."""
        site_packages_config = Path(".venv/lib/python3.12/site-packages/tinytroupe/config.ini")
        custom_config = Path("config.ini")
        
        print("\n🔍 Checking TinyTroupe configuration...")
        print(f"Site packages config: {site_packages_config.absolute()}")
        print(f"Custom config: {custom_config.absolute()}")
        
        # Try to read configs to verify they're valid
        configs_valid = False
        
        if site_packages_config.exists():
            try:
                with open(site_packages_config) as f:
                    content = f.read()
                    if "[DEFAULT]" in content and "[MEMORY]" in content:
                        print("✅ Site packages config is valid")
                        configs_valid = True
                    else:
                        print("⚠️  Site packages config is invalid")
            except Exception as e:
                print(f"⚠️  Error reading site packages config: {e}")
        
        if custom_config.exists():
            try:
                with open(custom_config) as f:
                    content = f.read()
                    if "[DEFAULT]" in content and "[MEMORY]" in content:
                        print("✅ Custom config is valid")
                        configs_valid = True
                    else:
                        print("⚠️  Custom config is invalid")
            except Exception as e:
                print(f"⚠️  Error reading custom config: {e}")
        
        if not configs_valid:
            print("\n⚠️  No valid TinyTroupe configuration found")
            print("Creating default config.ini...")
            
            config_content = """[DEFAULT]
model_api_type = lmstudio
model_api_base = http://localhost:1234/v1
model_name = local-model

[MEMORY]
consolidation_interval = 300
importance_threshold = 0.5
"""
            try:
                with open(custom_config, "w") as f:
                    f.write(config_content)
                print(f"✅ Created default config.ini at {custom_config.absolute()}")
                print("Please customize if needed, especially:")
                print("- model_api_type")
                print("- model_api_base")
                print("- model_name")
            except Exception as e:
                print(f"❌ Failed to create config.ini: {e}")
                sys.exit(1)

    def wait_for_service(self, name: str, timeout: int = 30, interval: int = 1):
        """Wait for service to be ready with timeout."""
        print(f"⏳ Waiting for {name} to start...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service(name, self.services[name]["health_url"]):
                print(f"✅ {name} is running")
                return True
            time.sleep(interval)
        print(f"⚠️  {name} did not start within {timeout} seconds")
        return False

    def start_fastapi(self):
        """Start FastAPI server."""
        print("\n🚀 Starting FastAPI server...")
        
        # Check dependencies first
        if not self.check_dependencies():
            sys.exit(1)
            
        # Check and create TinyTroupe config
        self.check_tinytroupe_config()
            
        try:
            # Set up environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd())
            
            # Start server with output
            process = subprocess.Popen(
                ["python", "scripts/run_server.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Check for immediate startup errors
            time.sleep(1)
            if process.poll() is not None:
                _, stderr = process.communicate()
                print(f"❌ FastAPI failed to start:\n{stderr}")
                sys.exit(1)
                
            # Wait for server to be ready
            if not self.wait_for_service("fastapi"):
                print("❌ FastAPI server failed to respond")
                self.stop_fastapi()
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error starting FastAPI server: {e}")
            sys.exit(1)
            
    def stop_fastapi(self):
        """Stop FastAPI server."""
        try:
            subprocess.run(["pkill", "-f", "scripts/run_server.py"], check=False)
        except Exception as e:
            print(f"Warning: Error stopping FastAPI: {e}")
    
    def stop_services(self):
        """Stop all services."""
        print("\n🛑 Stopping services...")
        
        # Stop FastAPI (find and kill process)
        print("Stopping FastAPI...")
        try:
            subprocess.run(
                ["pkill", "-f", "scripts/run_server.py"],
                check=False
            )
        except Exception as e:
            print(f"Warning: Error stopping FastAPI: {e}")
        
        # Stop Docker services
        print("Stopping Docker services...")
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.docker_compose_file, "down"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error stopping Docker services: {e}")
            sys.exit(1)
        
        print("✅ All services stopped")
    
    def show_status(self):
        """Show status of all services."""
        print("\n📊 Service Status:")
        
        # Check Docker services
        for service in ["neo4j", "qdrant"]:
            status = "✅ Running" if self.check_service(
                service, 
                self.services[service]["health_url"]
            ) else "❌ Not running"
            print(f"{service.title()}: {status}")
        
        # Check LMStudio
        status = "✅ Running" if self.check_service(
            "lmstudio",
            self.services["lmstudio"]["health_url"]
        ) else "❌ Not running"
        print(f"LMStudio: {status}")
        
        # Check FastAPI
        status = "✅ Running" if self.check_service(
            "fastapi",
            self.services["fastapi"]["health_url"]
        ) else "❌ Not running"
        print(f"FastAPI: {status}")

def main():
    """Run service manager."""
    parser = argparse.ArgumentParser(description="Manage NIA services")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    manager = ServiceManager()
    
    if args.action == "start":
        manager.start_docker_services()
        manager.check_lmstudio()
        manager.check_tinytroupe_config()
        manager.start_fastapi()
        print("\n✨ All services started!")
        
    elif args.action == "stop":
        manager.stop_services()
        
    elif args.action == "restart":
        manager.stop_services()
        time.sleep(2)
        manager.start_docker_services()
        manager.check_lmstudio()
        manager.check_tinytroupe_config()
        manager.start_fastapi()
        print("\n✨ All services restarted!")
        
    elif args.action == "status":
        manager.show_status()

if __name__ == "__main__":
    main()
