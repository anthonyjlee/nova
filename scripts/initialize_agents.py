"""Initialize default agents in the store."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.memory.agent_store import AgentStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_agents():
    """Initialize default agents in the store."""
    try:
        agent_store = AgentStore()
        
        # Default agents
        default_agents = [
            {
                "id": "nova-team",
                "name": "NovaTeam",
                "type": "nova",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "type": "agent-team",
                    "system": True,
                    "pinned": True,
                    "description": "This is where NOVA and core agents collaborate."
                }
            },
            {
                "id": "belief-agent-1",
                "name": "BeliefAgent",
                "type": "belief",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["belief_analysis", "context_understanding"]
                }
            },
            {
                "id": "desire-agent-1",
                "name": "DesireAgent",
                "type": "desire",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["goal_tracking", "intention_analysis"]
                }
            },
            {
                "id": "emotion-agent-1",
                "name": "EmotionAgent",
                "type": "emotion",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["sentiment_analysis", "emotion_detection"]
                }
            }
        ]
        
        # Store each agent
        for agent in default_agents:
            logger.info(f"Storing agent: {agent['name']}")
            success = await agent_store.store_agent(agent)
            if success:
                logger.info(f"Successfully stored agent: {agent['name']}")
            else:
                logger.error(f"Failed to store agent: {agent['name']}")
                
        # Verify agents were stored
        all_agents = await agent_store.get_all_agents()
        logger.info(f"Total agents in store: {len(all_agents)}")
        for agent in all_agents:
            logger.info(f"Found agent: {agent['name']}")
            
    except Exception as e:
        logger.error(f"Error initializing agents: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_agents())
