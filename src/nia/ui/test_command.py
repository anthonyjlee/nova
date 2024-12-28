"""Test script for command execution."""

import os
import json
import asyncio
import logging
from handlers import System1Handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_commands():
    """Test various computer control commands."""
    # Initialize handler
    handler = System1Handler()
    
    try:
        # Test typing
        cmd = {
            "action": "type",
            "text": "Hello, World!"
        }
        output, status, _ = await handler.execute_command(json.dumps(cmd))
        logger.info(f"Type command - Output: {output}, Status: {status}")
        
        # Test key combination
        cmd = {
            "action": "key",
            "text": "cmd+a"  # Select all
        }
        output, status, _ = await handler.execute_command(json.dumps(cmd))
        logger.info(f"Key command - Output: {output}, Status: {status}")
        
        # Test mouse movement
        cmd = {
            "action": "mouse_move",
            "coordinate": [100, 100]
        }
        output, status, _ = await handler.execute_command(json.dumps(cmd))
        logger.info(f"Mouse move command - Output: {output}, Status: {status}")
        
        # Test clicking
        cmd = {
            "action": "left_click"
        }
        output, status, _ = await handler.execute_command(json.dumps(cmd))
        logger.info(f"Click command - Output: {output}, Status: {status}")
        
        # Test screenshot
        cmd = {
            "action": "screenshot"
        }
        output, status, screenshot = await handler.execute_command(json.dumps(cmd))
        logger.info(f"Screenshot command - Output: {output}, Status: {status}")
        logger.info(f"Screenshot data length: {len(screenshot) if screenshot else 0}")
        
        # Test error handling
        cmd = {
            "action": "invalid_action"
        }
        output, status, _ = await handler.execute_command(json.dumps(cmd))
        logger.info(f"Invalid command - Output: {output}, Status: {status}")
        
        # Test port forwarding
        if handler.public_url:
            logger.info(f"Port forwarding active at: {handler.public_url}")
        else:
            logger.warning("Port forwarding not active")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_commands())
