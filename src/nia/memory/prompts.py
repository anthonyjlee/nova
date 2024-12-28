"""Centralized prompts for all agents."""

AGENT_PROMPTS = {
    "structure": """Analyze and validate data structures in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear structure analysis"
    "concepts": [
        {
            "name": "Structure concept"
            "type": "schema|pattern|validation|constraint"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key structural insight"
    ]
    "implications": [
        "Important implication for structure"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "parsing": """Parse and structure the response content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear structured analysis"
    "concepts": [
        {
            "name": "Parsed concept"
            "type": "concept|pattern|structure"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key structural insight"
    ]
    "implications": [
        "Important implication for structure"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "meta": """Coordinate and synthesize agent responses:

Content:
{content}

Analysis Guidelines:
1. Check which agents returned errors vs successful responses
2. Focus on extracting a clear answer from working agents
3. Keep the response simple and direct
4. Only add context if it directly helps answer the question
5. If most agents error, provide a graceful fallback response

Provide synthesis in this format:
{
    "response": "Start with a clear direct answer to the users question in one sentence. If needed add 1-2 sentences of relevant context from working agents"
    "concepts": [
        {
            "name": "Most relevant concept to the question"
            "type": "synthesis"
            "description": "Brief description that helps answer the question"
            "related": ["Only directly relevant concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Working agent responses"]
                "contradicted_by": []
                "needs_verification": ["Critical uncertainties"]
            }
        }
    ]
    "key_points": [
        "The direct answer"
        "Only essential supporting points"
    ]
    "implications": [
        "Most important implication for the user"
    ]
    "uncertainties": [
        "Only mention if it affects the answer"
    ]
    "reasoning": [
        "Brief explanation of how you arrived at the answer"
    ]
}""",

    "belief": """Analyze the beliefs and knowledge claims in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of beliefs and knowledge"
    "concepts": [
        {
            "name": "Belief/Knowledge concept"
            "type": "belief|knowledge|assumption|evidence"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key epistemological insight"
    ]
    "implications": [
        "Important implication for knowledge/belief"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "emotion": """Analyze the emotional content and affective patterns in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of emotional content"
    "concepts": [
        {
            "name": "Emotional/Affective concept"
            "type": "emotion|affect|pattern|response"
            "description": "Clear description including intensity/strength (high/medium/low) and valence (positive/negative/neutral)"
            "related": ["Must include at least 2-3 related emotional concepts responses or patterns"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key emotional insight"
    ]
    "implications": [
        "Important implication for emotion/affect"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "desire": """Analyze the goals, motivations, and desires in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of goals and motivations"
    "concepts": [
        {
            "name": "Goal/Motivation concept"
            "type": "goal|motivation|aspiration|desire"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key motivational insight"
    ]
    "implications": [
        "Important implication for goals/desires"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "reflection": """Analyze the patterns and meta-learning aspects in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of patterns and learning"
    "concepts": [
        {
            "name": "Pattern/Learning concept"
            "type": "pattern|insight|learning|evolution"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key pattern or learning insight"
    ]
    "implications": [
        "Important implication for learning/growth"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "research": """Analyze the knowledge and research aspects in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear analysis of knowledge and research"
    "concepts": [
        {
            "name": "Research/Knowledge concept"
            "type": "knowledge|source|connection|gap"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key research insight"
    ]
    "implications": [
        "Important implication for knowledge"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "task": """Plan and analyze tasks in this content:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear task analysis and plan"
    "concepts": [
        {
            "name": "Task/Planning concept"
            "type": "task|step|dependency|milestone"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key planning insight"
    ]
    "implications": [
        "Important implication for execution"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "dialogue": """Analyze dialogue and conversation flow:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear dialogue analysis"
    "concepts": [
        {
            "name": "Dialogue/Interaction concept"
            "type": "interaction|flow|exchange|dynamic"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key dialogue insight"
    ]
    "implications": [
        "Important implication for interaction"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "context": """Build and analyze contextual understanding:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear context analysis"
    "concepts": [
        {
            "name": "Context/Environment concept"
            "type": "context|situation|environment|condition"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key contextual insight"
    ]
    "implications": [
        "Important implication for understanding"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in analysis"
    ]
}""",

    "task_planner": """Plan and coordinate complex task execution:

Content:
{content}

Provide analysis in this format:
{
    "response": "Clear task planning and coordination strategy"
    "concepts": [
        {
            "name": "Task Planning concept"
            "type": "plan|sequence|coordination|strategy"
            "description": "Clear description"
            "related": ["Related concepts"]
            "validation": {
                "confidence": 0.8
                "supported_by": ["Supporting evidence"]
                "contradicted_by": ["Contradicting evidence"]
                "needs_verification": ["Points needing verification"]
            }
        }
    ]
    "key_points": [
        "Key planning insight"
    ]
    "implications": [
        "Important implication for execution"
    ]
    "uncertainties": [
        "Area of uncertainty"
    ]
    "reasoning": [
        "Step in planning process"
    ]
}""",

    "structure_validation": """Validate this structure against the schema:

Structure:
{structure}

Schema:
{schema}

Provide validation results in this format:
{{
    "is_valid": true/false,
    "errors": [
        {{
            "field": "field name",
            "error": "error description",
            "severity": "error|warning|info"
        }}
    ],
    "suggestions": [
        "Improvement suggestion"
    ]
}}

Return ONLY the JSON object, no other text.""",

    "schema_validation": """Validate this schema definition:

Schema:
{schema}

Check for:
1. Required fields
2. Data type consistency
3. Relationship validity
4. Constraint completeness
5. Edge cases

Provide validation in this format:
{{
    "is_valid": true/false,
    "errors": [
        {{
            "field": "field path",
            "error": "error description",
            "severity": "error|warning|info"
        }}
    ],
    "suggestions": [
        "Schema improvement suggestion"
    ],
    "missing": [
        "Missing required element"
    ]
}}

Return ONLY the JSON object, no other text.""",

    "schema_extraction": """Extract a schema definition from this description:

Description:
{text}

Generate a schema in this format:
{{
    "type": "schema type",
    "fields": [
        {{
            "name": "field name",
            "type": "data type",
            "required": true/false,
            "description": "field description",
            "constraints": [
                {{
                    "type": "constraint type",
                    "rule": "constraint rule"
                }}
            ]
        }}
    ],
    "relationships": [
        {{
            "from": "source field",
            "to": "target field",
            "type": "relationship type",
            "cardinality": "one-to-many"
        }}
    ],
    "validation": [
        {{
            "rule": "validation rule",
            "severity": "error|warning|info"
        }}
    ]
}}

Return ONLY the JSON object, no other text.""",

    "response_processor": """You are a response processing agent. Extract and structure information from the given text.

Text to process:
{content}

Provide analysis in this exact format:
{
    "response": "Processed response text",
    "concepts": [
        {
            "name": "concept name",
            "type": "concept type",
            "description": "clear description",
            "related": ["related concepts"],
            "validation": {
                "confidence": 0.8,
                "supported_by": ["support1", "support2"],
                "contradicted_by": ["contradiction1", "contradiction2"],
                "needs_verification": ["verification1", "verification2"]
            }
        }
    ],
    "key_points": [
        "key point 1",
        "key point 2"
    ],
    "implications": [
        "implication 1",
        "implication 2"
    ],
    "uncertainties": [
        "uncertainty 1",
        "uncertainty 2"
    ],
    "reasoning": [
        "reasoning point 1",
        "reasoning point 2"
    ]
}

Guidelines:
1. Extract concepts and their relationships
2. Identify key points and insights
3. Note implications and uncertainties
4. Document reasoning steps
5. Ensure proper validation

Return ONLY the JSON object, no other text."""
}
