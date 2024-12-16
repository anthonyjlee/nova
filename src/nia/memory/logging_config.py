"""
Logging configuration for memory system.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter('%(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s\n%(message)s\n')
    
    # Console handler - minimal output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler for agent responses - detailed output
    responses_file = 'logs/agent_responses.log'
    responses_handler = RotatingFileHandler(
        responses_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    responses_handler.setFormatter(file_formatter)
    responses_handler.setLevel(logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Create agent response logger
    agent_logger = logging.getLogger('agent_responses')
    agent_logger.setLevel(logging.INFO)
    agent_logger.addHandler(responses_handler)
    
    return agent_logger
