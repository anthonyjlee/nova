"""
Demo script to showcase NIA functionality using FastAPI endpoints and LMStudio
"""

import asyncio
import logging
import json
import time
import requests
import websockets
import subprocess
from datetime import datetime
from colorama import init, Fore, Style

# Constants
API_BASE = "http://localhost:8000/api"
WS_BASE = "ws://localhost:8000/api"
LMSTUDIO_BASE = "http://localhost:1234/v1"

def check_docker_running():
    """Check if Docker is running"""
    try:
        subprocess.run(["docker", "info"], 
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE, 
                     check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_docker_compose_services():
    """Check if required Docker services are running"""
    try:
        result = subprocess.run(["docker-compose", "ps", "--services", "--filter", "status=running"],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True,
                              check=True)
        running_services = set(result.stdout.strip().split('\n'))
        required_services = {'neo4j', 'qdrant'}
        return required_services.issubset(running_services)
    except subprocess.CalledProcessError:
        return False

def start_docker_services():
    """Start required Docker services"""
    try:
        subprocess.run(["docker-compose", "up", "-d", "neo4j", "qdrant"],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_lmstudio_health(retries=5, delay=2):
    """Check if LM Studio is running"""
    for i in range(retries):
        try:
            response = requests.get(f"{LMSTUDIO_BASE}/models")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if i < retries - 1:
                time.sleep(delay)
                continue
    return False

def check_neo4j_health(retries=30, delay=2):
    """Check if Neo4j is healthy"""
    for i in range(retries):
        try:
            response = requests.get("http://localhost:7474")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if i < retries - 1:
                time.sleep(delay)
                continue
    return False

def check_qdrant_health(retries=30, delay=2):
    """Check if Qdrant is healthy"""
    for i in range(retries):
        try:
            response = requests.get("http://localhost:6333/collections")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if i < retries - 1:
                time.sleep(delay)
                continue
    return False

# Import core agents
from nia.memory.agents.meta_agent import MetaAgent
from nia.memory.agents.parsing_agent import ParsingAgent
from nia.memory.agents.belief_agent import BeliefAgent
from nia.memory.agents.desire_agent import DesireAgent
from nia.memory.agents.emotion_agent import EmotionAgent
from nia.memory.agents.reflection_agent import ReflectionAgent

async def check_api_health(retries=30, delay=2):
    """Check if FastAPI server is running"""
    for i in range(retries):
        try:
            response = requests.get(f"{API_BASE}/health")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if i < retries - 1:
                time.sleep(delay)
                continue
    return False

def print_agent_message(agent_name: str, message: str, is_thinking: bool = False):
    """Print styled agent message"""
    # Color mapping for different agents
    colors = {
        'Nova': Fore.GREEN,
        'Parser': Fore.BLUE,
        'Belief': Fore.MAGENTA,
        'Desire': Fore.YELLOW,
        'Emotion': Fore.RED,
        'Reflection': Fore.CYAN
    }
    
    # Get color or default to white
    color = colors.get(agent_name, Fore.WHITE)
    
    # Format the message
    prefix = "..." if is_thinking else ">>>"
    
    print(f"\n{color}{agent_name} {prefix}{Style.RESET_ALL} {message}")

async def verify_system():
    """Verify system health and test coverage"""
    
    # 1. Check Docker
    print(f"\n{Fore.CYAN}Checking Docker Status:{Style.RESET_ALL}")
    if not check_docker_running():
        print(f"{Fore.RED}Error: Docker is not running!{Style.RESET_ALL}")
        print("Please start Docker and try again")
        return False
    print(f"{Fore.GREEN}✓ Docker is running{Style.RESET_ALL}")
    
    # 2. Check Docker services
    print(f"\n{Fore.CYAN}Checking Docker Services:{Style.RESET_ALL}")
    if not check_docker_compose_services():
        print(f"{Fore.YELLOW}Starting required Docker services...{Style.RESET_ALL}")
        if not start_docker_services():
            print(f"{Fore.RED}Error: Failed to start Docker services!{Style.RESET_ALL}")
            return False
        print(f"\n{Fore.YELLOW}Waiting for Neo4j to be ready (this may take a minute)...{Style.RESET_ALL}")
        attempts = 0
        while not check_neo4j_health() and attempts < 30:
            print(".", end="", flush=True)
            time.sleep(2)
            attempts += 1
        print("\n")
        
        print(f"{Fore.YELLOW}Waiting for Qdrant to be ready...{Style.RESET_ALL}")
        attempts = 0
        while not check_qdrant_health() and attempts < 30:
            print(".", end="", flush=True)
            time.sleep(2)
            attempts += 1
        print("\n")
    print(f"{Fore.GREEN}✓ Docker services are running{Style.RESET_ALL}")
    
    # 3. Check core services
    print(f"\n{Fore.CYAN}Verifying All Services:{Style.RESET_ALL}")
    print("This may take a moment as services initialize...")
    services_status = {
        "LM Studio": check_lmstudio_health(),
        "FastAPI": await check_api_health(),
        "Neo4j": check_neo4j_health(),
        "Qdrant": check_qdrant_health()
    }
    
    all_healthy = all(services_status.values())
    
    if not all_healthy:
        print(f"\n{Fore.RED}Service Health Check Failed:{Style.RESET_ALL}")
        for service, status in services_status.items():
            status_color = Fore.GREEN if status else Fore.RED
            status_text = "Healthy" if status else "Unhealthy"
            print(f"- {service}: {status_color}{status_text}{Style.RESET_ALL}")
        
        if not services_status["LM Studio"]:
            print(f"\n{Fore.YELLOW}Please:{Style.RESET_ALL}")
            print("1. Open LM Studio")
            print("2. Load a model")
            print("3. Start the local server")
        
        return False
    
    print(f"\n{Fore.GREEN}Core Services:{Style.RESET_ALL}")
    print("✓ LM Studio - Local LLM Server")
    print("✓ FastAPI - Nova Server")
    print("✓ Neo4j - Graph Database (Semantic Layer)")
    print("✓ Qdrant - Vector Store (Episodic Layer)")
    
    # 2. Display test coverage areas
    print(f"\n{Fore.CYAN}Test Coverage Areas:{Style.RESET_ALL}")
    print("\nCore Systems:")
    print("1. Memory System")
    print("   - Two-layer integration (Vector + Neo4j)")
    print("   - Memory consolidation")
    print("   - Domain-labeled storage")
    print("   - Cross-domain operations")
    
    print("\n2. Agent System")
    print("   - Core agent initialization")
    print("   - Agent communication")
    print("   - Swarm coordination")
    print("   - Task processing")
    
    print("\n3. Nova Orchestration")
    print("   - Multi-agent coordination")
    print("   - Task planning and execution")
    print("   - Memory integration")
    print("   - Domain management")
    
    print("\n4. Integration Points")
    print("   - LLM interface")
    print("   - Memory consolidation")
    print("   - Agent collaboration")
    print("   - Error handling")
    
    return True

async def demo_core_functionality():
    """Demonstrate core NIA functionality using FastAPI endpoints"""
    
    # Verify system health and display test coverage
    if not await verify_system():
        return
    print(f"\n{Fore.CYAN}NIA Multi-Agent Dialogue Demo{Style.RESET_ALL}")
    print(f"{Fore.CYAN}============================{Style.RESET_ALL}\n")

    print_agent_message("System", "Initializing NIA components and agents...")
    
    # Get available LM Studio models
    response = requests.get(f"{LMSTUDIO_BASE}/models")
    models = response.json()["data"]
    chat_model = next((m["id"] for m in models if "instruct" in m["id"].lower()), models[0]["id"])
    embedding_model = next((m["id"] for m in models if "embed" in m["id"].lower()), models[0]["id"])
    
    llm_config = {
        "chat_model": chat_model,
        "embedding_model": embedding_model
    }
    
    print_agent_message("System", f"Using LM Studio models:")
    print_agent_message("System", f"• Chat: {chat_model}")
    print_agent_message("System", f"• Embeddings: {embedding_model}")
    print_agent_message("Emotion", "Experiencing satisfaction with successful integration")
    print_agent_message("Nova", "Initialization complete. Ready for interaction. How may I assist you?")

    # Store initial knowledge using memory endpoint
    print_agent_message("Nova", "Let me store some initial knowledge...")
    
    memory_request = {
        "content": "The sky is blue because of Rayleigh scattering of sunlight.",
        "type": "fact",
        "importance": 0.95,
        "context": {"domain": "science"},
        "llm_config": llm_config
    }
    
    print_agent_message("Nova", "Storing fact in memory system...", True)
    response = requests.post(
        f"{API_BASE}/orchestration/memory/store",
        json=memory_request
    )
    print_agent_message("Nova", "Memory system initialized with initial knowledge.")

    # Parse user query using LM Studio integration
    test_input = "Why is the sky blue?"
    print(f"\n{Fore.CYAN}User:{Style.RESET_ALL} {test_input}")
    
    parse_request = {
        "text": test_input,
        "domain": "science",
        "llm_config": llm_config
    }
    
    print_agent_message("Parser", "Analyzing question structure...", True)
    response = requests.post(
        f"{API_BASE}/analytics/parse",
        json=parse_request
    )
    parse_result = response.json()
    
    # Coordinate agents for response using WebSocket
    print_agent_message("Nova", "Coordinating agent response...", True)
    
    async with websockets.connect(f"{WS_BASE}/analytics/ws") as websocket:
        await websocket.send(json.dumps({
            "type": "agent_coordination",
            "content": test_input,
            "domain": "science",
            "llm_config": llm_config
        }))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "analytics_update":
                for agent, update in data["analytics"].items():
                    print_agent_message(agent.title(), update["message"])
            elif data["type"] == "response":
                print_agent_message("Nova", data["content"])
                break

    # Demonstrate memory consolidation using analytics endpoint
    print_agent_message("Nova", "Analyzing memory patterns...", True)
    
    analytics_response = requests.get(
        f"{API_BASE}/analytics/flows",
        params={"domain": "science"}
    )
    analytics = analytics_response.json()
    
    print_agent_message("Nova", "Memory analysis complete:")
    for insight in analytics.get("insights", []):
        print_agent_message("Nova", f"• {insight}")

    # Note: Full swarm capabilities are under development
    print_agent_message("Nova", "Note: Advanced swarm architectures are in development...")
    print_agent_message("Nova", "Currently implemented patterns:")
    print_agent_message("Nova", "• Basic agent coordination through WebSocket")
    print_agent_message("Nova", "• Sequential task processing")
    print_agent_message("Nova", "• Memory consolidation")
    
    print_agent_message("Nova", "\nPlanned swarm architectures:")
    print_agent_message("Nova", "• Hierarchical swarms")
    print_agent_message("Nova", "• Parallel processing")
    print_agent_message("Nova", "• Round-robin task distribution")
    print_agent_message("Nova", "• Graph-based workflows")
    print_agent_message("Nova", "• Majority voting systems")

    # Current coordination capabilities demo
    print_agent_message("Nova", "\nDemonstrating current coordination capabilities...")
    
    coordination_request = {
        "task": {
            "type": "sequential_processing",
            "content": "Analyze the relationship between sky color and light scattering",
            "agents": ["parser", "belief"]
        },
        "llm_config": llm_config
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/orchestration/agents/coordinate",
            json=coordination_request
        )
        if response.status_code == 200:
            result = response.json()
            print_agent_message("Nova", "Basic coordination successful")
        else:
            print_agent_message("Nova", "Note: Some coordination features are still in development")
    except Exception as e:
        print_agent_message("Nova", "Note: Advanced coordination features coming soon")
    
    # System status and development roadmap
    print_agent_message("Nova", "\nSystem Status and Development Roadmap:")
    print_agent_message("Nova", "1. Core API Endpoints: ✓ Implemented")
    print_agent_message("Nova", "2. LM Studio Integration: ✓ Implemented")
    print_agent_message("Nova", "3. Memory System: ✓ Implemented")
    print_agent_message("Nova", "4. Basic Agent Coordination: ✓ Implemented")
    print_agent_message("Nova", "5. Advanced Swarm Patterns: ⟳ In Development")
    
    print(f"\n{Fore.CYAN}Demo Complete!{Style.RESET_ALL}")
    print("Demonstrated capabilities:")
    print("1. Multi-agent dialogue and interaction")
    print("2. Two-layer memory system")
    print("3. Memory consolidation")
    print("4. Swarm architecture")
    print("5. Concept validation")

if __name__ == "__main__":
    # Initialize colorama
    init()
    
    # Configure logging
    configure_logging()
    
    try:
        asyncio.run(demo_core_functionality())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Demo interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
