"""Configuration module for NIA."""

from .agent_config import (
    get_agent_prompt,
    validate_agent_config,
    AGENT_RESPONSIBILITIES,
    BASE_AGENT_TEMPLATE
)

__all__ = [
    'get_agent_prompt',
    'validate_agent_config',
    'AGENT_RESPONSIBILITIES',
    'BASE_AGENT_TEMPLATE'
]
