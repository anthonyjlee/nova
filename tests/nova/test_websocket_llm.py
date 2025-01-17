"""Tests for WebSocket LLM integration.

This test suite verifies the integration between WebSocket and LLM functionality:
- Direct LLM testing
- WebSocket streaming
- Template validation
- Error handling
- Agent coordination
- Connection stability
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Awaitable
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

from nia.nova.core.llm import LMStudioLLM
from nia.nova.core.websocket import WebSocketManager
from nia.nova.core.websocket_test_utils import create_websocket_session
from nia.agents.base import BaseAgent, CoordinationAgent, AnalyticsAgent, ParsingAgent, OrchestrationAgent

# Initialize agents before tests
from unittest.mock import AsyncMock

@pytest.fixture
def mock_memory_system():
    """Create async mock memory system."""
    return AsyncMock()

@pytest.fixture
def mock_world():
    """Create async mock world."""
    return AsyncMock()

@pytest.fixture
async def test_agents(mock_memory_system, mock_world, llm: LMStudioLLM):
    """Create and initialize test agents."""
    # Configure memory system with real LLM
    mock_memory_system.llm = llm
    
    # Create specialized agents
    coordinator = CoordinationAgent()
    coordinator.name = "TestCoordinator"
    coordinator.agent_type = "coordinator"
    coordinator._memory_system = mock_memory_system
    coordinator._world = mock_world
    
    analytics = AnalyticsAgent()
    analytics.name = "TestAnalytics"
    analytics.agent_type = "analytics"
    analytics._memory_system = mock_memory_system
    analytics._world = mock_world
    
    parser = ParsingAgent()
    parser.name = "TestParser"
    parser.agent_type = "parser"
    parser._memory_system = mock_memory_system
    parser._world = mock_world
    
    orchestrator = OrchestrationAgent()
    orchestrator.name = "TestOrchestrator"
    orchestrator.agent_type = "orchestrator"
    orchestrator._memory_system = mock_memory_system
    orchestrator._world = mock_world
    
    agents = {
        "coordinator": coordinator,
        "analytics": analytics,
        "parser": parser,
        "orchestrator": orchestrator
    }
    
    # Initialize agents with mock dependencies
    for agent in agents.values():
        agent._memory_system = mock_memory_system
        agent._world = mock_world
        # initialize() is async, so we need to await it
        await agent.initialize()
        
    return agents

@pytest.fixture
def initialized_agents(test_agents):
    """Get initialized agents."""
    return test_agents

@pytest.fixture
async def test_app(llm: LMStudioLLM, initialized_agents) -> FastAPI:
    """Create FastAPI test application."""
    app = FastAPI()
    
    # Create WebSocket manager
    websocket_manager = WebSocketManager(llm=llm)
    
    # Get initialized agents
    agents = await initialized_agents
    
    # Initialize agents
    websocket_manager.coordination_agent = agents["coordinator"]
    websocket_manager.analytics_agent = agents["analytics"]
    websocket_manager.parsing_agent = agents["parser"]
    websocket_manager.orchestration_agent = agents["orchestrator"]
    
    @app.websocket("/api/nova/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await websocket_manager.ensure_initialized()
        await websocket_manager.connect(websocket, client_id)
        try:
            while True:
                data = await websocket.receive_json()
                if data["type"] == "llm_request":
                    await websocket_manager.handle_llm_request(websocket, data)
                elif data["type"] == "chat_message":
                    await websocket_manager.handle_chat_message(websocket, data)
        except WebSocketDisconnect:
            await websocket_manager.disconnect(client_id)
            
    return app

@pytest.fixture
def llm() -> LMStudioLLM:
    """Create LLM instance."""
    return LMStudioLLM(
        chat_model="llama-3.2-3b-instruct",
        embedding_model="text-embedding-nomic-embed-text-v1.5@f16",
        api_base="http://localhost:1234/v1"
    )

@pytest.mark.asyncio
async def test_llm_direct_request(llm: LMStudioLLM) -> None:
    """Test direct LLM request without WebSocket."""
    result = await llm.analyze(
        content={
            "query": "Test query",
            "type": "analysis"
        },
        template="parsing_analysis"
    )
    assert "response" in result
    assert "concepts" in result

@pytest.mark.asyncio
async def test_llm_websocket_streaming(test_app: Awaitable[FastAPI], llm: LMStudioLLM) -> None:
    """Test LLM streaming through WebSocket."""
    app = await test_app
    async with create_websocket_session(app, "/api/nova/ws/test-client") as session:
        # Send LLM request
        await session.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "parsing_analysis",
                "metadata": {
                    "domain": "test",
                    "type": "analysis"
                }
            }
        })
        
        # Collect streaming chunks
        chunks = []
        while True:
            msg = await session.receive_json()
            chunks.append(msg)
            if msg["type"] == "llm_chunk" and msg["data"]["is_final"]:
                break
        
        # Verify streaming worked
        assert len(chunks) > 1  # Should have multiple chunks
        assert all(c["type"] == "llm_chunk" for c in chunks)
        
        # Verify complete response
        complete_response = "".join(
            c["data"]["chunk"] for c in chunks 
            if not c["data"]["is_final"]
        )
        assert len(complete_response) > 0

@pytest.mark.asyncio
async def test_llm_template_validation(test_app: Awaitable[FastAPI]) -> None:
    """Test LLM template validation through WebSocket."""
    app = await test_app
    async with create_websocket_session(app, "/api/nova/ws/test-client") as session:
        # Test invalid template
        await session.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "invalid_template"
            }
        })
        response = await session.receive_json()
        assert response["type"] == "error"
        assert "template not found" in response["data"]["message"].lower()
        
        # Test valid template
        await session.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "parsing_analysis"
            }
        })
        response = await session.receive_json()
        assert response["type"] == "llm_chunk"

@pytest.mark.asyncio
async def test_llm_error_recovery(test_app: Awaitable[FastAPI], llm: LMStudioLLM) -> None:
    """Test LLM error handling and recovery."""
    app = await test_app
    async with create_websocket_session(app, "/api/nova/ws/test-client") as session:
        # Simulate LLM API error by using a non-existent port
        llm.api_base = "http://localhost:9999/v1"
        await session.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "parsing_analysis"
            }
        })
        response = await session.receive_json()
        assert response["type"] == "error"
        assert "failed to connect" in response["data"]["message"].lower()
        
        # Fix LLM and retry
        llm.api_base = "http://localhost:1234/v1"
        await session.send_json({
            "type": "llm_request",
            "data": {
                "content": "Test query",
                "template": "parsing_analysis"
            }
        })
        response = await session.receive_json()
        assert response["type"] == "llm_chunk"

@pytest.mark.asyncio
async def test_llm_agent_coordination(test_app: Awaitable[FastAPI]) -> None:
    """Test LLM coordination with agents."""
    app = await test_app
    async with create_websocket_session(app, "/api/nova/ws/test-client") as session:
        # Test sequential coordination
        await session.send_json({
            "type": "chat_message",
            "data": {
                "content": "Sequential task requiring parser then orchestrator",
                "pattern": "sequential",
                "workspace": "test"
            }
        })
        messages = await collect_messages(session)
        verify_sequential_pattern(messages)
        
        # Test parallel coordination
        await session.send_json({
            "type": "chat_message",
            "data": {
                "content": "Parallel task for multiple agents",
                "pattern": "parallel",
                "workspace": "test"
            }
        })
        messages = await collect_messages(session)
        verify_parallel_pattern(messages)
        
        # Test hierarchical coordination
        await session.send_json({
            "type": "chat_message",
            "data": {
                "content": "Hierarchical task with coordinator managing others",
                "pattern": "hierarchical",
                "workspace": "test"
            }
        })
        messages = await collect_messages(session)
        verify_hierarchical_pattern(messages)

async def collect_messages(session) -> List[Dict]:
    """Collect all messages until final response."""
    messages = []
    while True:
        msg = await session.receive_json()
        messages.append(msg)
        if msg["type"] == "chat_message" and msg["data"].get("is_final"):
            break
    return messages

def verify_sequential_pattern(messages: List[Dict]) -> None:
    """Verify sequential coordination pattern."""
    # Get agent actions in order
    actions = [m for m in messages if m["type"] == "agent_action"]
    assert len(actions) >= 2
    
    # Verify parser runs before orchestrator
    parser_idx = next(i for i, m in enumerate(actions) 
                     if m["data"]["agent"] == "parser")
    orchestrator_idx = next(i for i, m in enumerate(actions)
                          if m["data"]["agent"] == "orchestrator")
    assert parser_idx < orchestrator_idx

def verify_parallel_pattern(messages: List[Dict]) -> None:
    """Verify parallel coordination pattern."""
    # Get unique agents that acted
    agents = {m["data"]["agent"] for m in messages 
             if m["type"] == "agent_action"}
    assert len(agents) >= 2
    
    # Verify analytics and parser both participated
    assert "analytics" in agents
    assert "parser" in agents

def verify_hierarchical_pattern(messages: List[Dict]) -> None:
    """Verify hierarchical coordination pattern."""
    # Get agent actions
    actions = [m for m in messages if m["type"] == "agent_action"]
    assert len(actions) >= 3
    
    # Verify coordinator delegated to other agents
    coordinator_actions = [m for m in actions 
                         if m["data"]["agent"] == "coordinator"]
    assert len(coordinator_actions) >= 1
    
    # Verify other agents were coordinated
    coordinated_agents = {m["data"]["agent"] for m in actions 
                         if m["data"]["agent"] != "coordinator"}
    assert len(coordinated_agents) >= 2

@pytest.mark.asyncio
async def test_llm_connection_stability(test_app: Awaitable[FastAPI]) -> None:
    """Test WebSocket stability during long LLM operations."""
    app = await test_app
    async with create_websocket_session(app, "/api/nova/ws/test-client") as session:
        # Send long query
        await session.send_json({
            "type": "llm_request",
            "data": {
                "content": "Very long query requiring extensive processing",
                "template": "analytics_processing"
            }
        })
        
        # Collect chunks with timeout monitoring
        start_time = time.time()
        chunks = []
        while True:
            try:
                msg = await asyncio.wait_for(
                    session.receive_json(),
                    timeout=5.0  # 5 second timeout per chunk
                )
                chunks.append(msg)
                if msg["type"] == "llm_chunk" and msg["data"]["is_final"]:
                    break
            except asyncio.TimeoutError:
                assert False, "Timeout waiting for LLM response"
        
        # Verify connection remained stable
        elapsed_time = time.time() - start_time
        assert elapsed_time > 1.0  # Should take some time
        assert len(chunks) > 5  # Should have multiple chunks
