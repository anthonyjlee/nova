"""Test script for NIA chat interface."""

import asyncio
import logging
import os
import sys
from pathlib import Path

from nia.ui.mobile import MobileUI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat():
    """Test chat functionality with different agents."""
    ui = MobileUI()
    
    try:
        # Test main chat
        chat_history = []
        chat_history = await ui.handle_message(
            "Hello Nova!",
            chat_history
        )
        logger.info("Main chat message sent")
        logger.info(f"Chat history: {chat_history}")
        
        # Test switching to Belief Agent
        status = ui.switch_chat("Belief Agent")
        logger.info(f"Switched to Belief Agent: {status}")
        
        # Test message with Belief Agent
        chat_history = []
        chat_history = await ui.handle_message(
            "What are your core beliefs?",
            chat_history
        )
        logger.info("Belief Agent message sent")
        logger.info(f"Chat history: {chat_history}")
        
        # Test switching to Emotion Agent
        status = ui.switch_chat("Emotion Agent")
        logger.info(f"Switched to Emotion Agent: {status}")
        
        # Test message with Emotion Agent
        chat_history = []
        chat_history = await ui.handle_message(
            "How do you feel about this conversation?",
            chat_history
        )
        logger.info("Emotion Agent message sent")
        logger.info(f"Chat history: {chat_history}")
        
    except Exception as e:
        logger.error(f"Chat test failed: {str(e)}")
        raise

async def main():
    """Run all tests."""
    logger.info("Testing chat interface...")
    
    try:
        await test_chat()
        logger.info("\nAll tests passed!")
        
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    asyncio.run(main())
