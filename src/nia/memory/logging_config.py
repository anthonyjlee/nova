"""
Logging configuration for the memory system.
"""

import logging
import sys
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        # Add color to levelname
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        
        # Add color to name (logger name)
        record.name = f"{Fore.BLUE}{record.name}{Style.RESET_ALL}"
        
        return super().format(record)

def configure_logging():
    """Configure logging for the memory system."""
    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)  # Set to DEBUG to see detailed logs
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to see detailed logs
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Configure our loggers
    for logger_name in [
        'nia.memory.llm_interface',
        'nia.memory.agents.base',
        'nia.memory.neo4j.concept_manager',
        'nia.memory.memory_integration'
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Allow messages to propagate to root logger
    
    # Log startup message
    logging.info("Logging configured with DEBUG level")
