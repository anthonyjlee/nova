"""Test script for mobile interface."""

import os
import json
import asyncio
import logging
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))

from nia.ui.mobile import MobileUI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system1():
    """Test System-1 remote control functionality."""
    ui = MobileUI()
    
    try:
        # Test typing
        cmd = {
            "action": "type",
            "text": "Hello from mobile!"
        }
        status, screenshot = await ui.handle_command(json.dumps(cmd), os.getenv("ANTHROPIC_API_KEY"))
        logger.info(f"Type command - Status: {status}")
        
        # Test clicking
        cmd = {
            "action": "left_click"
        }
        status, screenshot = await ui.handle_command(json.dumps(cmd), os.getenv("ANTHROPIC_API_KEY"))
        logger.info(f"Click command - Status: {status}")
        
        # Test screenshot
        cmd = {
            "action": "screenshot"
        }
        status, screenshot = await ui.handle_command(json.dumps(cmd), os.getenv("ANTHROPIC_API_KEY"))
        logger.info(f"Screenshot command - Status: {status}")
        logger.info(f"Screenshot captured: {bool(screenshot)}")
        
    except Exception as e:
        logger.error(f"System-1 test failed: {str(e)}")
        raise

async def test_agents():
    """Test multi-agent chat functionality."""
    ui = MobileUI()
    
    try:
        # Test group chat
        chat_history = []
        chat_history = await ui.handle_message(
            "Hello Nova team!",
            chat_history,
            "Nova (Group)"
        )
        logger.info("Group message sent")
        logger.info(f"Chat history: {chat_history}")
        
        # Test individual agent
        chat_history = []
        chat_history = await ui.handle_message(
            "What do you believe about this?",
            chat_history,
            "Belief Agent"
        )
        logger.info("Agent message sent")
        logger.info(f"Chat history: {chat_history}")
        
    except Exception as e:
        logger.error(f"Agents test failed: {str(e)}")
        raise

async def main():
    """Run all tests."""
    logger.info("Testing mobile interface...")
    
    try:
        # Test System-1
        logger.info("\nTesting System-1...")
        await test_system1()
        
        # Test Agents
        logger.info("\nTesting Agents...")
        await test_agents()
        
        logger.info("\nAll tests passed!")
        
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Add project root to Python path
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    asyncio.run(main())
