"""Service management script for NIA."""

import argparse
import configparser
import subprocess
import sys
import time
import requests
import os
import socket
import redis
import logging
from pathlib import Path
from celery.app.control import Control

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO level to reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(Path.cwd() / 'logs' / 'service_manager.log'))
    ]
)
logger = logging.getLogger('service_manager')

# Reduce urllib3 logging noise
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
os.environ["PYTHONPATH"] = str(project_root)

from nia.nova.core.celery_app import celery_app

class ServiceManager:
    """Manages NIA services."""
    
    def __init__(self):
        """Initialize service manager."""
        self.docker_compose_file = "scripts/docker/docker-compose.yml"
        self.debug = False  # Disable debug output
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": "valid-test-key"})
        
        # Read config
        self.config = configparser.ConfigParser()
        self.config.read(str(Path.cwd().parent / 'config.ini'))
        self.embedding_model = self.config.get('DEFAULT', 'embedding_model', fallback='text-embedding-nomic-embed-text-v1.5@f16')
        self.services = {
            "neo4j": {
                "port": 7687,
                "health_url": "http://localhost:7474/browser/",
                "startup_time": 30,
                "check_interval": 5  # Add check interval to reduce frequency
            },
            "qdrant": {
                "port": 6333,
                "health_url": "http://localhost:6333/dashboard",
                "startup_time": 5
            },
            "redis": {
                "port": 6379,
                "health_url": None,
                "startup_time": 2
            },
            "lmstudio": {
                "port": 1234,
                "health_url": "http://localhost:1234/v1/models",
                "startup_time": 2
            },
            "fastapi": {
                "port": 8000,
                "health_url": "http://localhost:8000/api/status",
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

    def check_service(self, name: str, url: str | None = None) -> bool:
        """Check if a service is responding."""
        try:
            if name == "neo4j":
                try:
                    # First check HTTP endpoint
                    if url is None:
                        return False
                    http_response = requests.get(url)
                    if http_response.status_code != 200:
                        return False
                        
                    # Then check if Bolt port is open
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 7687))
                    sock.close()
                    return result == 0
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Neo4j check error: {str(e)}")
                    return False
                
            elif name == "redis":
                try:
                    # First check socket connection
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 6379))
                    sock.close()
                    if result != 0:
                        return False
                    
                    # Then verify Redis is accepting connections
                    r = redis.Redis(host='localhost', port=6379, db=0)
                    if not r.ping():
                        return False
                        
                    # Finally verify Redis is ready for operations
                    test_key = "health_check"
                    r.set(test_key, "test")
                    if r.get(test_key) != b"test":
                        return False
                    r.delete(test_key)
                    return True
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Redis check error: {str(e)}")
                    return False
                    
            elif name == "frontend":
                try:
                    # First check if port is open
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 5173))
                    sock.close()
                    if result != 0:
                        return False
                    
                    # Then verify Vite is serving content
                    if url is None:
                        return False
                    response = requests.get(url)
                    # Check for Vite's dev server signature in headers
                    server_header = response.headers.get('server', '').lower()
                    if 'vite' in server_header:
                        return True
                    # Fallback check - look for SvelteKit content
                    return 'sveltekit' in response.text.lower()
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Frontend check error: {str(e)}")
                    return False
                    
            elif name == "celery":
                try:
                    # First check if Redis is ready since Celery depends on it
                    if not self.check_service("redis", None):
                        if self.debug:
                            logger.debug("Redis not ready for Celery")
                        return False
                    
                    # Then check if celery process exists
                    subprocess.check_output(["pgrep", "-f", "celery.*nia.nova.core.celery_app.*worker"])
                    
                    # Finally check if worker is responding using our status check
                    status = celery_app.send_task('nova.check_status').get(timeout=5.0)
                    if not status:
                        return False
                    celery_status = status.get('celery', {})
                    return bool(
                        celery_status.get('active') and 
                        celery_status.get('workers') and 
                        celery_status['workers'][0]['status'] == 'active'
                    )
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Celery check error: {str(e)}")
                    return False
                    
            else:
                # Default HTTP check for other services
                try:
                    if url is None:
                        return False
                    headers = {}
                    if name == "fastapi":
                        headers["X-API-Key"] = "valid-test-key"
                    response = self.session.get(url)
                    return response.status_code == 200
                except Exception as e:
                    if self.debug:
                        logger.debug(f"HTTP check error for {name}: {str(e)}")
                    return False
                
        except Exception as e:
            if self.debug:
                logger.debug(f"Error checking {name}: {str(e)}")
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
            logger.error("Docker is not running")
            print("❌ Docker is not running")
            print("Please start Docker Desktop")
            return False

    def wait_for_service(self, name: str, timeout: int = 30, interval: int = 1):
        """Wait for service to be ready with timeout."""
        print(f"⏳ Waiting for {name} to start...")
        start_time = time.time()
        check_interval = self.services[name].get("check_interval", interval)
        
        while time.time() - start_time < timeout:
            if self.check_service(name, self.services[name]["health_url"]):
                print(f"✅ {name} is running")
                return True
            time.sleep(check_interval)  # Use service-specific interval
            
        logger.warning(f"{name} did not start within {timeout} seconds")
        print(f"⚠️  {name} did not start within {timeout} seconds")
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
            if not self.wait_for_service("neo4j", timeout=120):  # 2 minutes timeout
                services_ready = False
            
            # Then check Qdrant
            if services_ready and not self.wait_for_service("qdrant", timeout=60):
                services_ready = False
            
            if not services_ready:
                logger.error("Some Docker services failed to start")
                print("❌ Some Docker services failed to start")
                self.stop_services()
                sys.exit(1)
                
            # Give Neo4j extra time to complete initialization
            print("✅ Docker services started, waiting for full initialization...")
            time.sleep(30)  # Increased from 20s to 30s
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error starting Docker services: {e}")
            print(f"❌ Error starting Docker services: {e}")
            sys.exit(1)

    def check_lmstudio(self):
        """Check if LMStudio is running."""
        print("\n🤖 Checking LMStudio...")
        if self.check_service("lmstudio", self.services["lmstudio"]["health_url"]):
            print("✅ LMStudio is running")
            return True
        else:
            logger.error("LMStudio is not running")
            print("❌ LMStudio is not running")
            print("Please:")
            print("1. Open LMStudio application")
            print("2. Load your preferred model")
            print("3. Start the local server")
            return False

    def start_celery(self):
        """Start Celery worker."""
        print("\n🌾 Starting Celery worker...")
        try:
            # Stop any existing celery workers first
            self.stop_celery()
            time.sleep(2)  # Give time for cleanup
            
            # Wait for Redis to be ready
            if not self.wait_for_redis():
                logger.error("Cannot start Celery without Redis")
                print("❌ Cannot start Celery without Redis")
                sys.exit(1)
            
            # Set up environment with debug flags
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd().parent)
            env["LOG_LEVEL"] = "DEBUG"
            env["UVICORN_LOG_LEVEL"] = "debug"
            env["PYTHONUNBUFFERED"] = "1"
            env["C_FORCE_ROOT"] = "true"  # Allow running as root (for Docker)
            
            # Create logs directory
            logs_dir = Path("logs/celery")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up log files
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            stdout_log = logs_dir / f"celery-{timestamp}.out"
            stderr_log = logs_dir / f"celery-{timestamp}.err"
            
            # Start Celery worker with working command
            env["PYTHONPATH"] = str(Path.cwd().parent)
            celery_cmd = ["celery", "-A", "nia.nova.core.celery_app", "worker", "--loglevel=info"]
            
            # Open log files
            with open(stdout_log, 'w') as stdout, open(stderr_log, 'w') as stderr:
                process = subprocess.Popen(
                    celery_cmd,
                    env=env,
                    stdout=stdout,
                    stderr=stderr,
                    cwd=str(Path.cwd())  # Ensure correct working directory
                )
            
            logger.info(f"Started Celery worker (PID: {process.pid})")
            logger.info(f"Stdout log: {stdout_log}")
            logger.info(f"Stderr log: {stderr_log}")
            
            # Check for immediate startup errors
            time.sleep(2)
            if process.poll() is not None:
                with open(stderr_log) as f:
                    error = f.read()
                logger.error(f"Celery worker failed to start:\n{error}")
                print(f"❌ Celery worker failed to start:\n{error}")
                sys.exit(1)
                
            # Wait for worker to be responsive
            start_time = time.time()
            while time.time() - start_time < 30:  # 30 second timeout
                try:
                    # Check if worker process is still running
                    if process.poll() is not None:
                        with open(stderr_log) as f:
                            error = f.read()
                        logger.error(f"Celery worker stopped unexpectedly:\n{error}")
                        print(f"❌ Celery worker stopped unexpectedly:\n{error}")
                        sys.exit(1)
                    
                    # Check if worker is responding using our status check
                    status = celery_app.send_task('nova.check_status').get(timeout=5.0)
                    if not status:
                        continue
                    celery_status = status.get('celery', {})
                    if (celery_status.get('active') and 
                        celery_status.get('workers') and 
                        celery_status['workers'][0]['status'] == 'active'):
                        logger.info("Celery worker started and responding")
                        print("✅ Celery worker started and responding")
                        return
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Ping error: {e}")
                time.sleep(2)
            
            logger.error("Celery worker started but not properly connected")
            print("❌ Celery worker started but not properly connected")
            sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error starting Celery worker: {e}")
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
            # Set up environment with debug flags
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd().parent)
            env["LOG_LEVEL"] = "DEBUG"
            env["UVICORN_LOG_LEVEL"] = "debug"
            env["PYTHONUNBUFFERED"] = "1"
            
            # Create logs directory
            logs_dir = Path("logs/fastapi")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up log files
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            stdout_log = logs_dir / f"fastapi-{timestamp}.out"
            stderr_log = logs_dir / f"fastapi-{timestamp}.err"
            
            # Start FastAPI server with uvicorn
            server_cmd = [
                "python", "-m", "uvicorn",
                "nia.nova.core.app:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--log-level", "debug"
            ]
            
            # Open log files
            with open(stdout_log, 'w') as stdout, open(stderr_log, 'w') as stderr:
                process = subprocess.Popen(
                    server_cmd,
                    env=env,
                    stdout=stdout,
                    stderr=stderr,
                    cwd=str(Path.cwd())  # Ensure correct working directory
                )
            
            logger.info(f"Started FastAPI server (PID: {process.pid})")
            logger.info(f"Stdout log: {stdout_log}")
            logger.info(f"Stderr log: {stderr_log}")
            
            # Check for immediate startup errors
            time.sleep(2)
            if process.poll() is not None:
                with open(stderr_log) as f:
                    error = f.read()
                logger.error(f"FastAPI failed to start:\n{error}")
                print(f"❌ FastAPI failed to start:\n{error}")
                sys.exit(1)
                
            # Wait for server to be ready with longer timeout
            if not self.wait_for_service("fastapi", timeout=120):  # Double timeout for FastAPI
                # Check logs for errors
                with open(stderr_log) as f:
                    error = f.read()
                logger.error(f"FastAPI server failed to respond. Logs:\n{error}")
                print(f"❌ FastAPI server failed to respond. Check logs for details.")
                self.stop_fastapi()
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error starting FastAPI server: {e}")
            print(f"❌ Error starting FastAPI server: {e}")
            sys.exit(1)

    def start_frontend(self):
        """Start frontend development server."""
        print("\n🎨 Starting frontend server...")
        try:
            frontend_path = Path.cwd() / "frontend"
            
            # Check and install dependencies first
            if not self.check_frontend_deps():
                sys.exit(1)
            
            # Kill any existing Vite processes
            subprocess.run(["pkill", "-f", "vite"], check=False)
            
            # Set up environment with explicit port
            env = os.environ.copy()
            env["PORT"] = "5173"  # Ensure consistent port
            
            # Create logs directory
            logs_dir = Path("logs/frontend")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up log files
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            stdout_log = logs_dir / f"frontend-{timestamp}.out"
            stderr_log = logs_dir / f"frontend-{timestamp}.err"
            
            # Start frontend server with managed script
            with open(stdout_log, 'w') as stdout, open(stderr_log, 'w') as stderr:
                process = subprocess.Popen(
                    ["npm", "run", "dev:managed"],
                    env=env,
                    stdout=stdout,
                    stderr=stderr,
                    cwd=str(frontend_path)
                )
            
            logger.info(f"Started frontend server (PID: {process.pid})")
            logger.info(f"Stdout log: {stdout_log}")
            logger.info(f"Stderr log: {stderr_log}")
            
            # Check for immediate startup errors
            time.sleep(2)  # Give more time for startup
            if process.poll() is not None:
                with open(stderr_log) as f:
                    error = f.read()
                logger.error(f"Frontend server failed to start:\n{error}")
                print(f"❌ Frontend server failed to start:\n{error}")
                sys.exit(1)
            
            # Wait for server with proper health check
            start_time = time.time()
            while time.time() - start_time < 30:
                try:
                    response = requests.get(self.services["frontend"]["health_url"])
                    if response.status_code < 400:  # Accept 2xx or 3xx as success
                        logger.info("Frontend server started")
                        print("✅ Frontend server started")
                        return
                except requests.exceptions.ConnectionError:
                    pass
                time.sleep(1)
            
            logger.error("Frontend server failed to respond")
            print("❌ Frontend server failed to respond")
            self.stop_frontend()
            sys.exit(1)
            
        except Exception as e:
            logger.error(f"Error starting frontend server: {e}")
            print(f"❌ Error starting frontend server: {e}")
            self.stop_frontend()
            sys.exit(1)

    def stop_celery(self):
        """Stop Celery worker."""
        print("Stopping Celery worker...")
        try:
            subprocess.run(["pkill", "-f", "celery worker"], check=False)
        except Exception as e:
            logger.warning(f"Error stopping Celery worker: {e}")
            print(f"Warning: Error stopping Celery worker: {e}")

    def stop_fastapi(self):
        """Stop FastAPI server."""
        try:
            # Kill any uvicorn process running our FastAPI server
            subprocess.run(["pkill", "-f", "uvicorn.*nia.nova.core"], check=False)
            time.sleep(1)  # Give time for the process to fully stop
        except Exception as e:
            logger.warning(f"Error stopping FastAPI: {e}")
            print(f"Warning: Error stopping FastAPI: {e}")

    def stop_frontend(self):
        """Stop frontend server."""
        try:
            subprocess.run(["pkill", "-f", "vite"], check=False)
        except Exception as e:
            logger.warning(f"Error stopping frontend: {e}")
            print(f"Warning: Error stopping frontend: {e}")

    def stop_services(self):
        """Stop all services."""
        print("\n🛑 Stopping services...")
        
        # Stop all processes
        processes = [
            "uvicorn.*nia.nova.core",  # FastAPI (any module)
            "celery worker",           # Celery
            "vite",                    # Frontend
            "redis-server"             # Redis
        ]
        
        for process in processes:
            try:
                subprocess.run(["pkill", "-f", process], check=False)
            except Exception as e:
                logger.warning(f"Error stopping {process}: {e}")
                print(f"Warning: Error stopping {process}: {e}")
        
        # Stop Docker services
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.docker_compose_file, "down"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping Docker services: {e}")
            print(f"Error stopping Docker services: {e}")
            sys.exit(1)
        
        print("✅ All services stopped")

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
        status = "✅ Running" if self.check_service("celery", None) else "❌ Not running"
        print(f"Celery Worker: {status}")

    def check_dependencies(self):
        """Check if required Python packages are installed."""
        try:
            import uvicorn
            import fastapi
            import tinytroupe
            return True
        except ImportError as e:
            logger.error(f"Missing dependencies: {e}")
            print(f"❌ Missing dependencies: {e}")
            print("Please run: pdm install")
            return False

    def check_tinytroupe_config(self):
        """Check TinyTroupe configuration."""
        site_packages_config = Path(Path.cwd().parent / ".venv/lib/python3.12/site-packages/tinytroupe/config.ini")
        print(f"Looking for default config on: {site_packages_config}")
        custom_config = Path(Path.cwd().parent / "config.ini")
        
        print("\n🔍 Checking TinyTroupe configuration...")
        logger.info(f"Site packages config: {site_packages_config.absolute()}")
        logger.info(f"Custom config: {custom_config.absolute()}")
        print(f"Site packages config: {site_packages_config.absolute()}")
        print(f"Custom config: {custom_config.absolute()}")
        
        # Try to read configs to verify they're valid
        configs_valid = False
        
        if site_packages_config.exists() and site_packages_config.is_file():
            try:
                with open(site_packages_config) as f:
                    content = f.read()
                    if "[DEFAULT]" in content and "[MEMORY]" in content and "[WORKSPACES]" in content:
                        print("✅ Site packages config is valid")
                        configs_valid = True
                    else:
                        logger.warning("Site packages config is invalid")
                        print("⚠️  Site packages config is invalid")
            except Exception as e:
                logger.error(f"Error reading site packages config: {e}")
                print(f"⚠️  Error reading site packages config: {e}")
        
        if custom_config.exists() and custom_config.is_file():
            print(f"Found custom config on: {custom_config}")
            try:
                with open(custom_config) as f:
                    content = f.read()
                    if "[DEFAULT]" in content and "[MEMORY]" in content and "[WORKSPACES]" in content:
                        print("✅ Custom config is valid")
                        configs_valid = True
                    else:
                        logger.warning("Custom config is invalid")
                        print("⚠️  Custom config is invalid")
            except Exception as e:
                logger.error(f"Error reading custom config: {e}")
                print(f"⚠️  Error reading custom config: {e}")
        else:
            print(f"Failed to find custom config on: {custom_config}")
        
        if not configs_valid:
            logger.warning("No valid TinyTroupe configuration found")
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
                logger.info(f"Created default config.ini at {custom_config.absolute()}")
                print(f"✅ Created default config.ini at {custom_config.absolute()}")
                print("Please customize if needed, especially:")
                print("- model_api_type")
                print("- model_api_base")
                print("- model_name")
            except Exception as e:
                logger.error(f"Failed to create config.ini: {e}")
                print(f"❌ Failed to create config.ini: {e}")
                sys.exit(1)

    def wait_for_redis(self, timeout=30):
        """Wait for Redis to be fully ready."""
        print("⏳ Waiting for Redis to be ready...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service("redis", None):
                print("✅ Redis is ready")
                return True
            time.sleep(1)
        logger.error("Redis failed to become ready")
        print("❌ Redis failed to become ready")
        return False

    def check_frontend_deps(self):
        """Check and install frontend dependencies."""
        frontend_path = Path.cwd() / "frontend"
        node_modules = frontend_path / "node_modules"
        
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    check=True,
                    cwd=str(frontend_path),
                    capture_output=True,
                    text=True
                )
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install frontend dependencies:\n{e.stderr}")
                print(f"❌ Failed to install frontend dependencies:\n{e.stderr}")
                return False
        return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NIA service management")
    parser.add_argument("command", choices=["clean", "start", "stop", "status"], help="Command to execute")
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.command == "start":
        manager.start_docker_services()
        manager.check_lmstudio()
        manager.start_celery()
        manager.start_fastapi()
        manager.start_frontend()
        manager.show_status()
    elif args.command == "stop":
        manager.stop_services()
    elif args.command == "status":
        manager.show_status()

if __name__ == "__main__":
    main()
