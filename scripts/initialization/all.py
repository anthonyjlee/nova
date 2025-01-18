#!/usr/bin/env python3
"""Master initialization script to coordinate all system components."""

import asyncio
import sys
import os
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Any, Dict, Optional

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from scripts.memory.initialize_memory import MemoryInitializer
from scripts.tasks.initialize_tasks import TaskInitializer
from scripts.websocket.initialize_websocket import WebSocketInitializer
from scripts.chat.initialize_chat import ChatInitializer
from scripts.users.initialize_users import UserInitializer
from src.nia.core.neo4j.base_store import Neo4jBaseStore
from src.nia.core.types.memory_types import BaseDomain
from src.nia.agents.base import BaseAgent
from src.nia.world.environment import NIAWorld
from src.nia.memory.two_layer import TwoLayerMemorySystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version."""
    logger.info("Checking Python version...")
    if sys.version_info < (3, 9):
        logger.error("Error: Python 3.9 or higher is required")
        sys.exit(1)
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_docker():
    """Check Docker installation."""
    logger.info("Checking Docker installation...")
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        logger.info("Docker is installed")
    except FileNotFoundError:
        logger.error("Docker not found. Please install Docker first:")
        logger.error("Visit: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    logger.info("Checking Docker Compose installation...")
    try:
        subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
        logger.info("Docker Compose is installed")
    except subprocess.CalledProcessError:
        logger.error("Docker Compose not found. Please install Docker Compose first:")
        logger.error("Visit: https://docs.docker.com/compose/install/")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    logger.info("Creating directories...")
    directories = [
        "logs",
        "data",
        "visualizations"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

def setup_env():
    """Set up environment configuration."""
    logger.info("Setting up environment configuration...")
    
    # Create .env file with Neo4j credentials
    env_path = Path(".env")
    if not env_path.exists():
        logger.info("Creating .env file with Neo4j credentials...")
        with open(env_path, "w") as f:
            f.write("""# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password  # Change this in production
