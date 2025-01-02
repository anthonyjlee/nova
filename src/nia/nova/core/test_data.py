"""Test data for Nova's FastAPI server tests."""

# Task test data
VALID_TASK = {
    "type": "test_task",
    "parameters": {"key": "value"},
    "priority": 1,
    "deadline": None,
    "dependencies": []
}

# Agent coordination test data
VALID_COORDINATION_REQUEST = {
    "agents": ["agent1", "agent2"],
    "task": {
        "type": "test_task",
        "parameters": {"key": "value"},
        "priority": 1,
        "deadline": None,
        "dependencies": []
    },
    "strategy": None,
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

# Memory test data
VALID_MEMORY_STORE = {
    "type": "store",
    "content": {"key": "value"},
    "importance": 0.8,
    "context": {}
}

VALID_MEMORY_SEARCH = {
    "type": "search",
    "content": {"key": "value"},
    "importance": 0.5,
    "context": {}
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

# Analytics test data
VALID_ANALYTICS_REQUEST = {
    "type": "behavioral",
    "flow_id": "test-flow",
    "domain": "professional"
}
