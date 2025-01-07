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
        self.docker_compose_file = "scripts/docker/compose/docker-compose.yml"
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
    
    def start_docker_services(self):
        """Start Neo4j and Qdrant containers."""
        print("\n🐳 Starting Docker services...")
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.docker_compose_file, "up", "-d"],
                check=True
            )
            
            # Wait for Neo4j
            print("⏳ Waiting for Neo4j to start...")
            time.sleep(self.services["neo4j"]["startup_time"])
            if self.check_service("neo4j", self.services["neo4j"]["health_url"]):
                print("✅ Neo4j is running")
            else:
                print("⚠️  Neo4j may not be ready")
            
            # Wait for Qdrant
            print("⏳ Waiting for Qdrant to start...")
            time.sleep(self.services["qdrant"]["startup_time"])
            if self.check_service("qdrant", self.services["qdrant"]["health_url"]):
                print("✅ Qdrant is running")
            else:
                print("⚠️  Qdrant may not be ready")
                
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
    
    def start_fastapi(self):
        """Start FastAPI server."""
        print("\n🚀 Starting FastAPI server...")
        try:
            subprocess.Popen(
                ["python", "scripts/run_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server
            print("⏳ Waiting for FastAPI to start...")
            time.sleep(self.services["fastapi"]["startup_time"])
            if self.check_service("fastapi", self.services["fastapi"]["health_url"]):
                print("✅ FastAPI is running")
            else:
                print("⚠️  FastAPI may not be ready")
                
        except Exception as e:
            print(f"❌ Error starting FastAPI server: {e}")
            sys.exit(1)
    
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
        manager.start_fastapi()
        print("\n✨ All services started!")
        
    elif args.action == "stop":
        manager.stop_services()
        
    elif args.action == "restart":
        manager.stop_services()
        time.sleep(2)
        manager.start_docker_services()
        manager.check_lmstudio()
        manager.start_fastapi()
        print("\n✨ All services restarted!")
        
    elif args.action == "status":
        manager.show_status()

if __name__ == "__main__":
    main()
