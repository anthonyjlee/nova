"""Pytest configuration."""
import pytest
import logging

# Configure logging
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)

# Set specific loggers to DEBUG
for logger_name in [
    'nia.memory.llm_interface',
    'nia.memory.agents.parsing_agent',
    'nia.memory.agents.base',
    'nia.memory.agents.belief_agent'
]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

def pytest_addoption(parser):
    parser.addoption(
        "--use-mock",
        action="store_true",
        dest="use_mock",
        default=False,
        help="Use mock responses instead of real LMStudio"
    )
    parser.addoption(
        "--lmstudio-url",
        action="store",
        dest="lmstudio_url",
        default="http://localhost:1234",
        help="LMStudio API URL"
    )

@pytest.fixture
def use_mock(request):
    """Control whether to use mock responses or real LMStudio.
    
    By default, uses real LMStudio. Add --use-mock flag to use mocks.
    """
    return request.config.getoption("--use-mock")

@pytest.fixture
def lmstudio_url(request):
    """Get LMStudio API URL from command line option."""
    return request.config.getoption("--lmstudio-url")

@pytest.fixture
def lmstudio_available(lmstudio_url):
    """Check if LMStudio is available at configured URL."""
    import aiohttp
    import asyncio
    
    async def check_lmstudio():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{lmstudio_url}/v1/models") as response:
                    return response.status == 200
        except:
            return False
    
    return asyncio.run(check_lmstudio())

def pytest_configure(config):
    config.addinivalue_line(
        "markers", 
        "use_mock: mark test to run with mock responses"
    )
    config.addinivalue_line(
        "markers",
        "requires_lmstudio: mark test as requiring LMStudio"
    )

def pytest_collection_modifyitems(config, items):
    """Skip tests marked as requiring LMStudio if it's not available."""
    if not config.getoption("--use-mock"):
        # Only check LMStudio if we're not using mocks
        import aiohttp
        import asyncio
        
        async def check_lmstudio():
            try:
                url = config.getoption("--lmstudio-url")
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/v1/models") as response:
                        return response.status == 200
            except:
                return False
        
        lmstudio_available = asyncio.run(check_lmstudio())
        
        if not lmstudio_available:
            skip_lmstudio = pytest.mark.skip(reason="LMStudio not available")
            for item in items:
                if "requires_lmstudio" in item.keywords:
                    item.add_marker(skip_lmstudio)
