"""Performance tests for Nova's core functionality."""

import pytest
import asyncio
import time
import logging
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from nia.memory.two_layer import TwoLayerMemorySystem
from nia.core.vector.vector_store import VectorStore
from nia.core.vector.embeddings import EmbeddingService
from nia.agents.specialized.swarm_metrics_agent import SwarmMetricsAgent
from nia.agents.specialized.swarm_registry_agent import SwarmRegistryAgent
from nia.memory.profile_store import ProfileStore
from nia.memory.agent_store import AgentStore
from nia.memory.graph_store import GraphStore

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Track and analyze performance metrics."""
    
    def __init__(self):
        """Initialize metrics storage."""
        self.response_times: List[float] = []
        self.memory_operations: List[float] = []
        self.concurrent_ops: List[int] = []
        self.errors: List[str] = []
    
    def add_response_time(self, time_ms: float):
        """Add response time measurement."""
        self.response_times.append(time_ms)
    
    def add_memory_operation(self, time_ms: float):
        """Add memory operation time."""
        self.memory_operations.append(time_ms)
    
    def add_concurrent_ops(self, count: int):
        """Add concurrent operation count."""
        self.concurrent_ops.append(count)
    
    def add_error(self, error: str):
        """Add error message."""
        self.errors.append(error)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        # Response time stats
        if self.response_times:
            stats["response_times"] = {
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": statistics.quantiles(self.response_times, n=20)[18],  # 95th percentile
                "min": min(self.response_times),
                "max": max(self.response_times)
            }
        
        # Memory operation stats
        if self.memory_operations:
            stats["memory_operations"] = {
                "mean": statistics.mean(self.memory_operations),
                "median": statistics.median(self.memory_operations),
                "p95": statistics.quantiles(self.memory_operations, n=20)[18],
                "min": min(self.memory_operations),
                "max": max(self.memory_operations)
            }
        
        # Concurrent operation stats
        if self.concurrent_ops:
            stats["concurrent_operations"] = {
                "mean": statistics.mean(self.concurrent_ops),
                "max": max(self.concurrent_ops),
                "total": sum(self.concurrent_ops)
            }
        
        # Error stats
        stats["errors"] = {
            "count": len(self.errors),
            "messages": self.errors[:10]  # First 10 errors
        }
        
        return stats

@pytest.fixture
async def performance_metrics():
    """Create performance metrics tracker."""
    return PerformanceMetrics()

@pytest.fixture
async def memory_system(request):
    """Create memory system for performance testing."""
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        embedding_service=embedding_service,
        host="localhost",
        port=6333
    )
    
    memory = TwoLayerMemorySystem(
        neo4j_uri="bolt://localhost:7687",
        vector_store=vector_store
    )
    
    async def cleanup():
        """Clean up test data."""
        try:
            await memory.semantic.store.run_query(
                "MATCH (n) WHERE n.domain = 'test' DETACH DELETE n"
            )
            if hasattr(memory.episodic.store, 'delete_collection'):
                await memory.episodic.store.delete_collection()
            await memory.cleanup()
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
    
    try:
        await memory.initialize()
        if hasattr(memory.episodic.store, 'ensure_collection'):
            await memory.episodic.store.ensure_collection("test_performance")
        yield memory
    finally:
        request.addfinalizer(cleanup)

@pytest.mark.performance
class TestMemoryPerformance:
    """Test memory system performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(
        self,
        memory_system: TwoLayerMemorySystem,
        performance_metrics: PerformanceMetrics
    ):
        """Test concurrent memory operations."""
        # Generate test data
        test_data = [
            {
                "content": f"Test content {i}",
                "type": "test",
                "importance": 0.8,
                "context": {"domain": "test"}
            }
            for i in range(100)
        ]
        
        async def store_and_measure(data):
            """Store data and measure time."""
            try:
                start = time.time()
                await memory_system.store(data)
                end = time.time()
                performance_metrics.add_memory_operation((end - start) * 1000)
                return True
            except Exception as e:
                performance_metrics.add_error(str(e))
                return False
        
        # Run concurrent operations
        tasks = [
            asyncio.create_task(store_and_measure(data))
            for data in test_data
        ]
        
        results = await asyncio.gather(*tasks)
        performance_metrics.add_concurrent_ops(len([r for r in results if r]))
        
        # Get and log statistics
        stats = performance_metrics.get_stats()
        logger.info(f"Memory operation stats: {stats}")
        
        # Verify performance
        assert stats["memory_operations"]["p95"] < 1000  # 95th percentile under 1s
        assert stats["errors"]["count"] == 0  # No errors
        assert stats["concurrent_operations"]["total"] == 100  # All ops successful