""")
        logger.info(".env file created")
    else:
        logger.info(".env file already exists")

class SystemInitializer(Neo4jBaseStore):
    """Initialize all system components in the correct order."""
    
    def __init__(self):
        """Initialize system components."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        self.logger = logging.getLogger("system_init")
        
    async def _initialize_base_agents(
        self,
        world: NIAWorld,
        memory_system: TwoLayerMemorySystem
    ) -> List[BaseAgent]:
        """Initialize base agents."""
        base_agents = []
        
        # Create base agent
        base_agent = await BaseAgent.create(
            name="BaseAgent",
            agent_type="base",
            memory_system=memory_system,
            world=world,
            attributes={
                "type": "base",
                "workspace": "system",
                "domain": BaseDomain.GENERAL
            }
        )
        base_agents.append(base_agent)
        
        return base_agents
        
    async def _initialize_emotional_states(self, agents: List[BaseAgent]):
        """Initialize emotional states for agents."""
        for agent in agents:
            await self.run_query(
                """
                MATCH (a:Agent {name: $name})
                SET a.emotions = $emotions
                """,
                {
                    "name": agent.name,
                    "emotions": {
                        "task_focus": "neutral",
                        "collaboration_readiness": "active",
                        "domain_confidence": "high"
                    }
                }
            )
            
    async def _initialize_tinytroupe(self, agents: List[BaseAgent], world: NIAWorld):
        """Initialize TinyTroupe integration."""
        for agent in agents:
            if not agent:
                continue
                
            # Add TinyTroupe capabilities
            await self.run_query(
                """
                MATCH (a:Agent {name: $name})
                SET a.capabilities = $capabilities
                """,
                {
                    "name": agent.name,
                    "capabilities": [
                        "emotional_processing",
                        "goal_management",
                        "world_interaction"
                    ]
                }
            )
            
            # Initialize in world
            world.add_agent(agent.name, agent)
            
    async def _initialize_meta_agent(
        self,
        world: NIAWorld,
        memory_system: TwoLayerMemorySystem
    ) -> BaseAgent:
        """Initialize meta agent."""
        meta_agent = await BaseAgent.create(
            name="MetaAgent",
            agent_type="meta",
            memory_system=memory_system,
            world=world,
            attributes={
                "type": "meta",
                "workspace": "system",
                "domain": BaseDomain.GENERAL,
                "capabilities": [
                    "team_coordination",
                    "task_distribution",
                    "cognitive_oversight"
                ]
            }
        )
        return meta_agent
        
    async def _initialize_core_agents(
        self,
        world: NIAWorld,
        memory_system: TwoLayerMemorySystem,
        meta_agent: BaseAgent
    ) -> List[BaseAgent]:
        """Initialize core cognitive agents."""
        core_agents = []
        
        # Create belief agent
        belief_agent = await BaseAgent.create(
            name="BeliefAgent",
            agent_type="belief",
            memory_system=memory_system,
            world=world,
            attributes={
                "type": "belief",
                "workspace": "system",
                "domain": BaseDomain.GENERAL
            }
        )
        core_agents.append(belief_agent)
        
        # Create desire agent
        desire_agent = await BaseAgent.create(
            name="DesireAgent",
            agent_type="desire",
            memory_system=memory_system,
            world=world,
            attributes={
                "type": "desire",
                "workspace": "system",
                "domain": BaseDomain.GENERAL
            }
        )
        core_agents.append(desire_agent)
        
        # Create emotion agent
        emotion_agent = await BaseAgent.create(
            name="EmotionAgent",
            agent_type="emotion",
            memory_system=memory_system,
            world=world,
            attributes={
                "type": "emotion",
                "workspace": "system",
                "domain": BaseDomain.GENERAL
            }
        )
        core_agents.append(emotion_agent)
        
        # Set up relationships with meta agent
        for agent in core_agents:
            await self.run_query(
                """
                MATCH (m:Agent {name: $meta_name})
                MATCH (a:Agent {name: $agent_name})
                MERGE (m)-[:COORDINATES]->(a)
                """,
                {
                    "meta_name": meta_agent.name,
                    "agent_name": agent.name
                }
            )
        
        return core_agents
        
    async def initialize(self):
        """Initialize all components in sequence."""
        try:
            # 1. Initialize Memory System (foundation)
            self.logger.info("Initializing Memory System...")
            memory_init = MemoryInitializer()
            await memory_init.initialize()
            self.logger.info("Memory System initialized successfully")
            
            # 2. Initialize TinyWorld Environment
            self.logger.info("Initializing TinyWorld Environment...")
            # Initialize world with memory system
            world = NIAWorld(
                name="NIAWorld",
                memory_system=memory_init.memory_system
            )
            self.logger.info("TinyWorld Environment initialized successfully")
            
            # 3. Initialize Base Agents
            self.logger.info("Initializing Base Agents...")
            # BaseAgent components
            base_agents = await self._initialize_base_agents(world, memory_init.memory_system)
            # TinyPerson emotional states
            await self._initialize_emotional_states(base_agents)
            # TinyTroupe integration
            await self._initialize_tinytroupe(base_agents, world)
            self.logger.info("Base Agents initialized successfully")
            
            # 4. Initialize Core Cognitive Agents
            self.logger.info("Initializing Core Cognitive Agents...")
            # Meta agent first (coordinates others)
            meta_agent = await self._initialize_meta_agent(world, memory_init.memory_system)
            # Other core agents
            core_agents = await self._initialize_core_agents(world, memory_init.memory_system, meta_agent)
            self.logger.info("Core Cognitive Agents initialized successfully")
            
            # 5. Initialize User Management System (required by other systems)
            self.logger.info("Initializing User Management System...")
            user_init = UserInitializer()
            await user_init.initialize()
            self.logger.info("User Management System initialized successfully")
            
            # 6. Initialize Task System (depends on user rules)
            self.logger.info("Initializing Task System...")
            task_init = TaskInitializer()
            await task_init.initialize()
            self.logger.info("Task System initialized successfully")
            
            # 7. Initialize Chat System (depends on user preferences and tasks)
            self.logger.info("Initializing Chat System...")
            chat_init = ChatInitializer()
            await chat_init.initialize()  # Chat system gets agents from world
            self.logger.info("Chat System initialized successfully")
            
            # 8. Initialize WebSocket System (depends on all other systems)
            self.logger.info("Initializing WebSocket System...")
            websocket_init = WebSocketInitializer()
            await websocket_init.initialize()
            self.logger.info("WebSocket System initialized successfully")
            
            self.logger.info("All systems initialized successfully")
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            raise
            
    async def verify_initialization(self):
        """Verify all systems are properly initialized."""
        try:
            self.logger.info("Verifying system initialization...")
            
            # 1. Verify Memory System
            self.logger.info("Verifying Memory System...")
            memory_init = MemoryInitializer()
            await memory_init.connect()
            await memory_init.vector_store.connect()
            self.logger.info("Memory System verification successful")
            
            # 2. Verify TinyWorld Environment
            self.logger.info("Verifying TinyWorld Environment...")
            world = NIAWorld()
            if not world._initialized:
                raise Exception("TinyWorld not properly initialized")
            self.logger.info("TinyWorld Environment verification successful")
            
            # 3. Verify Base Agents
            self.logger.info("Verifying Base Agents...")
            result = await self.run_query(
                """
                MATCH (a:Agent)
                WHERE a.type = 'base'
                RETURN count(a) as count
                """
            )
            if result[0]["count"] < 1:
                raise Exception("Base agents not properly initialized")
            self.logger.info("Base Agents verification successful")
            
            # 4. Verify Core Cognitive Agents
            self.logger.info("Verifying Core Cognitive Agents...")
            result = await self.run_query(
                """
                MATCH (a:Agent)
                WHERE a.type IN ['meta', 'belief', 'desire', 'emotion']
                RETURN count(a) as count
                """
            )
            if result[0]["count"] < 4:  # Meta + 3 core cognitive agents
                raise Exception("Core cognitive agents not properly initialized")
            self.logger.info("Core Cognitive Agents verification successful")
            
            # 5. Verify Support Systems
            # User Management System
            self.logger.info("Verifying User Management System...")
            user_init = UserInitializer()
            await user_init.connect()
            result = await user_init.run_query(
                """
                MATCH (t:ProfileTemplate)
                WHERE t.name = 'default'
                RETURN count(t) as count
                """
            )
            if result[0]["count"] < 1:
                raise Exception("User profile templates not properly initialized")
            self.logger.info("User Management System verification successful")
            
            # Task System
            self.logger.info("Verifying Task System...")
            task_init = TaskInitializer()
            await task_init.connect()
            result = await task_init.run_query(
                """
                MATCH (s:TaskState)
                RETURN count(s) as count
                """
            )
            if result[0]["count"] < 4:
                raise Exception("Task states not properly initialized")
            self.logger.info("Task System verification successful")
            
            # Chat System
            self.logger.info("Verifying Chat System...")
            chat_init = ChatInitializer()
            await chat_init.connect()
            result = await chat_init.run_query(
                """
                MATCH (a:Agent)
                WHERE a.type = 'system'
                RETURN count(a) as count
                """
            )
            if result[0]["count"] < 2:
                raise Exception("System agents not properly initialized")
            self.logger.info("Chat System verification successful")
            
            # WebSocket System
            self.logger.info("Verifying WebSocket System...")
            websocket_init = WebSocketInitializer()
            await websocket_init.connect()
            result = await websocket_init.run_query(
                """
                MATCH (e:WebSocketEndpoint)
                RETURN count(e) as count
                """
            )
            if result[0]["count"] < 2:
                raise Exception("WebSocket endpoints not properly initialized")
            self.logger.info("WebSocket System verification successful")
            
            self.logger.info("All systems verified successfully")
            
        except Exception as e:
            self.logger.error(f"System verification failed: {str(e)}")
            raise

async def main():
    """Main entry point."""
    try:
        # Check system requirements
        check_python_version()
        check_docker()
        
        # Create required directories
        create_directories()
        
        # Set up environment
        setup_env()
        
        # Initialize all systems
        initializer = SystemInitializer()
        await initializer.initialize()
        
        # Verify initialization
        await initializer.verify_initialization()
        
        logger.info("\nSetup complete! You can now:")
        logger.info("1. Access Neo4j browser at http://localhost:7474")
        logger.info("2. Connect using:")
        logger.info("   - URL: bolt://localhost:7687")
        logger.info("   - Username: neo4j")
        logger.info("   - Password: password")
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
