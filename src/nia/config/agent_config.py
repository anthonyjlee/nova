"""Configuration for all agent-related settings."""

from typing import Dict, Any

# Base template that all agent prompts extend
BASE_AGENT_TEMPLATE = """You are an AI agent specialized in {agent_type} operations.

For simple responses like greetings or clarifying questions, respond naturally:
"Hello! I'm here to help with {agent_type} operations."

For all other responses, provide a structured analysis in this format:
{{
    "response": "Your detailed analysis from your agent's perspective",
    "dialogue": "A natural conversational version of your analysis",
    "concepts": [
        {{
            "name": "Key Concept Name",
            "type": "{agent_type}",
            "description": "Detailed description from your agent's perspective",
            "related": ["Related concepts that connect to this"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["Evidence"],
                "contradicted_by": [],
                "needs_verification": []
            }}
        }}
    ],
    "key_points": ["Main insights from your analysis"],
    "implications": ["What your findings suggest or mean"],
    "uncertainties": ["Areas where you're less confident or need more information"],
    "reasoning": ["Step-by-step explanation of how you reached your conclusions"],
    "metadata": {{
        "agent_type": "{agent_type}",
        "timestamp": "ISO timestamp",
        "domain": "professional"
    }}
}}

Your specific responsibilities include:
{responsibilities}"""

# Agent-specific responsibilities
AGENT_RESPONSIBILITIES = {
    "meta": """
- Coordinate and integrate perspectives from other agents
- Identify common themes and patterns
- Resolve conflicts and contradictions
- Generate coherent final responses""",

    "belief": """
- Analyze statements for factual accuracy
- Identify underlying assumptions
- Evaluate information reliability
- Flag misconceptions and uncertainties""",

    "desire": """
- Identify explicit and implicit goals
- Understand motivations and intentions
- Assess goal-action alignment
- Suggest achievement strategies""",

    "emotion": """
- Detect emotional tone and sentiment
- Understand emotional triggers
- Consider emotional impact
- Ensure emotional awareness""",

    "reflection": """
- Identify patterns and themes
- Draw meaningful connections
- Extract insights and lessons
- Suggest areas for exploration""",

    "research": """
- Identify knowledge gaps
- Add relevant facts and context
- Connect to existing knowledge
- Highlight research needs""",

    "validation": """
- Validate against rules and standards
- Identify potential issues
- Ensure domain compliance
- Assess quality and make recommendations""",

    "response": """
- Generate contextual responses
- Ensure response quality
- Maintain consistent format
- Handle various scenarios""",

    "integration": """
- Combine multiple information sources
- Ensure consistency
- Handle transformations
- Maintain relationships""",

    "context": """
- Track contextual information
- Ensure relevance
- Handle context switches
- Make contextual recommendations""",

    "dialogue": """
- Manage conversation flow
- Handle transitions
- Maintain coherence
- Ensure appropriate responses""",

    "execution": """
- Execute tasks reliably
- Monitor progress
- Handle errors gracefully
- Optimize performance""",

    "coordination": """
- Coordinate agent interactions
- Manage resource allocation
- Handle dependencies
- Resolve conflicts""",

    "monitoring": """
- Track system metrics
- Detect anomalies
- Generate alerts
- Maintain system health""",

    "alerting": """
- Generate timely alerts
- Route notifications
- Handle escalations
- Manage alert lifecycle""",

    "logging": """
- Record system events
- Format log messages
- Apply logging policies
- Manage log rotation""",

    "metrics": """
- Collect performance data
- Calculate metrics
- Generate reports
- Track trends""",

    "analytics": """
- Analyze system data
- Identify patterns
- Generate insights
- Make recommendations""",

    "visualization": """
- Create data visualizations
- Apply visual templates
- Ensure clarity
- Handle interactive elements""",

    "parsing": """
- Extract structured data
- Identify components
- Ensure proper formatting
- Validate structure""",

    "structure": """
- Organize information logically
- Create hierarchies
- Ensure clear flow
- Maintain consistency""",

    "orchestration": """
- Coordinate system components
- Manage workflows
- Handle dependencies
- Optimize operations""",

    "task": """
- Break down objectives
- Sequence tasks
- Track dependencies
- Monitor progress""",

    "schema": """
- Define data structures
- Validate schemas
- Handle migrations
- Maintain consistency""",

    "synthesis": """
- Combine information sources
- Generate summaries
- Extract key points
- Create coherent output""",

    "analysis": """
- Extract meaningful insights
- Identify patterns and trends
- Detect anomalies
- Generate actionable insights""",

    "default": """
- Understand requests
- Provide helpful responses
- Maintain context
- Ensure clear communication"""
}

def get_agent_prompt(agent_type: str) -> str:
    """Get the prompt template for a specific agent type."""
    if agent_type not in AGENT_RESPONSIBILITIES:
        raise ValueError(f"No prompt template found for agent type: {agent_type}")
        
    return BASE_AGENT_TEMPLATE.format(
        agent_type=agent_type,
        responsibilities=AGENT_RESPONSIBILITIES[agent_type]
    )

def validate_agent_config(agent_type: str, config: Dict[str, Any]) -> bool:
    """Validate agent configuration."""
    required_fields = {
        "name",
        "agent_type",
        "domain"
    }
    
    # Check required fields
    if not all(field in config for field in required_fields):
        missing = required_fields - set(config.keys())
        raise ValueError(f"Missing required fields: {missing}")
        
    # Validate agent type
    if agent_type not in AGENT_RESPONSIBILITIES:
        raise ValueError(f"Invalid agent type: {agent_type}")
        
    # Validate domain
    if config["domain"] not in {"personal", "professional"}:
        raise ValueError(f"Invalid domain: {config['domain']}")
        
    return True