@pytest.mark.performance
class TestSwarmPerformance:
    """Test swarm system performance."""
    
    @pytest.mark.asyncio
    async def test_swarm_coordination(
        self,
        memory_system: TwoLayerMemorySystem,
        performance_metrics: PerformanceMetrics
    ):
        """Test swarm coordination performance."""
        registry_agent = SwarmRegistryAgent(
            name="test_registry",
            memory_system=memory_system,
            domain="test"
        )
        
        metrics_agent = SwarmMetricsAgent(
            name="test_metrics",
            memory_system=memory_system,
            domain="test"
        )
        
        # Create test swarms
        swarms = []
        for i in range(10):
            start = time.time()
            swarm_id = f"swarm_{i}"
            
            # Register swarm
            await registry_agent.register_pattern(
                pattern_type="hierarchical",
                config={
                    "supervisor_id": f"supervisor_{i}",
                    "worker_ids": [f"worker_{i}_{j}" for j in range(5)]
                }
            )
            
            # Track metrics
            await metrics_agent.collect_metrics(
                swarm_id=swarm_id,
                metrics={
                    "response_time": 100,
                    "throughput": 50,
                    "success_rate": 0.95
                }
            )
            
            end = time.time()
            performance_metrics.add_response_time((end - start) * 1000)
            swarms.append(swarm_id)
        
        # Analyze patterns
        start = time.time()
        for swarm_id in swarms:
            await metrics_agent.analyze_patterns(swarm_id)
        end = time.time()
        
        performance_metrics.add_memory_operation((end - start) * 1000)
        
        # Get and log statistics
        stats = performance_metrics.get_stats()
        logger.info(f"Swarm coordination stats: {stats}")
        
        # Verify performance
        assert stats["response_times"]["mean"] < 500  # Mean under 500ms
        assert stats["memory_operations"]["mean"] < 1000  # Mean under 1s
        assert stats["errors"]["count"] == 0  # No errors

@pytest.mark.performance
class TestProfilePerformance:
    """Test profile system performance."""
    
    @pytest.mark.asyncio
    async def test_profile_operations(
        self,
        performance_metrics: PerformanceMetrics
    ):
        """Test profile operation performance."""
        profile_store = ProfileStore(uri="bolt://localhost:7687")
        
        # Generate test profiles
        profiles = []
        for i in range(50):
            start = time.time()
            
            # Store profile
            result = await profile_store.store_profile({
                "personality": {
                    "openness": 0.8,
                    "conscientiousness": 0.7,
                    "extraversion": 0.6,
                    "agreeableness": 0.75,
                    "neuroticism": 0.4
                },
                "learning_style": {
                    "visual": 0.8,
                    "auditory": 0.6,
                    "kinesthetic": 0.7
                },
                "communication_preferences": {
                    "detail_level": "high",
                    "feedback_frequency": "frequent",
                    "interaction_style": "collaborative"
                }
            })
            
            end = time.time()
            performance_metrics.add_response_time((end - start) * 1000)
            
            if result["storage_status"] == "success":
                profiles.append(result["profile_id"])
            else:
                performance_metrics.add_error(f"Profile storage failed: {result.get('error')}")
        
        # Test preference updates
        for profile_id in profiles:
            start = time.time()
            
            await profile_store.update_preferences(
                profile_id,
                {
                    "theme": "dark",
                    "message_density": "compact",
                    "auto_approval": {
                        "task_creation": True,
                        "memory_operations": False
                    }
                }
            )
            
            end = time.time()
            performance_metrics.add_memory_operation((end - start) * 1000)
        
        # Get and log statistics
        stats = performance_metrics.get_stats()
        logger.info(f"Profile operation stats: {stats}")
        
        # Verify performance
        assert stats["response_times"]["p95"] < 500  # 95th percentile under 500ms
        assert stats["memory_operations"]["mean"] < 200  # Mean under 200ms
        assert stats["errors"]["count"] == 0  # No errors

