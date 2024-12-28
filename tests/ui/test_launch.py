"""Test script to verify UI launch."""

import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mobile():
    """Test mobile UI launch."""
    from .mobile import MobileUI
    logger.info("Testing mobile UI...")
    ui = MobileUI()
    ui.launch()

async def test_desktop():
    """Test desktop UI launch."""
    from .desktop import DesktopUI
    logger.info("Testing desktop UI...")
    ui = DesktopUI()
    ui.launch()

async def main():
    """Run tests."""
    # Set API key
    os.environ["ANTHROPIC_API_KEY"] = "IGA3zJxd3AtXLWyVUq9fyNDev7xHD4UGbpwSWW8UejHeuUwO"
    
    try:
        # Test desktop first
        await test_desktop()
        
        # Wait for user to close desktop UI
        input("Press Enter after closing the desktop UI to test mobile UI...")
        
        # Test mobile
        await test_mobile()
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
