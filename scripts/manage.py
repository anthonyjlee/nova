#!/usr/bin/env python3
"""Service management script for NIA."""

import argparse
import subprocess
import sys
import time
import requests
import os
import socket
import redis
from pathlib import Path
from celery.app.control import Control

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
os.environ["PYTHONPATH"] = str(project_root)

from src.nia.nova.core.celery_app import celery_app

class ServiceManager:
    """Manages NIA services."""
    
    def __init__(self):
        """Initialize service manager."""
        self.docker_compose_file = "scripts/docker/docker-compose.yml"
        self.debug = False  # Control debug output
        self.services = {
            "neo4j": {
                "port": 7687,
                "health_url": "http://localhost:7474/browser/",
                "startup_time": 30
            },
            "qdrant": {
                "port": 6333,
                "health_url": "http://localhost:6333/dashboard",
                "startup_time": 5
            },
            "redis": {
                "port": 6379,
                "health_url": None,  # Redis doesn't use HTTP
                "startup_time": 2
            },
            "lmstudio": {
                "port": 1234,
                "health_url": "http://localhost:1234/v1/models",
                "startup_time": 2
            },
            "fastapi": {
                "port": 8000,
                "health_url": "http://localhost:8000/api/status?key=development",
                "startup_time": 3
            },
            "frontend": {
                "port": 5173,
                "health_url": "http://localhost:5173",
                "startup_time": 2
            },
            "celery": {
                "port": None,
                "health_url": None,
                "startup_time": 2
            }
        }
    
    def check_service(self, name: str, url: str = None) -> bool:
        """Check if a service is responding."""
        try:
            if name == "neo4j":
                # First check HTTP endpoint
                http_response = requests.get(url)
                if http_response.status_code != 200:
                    return False
                    
                # Then check if Bolt port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 7687))
                sock.close()
                return result == 0
                
            elif name == "redis":
                # Check Redis using socket connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 6379))
                sock.close()
                if result != 0:
                    return False
                    
                # Try to ping Redis
                try:
                    r = redis.Redis(host='localhost', port=6379, db=0)
                    return r.ping()
                except:
                    return False
                    
            elif name == "frontend":
                try:
                    # Check if port is open first
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 5173))
                    sock.close()
                    if result != 0:
                        return False
                        
                    # Then try HTTP request - accept any response as Vite may return non-200
                    response = requests.get(url)
                    return True
                except:
                    return False
                    
            elif name == "celery":
                try:
                    # First check if process exists
                    subprocess.check_output(["pgrep", "-f", "celery worker"])
                    
                    # Then check if worker is responding
                    control = Control(celery_app)
                    active = control.ping(timeout=1.0)
                    return bool(active)
                except:
                    return False
                    
            else:
                # Default HTTP check for other services
                response = requests.get(url)
                return response.status_code == 200
                
        except Exception as e:
            if self.debug:
                print(f"Error checking {name}: {str(e)}")
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
            
            # Neo4j needs extra time to initialize
            print("\n⏳ Waiting for Neo4j to initialize (this may take a minute)...")
            if not self.wait_for_service("neo4j", timeout=120):
                services_ready = False
            
            # Then check Qdrant
            if services_ready and not self.wait_for_service("qdrant", timeout=60):
                services_ready = False
            
            if not services_ready:
                print("❌ Some Docker services failed to start")
                self.stop_services()
                sys.exit(1)
                
            # Give Neo4j extra time to complete initialization
            print("✅ Docker services started, waiting for full initialization...")
            time.sleep(5)
                
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
                    if "[DEFAULT]" in content and "[MEMORY]" in content and "[WORKSPACES]" in content:
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
                    if "[DEFAULT]" in content and "[MEMORY]" in content and "[WORKSPACES]" in content:
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

[WORKSPACES]
# Access level configuration
personal_enabled = true
professional_enabled = true

[DOMAINS]
# Knowledge domains for Professional workspace
domains = retail,bfsi,finance
default_domain = retail