@pytest.mark.performance
class TestGraphPerformance:
    """Test graph system performance."""
    
    @pytest.mark.asyncio
    async def test_graph_operations(
        self,
        performance_metrics: PerformanceMetrics
    ):
        """Test graph operation performance."""
        graph_store = GraphStore(uri="bolt://localhost:7687")
        
        # Create test nodes and relationships
        start = time.time()
        for i in range(1000):
            await graph_store.run_query(
                """
                CREATE (n:TestNode {
                    id: $id,
                    type: 'test',
                    relevance: $relevance,
                    created_at: datetime()
                })
                """,
                parameters={
                    "id": f"node_{i}",
                    "relevance": 0.5 + (i % 10) * 0.05
                }
            )
        end = time.time()
        performance_metrics.add_memory_operation((end - start) * 1000)
        
        # Create relationships
        start = time.time()
        await graph_store.run_query(
            """
            MATCH (n:TestNode)
            WITH collect(n) as nodes
            UNWIND range(0, size(nodes)-2) as i
            WITH nodes[i] as n1, nodes[i+1] as n2
            CREATE (n1)-[:RELATES_TO]->(n2)
            """
        )
        end = time.time()
        performance_metrics.add_memory_operation((end - start) * 1000)
        
        # Test graph operations
        operations = [
            # Prune graph
            graph_store.prune_graph(
                min_relevance=0.7,
                max_age_days=30,
                exclude_domains=["critical"]
            ),
            # Check health
            graph_store.check_health(),
            # Get statistics
            graph_store.get_statistics(),
            # Create backup
            graph_store.create_backup(
                include_domains=["test"],
                backup_format="cypher",
                compression=True
            )
        ]
        
        # Run operations concurrently
        start = time.time()
        results = await asyncio.gather(*operations)
        end = time.time()
        
        performance_metrics.add_response_time((end - start) * 1000)
        
        # Verify results
        for result in results:
            if isinstance(result, dict) and "error" in result:
                performance_metrics.add_error(str(result["error"]))
        
        # Get and log statistics
        stats = performance_metrics.get_stats()
        logger.info(f"Graph operation stats: {stats}")
        
        # Verify performance
        assert stats["memory_operations"]["mean"] < 5000  # Mean under 5s
        assert stats["response_times"]["mean"] < 10000  # Mean under 10s
        assert stats["errors"]["count"] == 0  # No errors

@pytest.mark.performance
class TestAgentPerformance:
    """Test agent system performance."""
    
    @pytest.mark.asyncio
    async def test_agent_operations(
        self,
        performance_metrics: PerformanceMetrics
    ):
        """Test agent operation performance."""
        agent_store = AgentStore(uri="bolt://localhost:7687")
        
        # Create test agents
        agents = []
        for i in range(100):
            agent_id = f"agent_{i}"
            capabilities = [
                "analysis",
                "validation",
                "coordination",
                "task_execution"
            ]
            
            start = time.time()
            
            # Create agent node
            await agent_store.run_query(
                """
                CREATE (a:Agent {
                    id: $id,
                    type: 'specialized',
                    capabilities: $capabilities,
                    status: 'active',
                    created_at: datetime()
                })
                """,
                parameters={
                    "id": agent_id,
                    "capabilities": capabilities
                }
            )
            
            end = time.time()
            performance_metrics.add_response_time((end - start) * 1000)
            agents.append(agent_id)
        
        # Test concurrent operations
        async def run_agent_operations(agent_id):
            """Run operations for an agent."""
            try:
                start = time.time()
                
                # Get capabilities
                await agent_store.get_capabilities(agent_id)
                
                # Get metrics
                await agent_store.get_metrics(agent_id)
                
                # Update status
                await agent_store.set_status(agent_id, "inactive")
                
                end = time.time()
                performance_metrics.add_memory_operation((end - start) * 1000)
                return True
            except Exception as e:
                performance_metrics.add_error(str(e))
                return False
        
        # Run concurrent operations
        tasks = [
            asyncio.create_task(run_agent_operations(agent_id))
            for agent_id in agents
        ]
        
        results = await asyncio.gather(*tasks)
        performance_metrics.add_concurrent_ops(len([r for r in results if r]))
        
        # Get and log statistics
        stats = performance_metrics.get_stats()
        logger.info(f"Agent operation stats: {stats}")
        
        # Verify performance
        assert stats["response_times"]["p95"] < 500  # 95th percentile under 500ms
        assert stats["memory_operations"]["mean"] < 1000  # Mean under 1s
        assert stats["concurrent_operations"]["total"] == 100  # All ops successful
        assert stats["errors"]["count"] == 0  # No errors
