"""FastAPI dependencies for endpoints."""

from typing import Any
from fastapi import Depends

from ...memory.graph_store import GraphStore
from ...memory.two_layer import TwoLayerMemorySystem
from ...agents.base import CoordinationAgent, AnalyticsAgent

async def get_graph_store() -> GraphStore:
    """Get graph store instance."""
    return GraphStore()

async def get_memory_system() -> TwoLayerMemorySystem:
    """Get memory system instance."""
    return TwoLayerMemorySystem()

async def get_coordination_agent() -> CoordinationAgent:
    """Get coordination agent instance."""
    return CoordinationAgent()

async def get_analytics_agent() -> AnalyticsAgent:
    """Get analytics agent instance."""
    return AnalyticsAgent()
