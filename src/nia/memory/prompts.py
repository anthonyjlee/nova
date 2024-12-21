"""Centralized prompts for all agents."""

AGENT_PROMPTS = {
    "belief": """Analyze the beliefs and knowledge claims in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of beliefs and knowledge",
    "concepts": [
        {
            "name": "Belief/Knowledge concept",
            "type": "belief|knowledge|assumption|evidence",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }
        }
    ],
    "key_points": [
        "Key epistemological insight"
    ],
    "implications": [
        "Important implication for knowledge/belief"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "emotion": """Analyze the emotional content and affective patterns in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of emotional content",
    "concepts": [
        {
            "name": "Emotional/Affective concept",
            "type": "emotion|affect|pattern|response",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }
        }
    ],
    "key_points": [
        "Key emotional insight"
    ],
    "implications": [
        "Important implication for emotion/affect"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "desire": """Analyze the goals, motivations, and desires in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of goals and motivations",
    "concepts": [
        {
            "name": "Goal/Motivation concept",
            "type": "goal|motivation|aspiration|desire",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }
        }
    ],
    "key_points": [
        "Key motivational insight"
    ],
    "implications": [
        "Important implication for goals/desires"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "reflection": """Analyze the patterns and meta-learning aspects in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of patterns and learning",
    "concepts": [
        {
            "name": "Pattern/Learning concept",
            "type": "pattern|insight|learning|evolution",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }
        }
    ],
    "key_points": [
        "Key pattern or learning insight"
    ],
    "implications": [
        "Important implication for learning/growth"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "research": """Analyze the knowledge and research aspects in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of knowledge and research",
    "concepts": [
        {
            "name": "Research/Knowledge concept",
            "type": "knowledge|source|connection|gap",
            "description": "Clear description",
            "related": ["Related concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": ["Contradicting evidence"],
                "needs_verification": ["Points needing verification"]
            }
        }
    ],
    "key_points": [
        "Key research insight"
    ],
    "implications": [
        "Important implication for knowledge"
    ],
    "uncertainties": [
        "Area of uncertainty"
    ],
    "reasoning": [
        "Step in analysis"
    ]
}"""
}
