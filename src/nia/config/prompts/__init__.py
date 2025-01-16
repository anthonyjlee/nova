"""Agent prompt configuration module."""

from .analysis_agent import ANALYSIS_AGENT_PROMPT
from .belief_agent import BELIEF_AGENT_PROMPT
from .context_agent import CONTEXT_AGENT_PROMPT
from .desire_agent import DESIRE_AGENT_PROMPT
from .dialogue_agent import DIALOGUE_AGENT_PROMPT
from .emotion_agent import EMOTION_AGENT_PROMPT
from .integration_agent import INTEGRATION_AGENT_PROMPT
from .meta_agent import META_AGENT_PROMPT
from .orchestration_agent import ORCHESTRATION_AGENT_PROMPT
from .parsing_agent import PARSING_AGENT_PROMPT
from .reflection_agent import REFLECTION_AGENT_PROMPT
from .research_agent import RESEARCH_AGENT_PROMPT
from .synthesis_agent import SYNTHESIS_AGENT_PROMPT
from .validation_agent import VALIDATION_AGENT_PROMPT

# Map of agent types to their prompts
AGENT_PROMPTS = {
    "analysis": ANALYSIS_AGENT_PROMPT,
    "belief": BELIEF_AGENT_PROMPT,
    "context": CONTEXT_AGENT_PROMPT,
    "desire": DESIRE_AGENT_PROMPT,
    "dialogue": DIALOGUE_AGENT_PROMPT,
    "emotion": EMOTION_AGENT_PROMPT,
    "integration": INTEGRATION_AGENT_PROMPT,
    "meta": META_AGENT_PROMPT,
    "orchestration": ORCHESTRATION_AGENT_PROMPT,
    "parsing": PARSING_AGENT_PROMPT,
    "reflection": REFLECTION_AGENT_PROMPT,
    "research": RESEARCH_AGENT_PROMPT,
    "synthesis": SYNTHESIS_AGENT_PROMPT,
    "validation": VALIDATION_AGENT_PROMPT
}

def get_agent_prompt(agent_type: str) -> str:
    """Get the prompt for a specific agent type.
    
    Args:
        agent_type: The type of agent to get the prompt for
        
    Returns:
        The prompt string for the specified agent type
        
    Raises:
        KeyError: If no prompt exists for the specified agent type
    """
    if agent_type not in AGENT_PROMPTS:
        raise KeyError(f"No prompt found for agent type: {agent_type}")
    return AGENT_PROMPTS[agent_type]

def list_agent_types() -> list[str]:
    """Get a list of all available agent types.
    
    Returns:
        List of agent type strings
    """
    return list(AGENT_PROMPTS.keys())
