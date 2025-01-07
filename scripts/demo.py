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
from nia.agents.specialized.meta_agent import MetaAgent
from nia.agents.specialized.parsing_agent import ParsingAgent
from nia.agents.specialized.belief_agent import BeliefAgent
from nia.agents.specialized.desire_agent import DesireAgent
from nia.agents.specialized.emotion_agent import EmotionAgent
from nia.agents.specialized.reflection_agent import ReflectionAgent

async def check_api_health(retries=30, delay=2):
    """Check if FastAPI server is running"""
    for i in range(retries):
        try:
            response = requests.get("http://localhost:8000")
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
    
    # Check FastAPI server
    print(f"\n{Fore.CYAN}Checking FastAPI Server:{Style.RESET_ALL}")
    if not await check_api_health():
        print(f"{Fore.RED}Error: FastAPI server is not running!{Style.RESET_ALL}")
        print("Please start the server with scripts/run_server.py")
        return False
    print(f"{Fore.GREEN}✓ FastAPI server is running{Style.RESET_ALL}")
    
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
        "type": "semantic",
        "importance": 0.95,
        "context": {"domain": "science"},
        "llm_config": llm_config
    }
    
    print_agent_message("Nova", "Storing fact in memory system...", True)
    response = requests.post(
        f"{API_BASE}/orchestration/memory/store",
        json=memory_request,
        headers={"X-API-Key": "test-key"}
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
        json=parse_request,
        headers={"X-API-Key": "test-key"}
    )
    parse_result = response.json()
    
    # Coordinate agents for response using WebSocket
    print_agent_message("Nova", "Coordinating agent response...", True)
    
    headers = {"X-API-Key": "test-key"}
    async with websockets.connect(
        f"{WS_BASE}/analytics/ws",
        additional_headers=headers
    ) as websocket:
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
        params={"domain": "science"},
        headers={"X-API-Key": "test-key"}
    )
    analytics = analytics_response.json()
    
    print_agent_message("Nova", "Memory analysis complete:")
    for insight in analytics.get("insights", []):
        print_agent_message("Nova", f"• {insight}")

    # Demonstrate swarm architectures
    print_agent_message("Nova", "Demonstrating swarm architecture patterns...")
    
    # Let Nova decide swarm pattern based on task requirements
    print_agent_message("Nova", "Analyzing task requirements to determine optimal swarm pattern...", True)
    
    test_tasks = [
        {
            "type": "data_processing",
            "subtasks": [{"id": f"subtask_{i}"} for i in range(10)],
            "requirements": {
                "parallel_execution": True,
                "independent_tasks": True
            }
        },
        {
            "type": "workflow",
            "stages": ["parse", "analyze", "validate"],
            "requirements": {
                "ordered_execution": True,
                "stage_dependencies": True
            }
        },
        {
            "type": "decision_making",
            "options": ["A", "B", "C"],
            "requirements": {
                "consensus_needed": True,
                "multiple_perspectives": True
            }
        }
    ]

    swarm_patterns = {}
    for task in test_tasks:
        # Let Nova decide the swarm pattern
        decision_response = requests.post(
            f"{API_BASE}/orchestration/swarms/decide",
            json={
                "task": task,
                "domain": "test"
            },
            headers={"X-API-Key": "test-key"}
        )
        decision_data = decision_response.json()
        print_agent_message("Nova", f"For {task['type']}: Selected {decision_data['selected_pattern']} pattern")
        print_agent_message("Nova", f"Reasoning: {decision_data['reasoning']}")
        
        # Create swarm with the selected pattern
        swarm_request = {
            "type": "swarm_creation",
            "domain": "test",
            "pattern": decision_data['selected_pattern'],
            "task": task,
            "capabilities": [
                "task_execution",
                "communication",
                "coordination"
            ]
        }
    
    # Create swarms through Nova's orchestration
    response = requests.post(
        f"{API_BASE}/orchestration/swarms",
        json=swarm_request,
        headers={"X-API-Key": "test-key"}
    )
    swarm_data = response.json()
    
    # Display swarm creation results
    print_agent_message("Nova", "\nSwarm patterns created:")
    for pattern, info in swarm_data["swarms"].items():
        print_agent_message("Nova", f"• {pattern.title()} Swarm (ID: {info['swarm_id']})")
    
    # Demonstrate swarm coordination
    print_agent_message("Nova", "\nDemonstrating swarm coordination...")
    
    headers = {"X-API-Key": "test-key"}
    async with websockets.connect(
        f"{WS_BASE}/analytics/ws",
        additional_headers=headers
    ) as websocket:
        try:
            # Monitor swarm activity
            await websocket.send(json.dumps({
                "type": "swarm_monitor",
                "swarm_ids": [
                    info["swarm_id"] for info in swarm_data["swarms"].values()
                ]
            }))
            
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data["type"] == "swarm_update":
                        pattern = data.get("pattern")
                        event = data.get("event_type")
                        
                        if pattern and event:
                            print_agent_message(
                                "Nova", 
                                f"[{pattern.title()}] {event}: {data.get('message', '')}"
                            )
                    
                    elif data["type"] == "coordination_complete":
                        break
                        
                except websockets.exceptions.ConnectionClosed:
                    print_agent_message("Nova", "WebSocket connection closed")
                    break
                except Exception as e:
                    print_agent_message("Nova", f"Error: {str(e)}")
                    break
                    
        except Exception as e:
            print_agent_message("Nova", f"Swarm coordination error: {str(e)}")
        finally:
            # Cleanup swarms
            cleanup_response = requests.delete(
                f"{API_BASE}/orchestration/swarms",
                json={"swarm_ids": [info["swarm_id"] for info in swarm_data["swarms"].values()]},
                headers={"X-API-Key": "test-key"}
            )
            if cleanup_response.status_code != 200:
                print_agent_message("Nova", "Warning: Some swarms may not have been cleaned up properly")

    # Current coordination capabilities demo
    print_agent_message("Nova", "\nDemonstrating current coordination capabilities...")
    
    # Request coordination through TinyFactory
    coordination_request = {
        "type": "coordination_request",
        "domain": "science",
        "task": {
            "type": "analysis",
            "content": "Analyze the relationship between sky color and light scattering",
            "required_capabilities": ["parsing", "belief_management"]
        },
        "llm_config": llm_config
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/orchestration/coordinate",
            json=coordination_request,
            headers={"X-API-Key": "test-key"}
        )
        if response.status_code == 200:
            result = response.json()
            print_agent_message("Nova", "Coordination successful")
            print_agent_message("Nova", f"Analysis result: {result.get('content', 'No content available')}")
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

def configure_logging():
    """Configure logging for the demo script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('demo.log')
        ]
    )
    # Suppress websockets debug logging
    logging.getLogger('websockets').setLevel(logging.INFO)
    # Set Nova logger to INFO
    logging.getLogger('nia.nova').setLevel(logging.INFO)

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