# Domain-specific settings
retail_memory_threshold = 0.6
bfsi_memory_threshold = 0.7
finance_memory_threshold = 0.7
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

    def start_celery(self):
        """Start Celery worker."""
        print("\n🌾 Starting Celery worker...")
        try:
            # Set up environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd())
            
            # Start Celery worker with direct venv python path
            venv_python = str(Path.cwd() / ".venv" / "bin" / "python")
            celery_cmd = [
                venv_python, "-m", "celery",
                "-A", "src.nia.nova.core.celery_app",
                "worker",
                "--loglevel=info"
            ]
            
            process = subprocess.Popen(
                celery_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path.cwd())  # Ensure correct working directory
            )
            
            # Check for immediate startup errors
            time.sleep(1)
            if process.poll() is not None:
                _, stderr = process.communicate()
                print(f"❌ Celery worker failed to start:\n{stderr}")
                sys.exit(1)
                
            # Wait for worker to be responsive
            start_time = time.time()
            while time.time() - start_time < 30:  # 30 second timeout
                if self.check_service("celery"):
                    print("✅ Celery worker started and responding")
                    return
                time.sleep(1)
                
            print("❌ Celery worker started but not responding")
            sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error starting Celery worker: {e}")
            sys.exit(1)

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
            
            # Start FastAPI server with direct venv python path
            venv_python = str(Path.cwd() / ".venv" / "bin" / "python")
            server_cmd = [
                venv_python,
                "scripts/run_server.py"
            ]
            
            process = subprocess.Popen(
                server_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path.cwd())  # Ensure correct working directory
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
    
    def start_frontend(self):
        """Start frontend development server."""
        print("\n🎨 Starting frontend server...")
        try:
            # Set up environment
            env = os.environ.copy()
            
            # Start frontend server with npm path
            frontend_path = Path.cwd() / "frontend"
            npm_cmd = ["npm", "run", "dev"]
            
            process = subprocess.Popen(
                npm_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(frontend_path)  # Run in frontend directory
            )
            
            # Check for immediate startup errors
            time.sleep(1)
            if process.poll() is not None:
                _, stderr = process.communicate()
                print(f"❌ Frontend server failed to start:\n{stderr}")
                sys.exit(1)
                
            # Wait for server to be ready with more lenient check
            start_time = time.time()
            while time.time() - start_time < 30:  # 30 second timeout
                if self.check_service("frontend", self.services["frontend"]["health_url"]):
                    print("✅ Frontend server started")
                    return
                time.sleep(1)
                
            print("❌ Frontend server failed to respond")
            self.stop_frontend()
            sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error starting frontend server: {e}")
            sys.exit(1)

    def stop_frontend(self):
        """Stop frontend server."""
        try:
            subprocess.run(["pkill", "-f", "vite"], check=False)
        except Exception as e:
            print(f"Warning: Error stopping frontend: {e}")

    def stop_celery(self):
        """Stop Celery worker."""
        print("Stopping Celery worker...")
        try:
            subprocess.run(["pkill", "-f", "celery worker"], check=False)
        except Exception as e:
            print(f"Warning: Error stopping Celery worker: {e}")

    def cleanup_data(self):
        """Clean up all data stores."""
        print("\n🧹 Cleaning up data stores...")
        
        # Stop all services first
        self.stop_services()
        
        try:
            # Clear Redis data
            print("Clearing Redis data...")
            subprocess.run(
                ["docker", "compose", "-f", self.docker_compose_file, "run", "redis", "redis-cli", "FLUSHALL"],
                check=True
            )
            
            # Clear Neo4j data
            print("Clearing Neo4j data...")
            data_path = Path("scripts/data/neo4j")
            if data_path.exists():
                subprocess.run(["rm", "-rf", str(data_path)], check=True)
            
            # Clear Qdrant data
            print("Clearing Qdrant data...")
            qdrant_path = Path("scripts/data/qdrant")
            if qdrant_path.exists():
                subprocess.run(["rm", "-rf", str(qdrant_path)], check=True)
                
            print("✅ All data stores cleaned")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during cleanup: {e}")
            sys.exit(1)

    def stop_services(self):
        """Stop all services."""
        print("\n🛑 Stopping services...")
        
        # Stop all processes
        processes = [
            "scripts/run_server.py",  # FastAPI
            "celery worker",          # Celery
            "vite",                   # Frontend
            "redis-server"            # Redis
        ]
        
        for process in processes:
            try:
                subprocess.run(["pkill", "-f", process], check=False)
            except Exception as e:
                print(f"Warning: Error stopping {process}: {e}")
        
        # Stop Docker services
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.docker_compose_file, "down"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error stopping Docker services: {e}")
            sys.exit(1)
        
        print("✅ All services stopped")
    
    def check_workspace_config(self):
        """Validate workspace and domain configuration."""
        print("\n🔍 Checking workspace configuration...")
        
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read("config.ini")
            
            # Check workspaces section
            if not config.has_section("WORKSPACES"):
                print("⚠️  Missing [WORKSPACES] section")
                return False
                
            # Check domains section
            if not config.has_section("DOMAINS"):
                print("⚠️  Missing [DOMAINS] section")
                return False
                
            # Validate domains
            domains = config.get("DOMAINS", "domains", fallback="").split(",")
            if not domains or not all(domains):
                print("⚠️  No domains configured for Professional workspace")
                return False
                
            print("✅ Workspace configuration valid")
            print(f"Available domains: {', '.join(domains)}")
            return True
            
        except Exception as e:
            print(f"❌ Error checking workspace config: {e}")
            return False

    def show_status(self):
        """Show status of all services."""
        print("\n📊 Service Status:")
        
        # Check Docker services
        for service in ["neo4j", "qdrant", "redis"]:
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
        
        # Check Frontend
        status = "✅ Running" if self.check_service(
            "frontend",
            self.services["frontend"]["health_url"]
        ) else "❌ Not running"
        print(f"Frontend: {status}")

        # Check Celery
        status = "✅ Running" if self.check_service("celery") else "❌ Not running"
        print(f"Celery Worker: {status}")
        
        # Check workspace configuration
        print("\n📊 Workspace Status:")
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read("config.ini")
            
            # Show workspace status
            personal = config.getboolean("WORKSPACES", "personal_enabled", fallback=True)
            professional = config.getboolean("WORKSPACES", "professional_enabled", fallback=True)
            print(f"Personal Workspace: {'✅ Enabled' if personal else '❌ Disabled'}")
            print(f"Professional Workspace: {'✅ Enabled' if professional else '❌ Disabled'}")
            
            # Show domain status
            if professional:
                print("\n📊 Domain Status:")
                domains = config.get("DOMAINS", "domains", fallback="").split(",")
                default = config.get("DOMAINS", "default_domain", fallback="")
                for domain in domains:
                    if domain:
                        threshold = config.getfloat("DOMAINS", f"{domain}_memory_threshold", fallback=0.5)
                        print(f"{domain.upper()}: Memory Threshold {threshold}")
                print(f"Default Domain: {default.upper() if default else 'Not set'}")
        except Exception as e:
            print(f"⚠️  Error showing workspace status: {e}")

