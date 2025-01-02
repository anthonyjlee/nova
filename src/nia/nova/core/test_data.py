"""Test data for Nova's FastAPI server tests and LM Studio integration."""

# LM Studio test data
VALID_LM_STUDIO_PROMPT = {
    "model": "llama-3.2-3b-instruct",
    "messages": [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Analyze this data and provide insights."}
    ],
    "temperature": 0.7,
    "max_tokens": 500,
    "stream": False
}

EXPECTED_LM_STUDIO_RESPONSE = {
    "id": "test-response",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "test-model",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Here are the insights from the data analysis..."
            },
            "finish_reason": "stop"
        }
    ]
}

# Task test data with LM Studio integration
VALID_TASK = {
    "type": "test_task",
    "parameters": {
        "key": "value",
        "llm_config": {
            "model": "llama-3.2-3b-instruct",
            "temperature": 0.7,
            "max_tokens": 500
        }
    },
    "priority": 1,
    "deadline": None,
    "dependencies": []
}

# Agent coordination test data with LM Studio integration
VALID_COORDINATION_REQUEST = {
    "agents": ["agent1", "agent2"],
    "task": {
        "type": "test_task",
        "parameters": {
            "key": "value",
            "llm_config": {
                "model": "llama-3.2-3b-instruct",
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        "priority": 1,
        "deadline": None,
        "dependencies": []
    },
    "strategy": {
        "type": "llm_based",
        "parameters": {
            "model": "test-model",
            "temperature": 0.7
        }
    },
    "constraints": {}
}

# Agent assignment test data
VALID_AGENT_ASSIGNMENT = {
    "agent_id": "test-agent",
    "task": {
        "type": "test_task",
        "parameters": {"key": "value"},
        "priority": 1,
        "deadline": None,
        "dependencies": []
    },
    "constraints": {}
}

# Memory test data with LM Studio integration
VALID_MEMORY_STORE = {
    "type": "store",
    "content": {
        "key": "value",
        "llm_generated": True,
        "llm_model": "llama-3.2-3b-instruct",
        "llm_confidence": 0.85
    },
    "importance": 0.8,
    "llm_config": {
        "chat_model": "llama-3.2-3b-instruct",
        "embedding_model": "text-embedding-nomic-embed-text-v1.5@q8_0"
    }
}

VALID_MEMORY_SEARCH = {
    "type": "search",
    "content": {
        "key": "value",
        "semantic_search": True
    },
    "importance": 0.5,
    "llm_config": {
        "chat_model": "llama-3.2-3b-instruct",
        "embedding_model": "text-embedding-nomic-embed-text-v1.5@q8_0"
    }
}

# Resource test data
VALID_RESOURCE_ALLOCATION = {
    "resources": {
        "resource1": {"capacity": 100},
        "resource2": {"capacity": 200}
    },
    "constraints": {},
    "priority": 1
}

# Flow test data
VALID_FLOW_OPTIMIZATION = {
    "flow_id": "test-flow",
    "parameters": {"key": "value"},
    "constraints": {}
}

# Analytics test data with LM Studio integration
VALID_ANALYTICS_REQUEST = {
    "type": "behavioral",
    "flow_id": "test-flow",
    "domain": "professional",
    "llm_config": {
        "model": "llama-3.2-3b-instruct",
        "temperature": 0.7,
        "max_tokens": 500,
        "analysis_depth": "detailed",
        "include_reasoning": True
    }
}

# Expected LM Studio generated insights
EXPECTED_INSIGHTS = {
    "behavioral": [
        {
            "type": "pattern",
            "description": "Identified recurring pattern in user interactions",
            "confidence": 0.85,
            "llm_generated": True
        },
        {
            "type": "anomaly",
            "description": "Detected unusual resource usage pattern",
            "confidence": 0.92,
            "llm_generated": True
        }
    ],
    "predictive": [
        {
            "type": "forecast",
            "description": "Predicted increased load in next 24 hours",
            "confidence": 0.78,
            "llm_generated": True
        }
    ]
}