def main():
    """Run service manager."""
    parser = argparse.ArgumentParser(description="Manage NIA services")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status", "check-workspace", "cleanup"],
        help="Action to perform"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    manager = ServiceManager()
    manager.debug = args.debug
    
    if args.action == "start":
        manager.start_docker_services()
        manager.check_lmstudio()
        manager.check_tinytroupe_config()
        if not manager.check_workspace_config():
            print("❌ Invalid workspace configuration")
            sys.exit(1)
        manager.start_celery()
        manager.start_fastapi()
        manager.start_frontend()
        print("\n✨ All services started!")
        
    elif args.action == "stop":
        manager.stop_services()
        
    elif args.action == "restart":
        manager.stop_services()
        time.sleep(2)
        manager.start_docker_services()
        manager.check_lmstudio()
        manager.check_tinytroupe_config()
        if not manager.check_workspace_config():
            print("❌ Invalid workspace configuration")
            sys.exit(1)
        manager.start_celery()
        manager.start_fastapi()
        manager.start_frontend()
        print("\n✨ All services restarted!")
        
    elif args.action == "check-workspace":
        manager.check_workspace_config()
        
    elif args.action == "status":
        manager.show_status()
    elif args.action == "cleanup":
        manager.cleanup_data()

if __name__ == "__main__":
    main()
