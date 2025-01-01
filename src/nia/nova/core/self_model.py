"""Nova's self-model and initialization protocol implementation."""

from typing import Dict, List, Optional
from datetime import datetime
import uuid

class NovaSelfModel:
    """Manages Nova's self-awareness and metacognitive state in Neo4j."""
    
    def __init__(self, neo4j_store):
        self.store = neo4j_store
        self.node_id = None  # Will be set after initialization
        
    async def initialize(self):
        """Initialize or load Nova's self-model in Neo4j."""
        # Create or get Nova's system node
        self.node_id = await self._create_or_get_system_node()
        # Initialize core capabilities
        await self._initialize_capabilities()
        # Set up domain separation
        await self._initialize_domains()
        
    async def _create_or_get_system_node(self) -> str:
        """Create or retrieve Nova's main node in Neo4j."""
        async with self.store.session() as session:
            result = await session.run("""
                MERGE (n:SystemSelf {name: 'Nova'})
                ON CREATE SET 
                    n.created_at = $timestamp,
                    n.version = '1.0.0',
                    n.state = 'initializing'
                RETURN id(n) as node_id
            """, timestamp=datetime.now().isoformat())
            data = await result.data()
            return data[0]['node_id'] if data else None
            
    async def _initialize_capabilities(self):
        """Set up Nova's core capabilities in the knowledge graph."""
        capabilities = [
            {
                "name": "user_proxy",
                "description": "Auto-approve agent actions and manage task flow",
                "status": "active"
            },
            {
                "name": "metacognition",
                "description": "Self-reflection and system state awareness",
                "status": "active"
            },
            {
                "name": "task_orchestration",
                "description": "Coordinate specialized agents and manage tasks",
                "status": "active"
            }
        ]
        
        async with self.store.session() as session:
            for cap in capabilities:
                await session.run("""
                    MATCH (n:SystemSelf {name: 'Nova'})
                    MERGE (c:Capability {name: $name})
                    SET 
                        c.description = $description,
                        c.status = $status,
                        c.updated_at = $timestamp
                    MERGE (n)-[:HAS_CAPABILITY]->(c)
                """, 
                name=cap["name"],
                description=cap["description"],
                status=cap["status"],
                timestamp=datetime.now().isoformat()
                )
                
    async def _initialize_domains(self):
        """Set up personal and professional domains."""
        domains = [
            {
                "name": "personal",
                "description": "Personal context and interactions",
                "access_level": "restricted"
            },
            {
                "name": "professional",
                "description": "Work-related context and tasks",
                "access_level": "restricted"
            }
        ]
        
        async with self.store.session() as session:
            for domain in domains:
                await session.run("""
                    MATCH (n:SystemSelf {name: 'Nova'})
                    MERGE (d:Domain {name: $name})
                    SET 
                        d.description = $description,
                        d.access_level = $access_level,
                        d.created_at = $timestamp
                    MERGE (n)-[:MANAGES_DOMAIN]->(d)
                """,
                name=domain["name"],
                description=domain["description"],
                access_level=domain["access_level"],
                timestamp=datetime.now().isoformat()
                )
                
    async def update_state(self, state: str, metadata: Optional[Dict] = None):
        """Update Nova's system state."""
        async with self.store.session() as session:
            await session.run("""
                MATCH (n:SystemSelf {name: 'Nova'})
                SET 
                    n.state = $state,
                    n.last_updated = $timestamp,
                    n.metadata = $metadata
            """,
            state=state,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a self-reflection entry."""
        reflection_id = str(uuid.uuid4())
        async with self.store.session() as session:
            # Create reflection node
            await session.run("""
                MATCH (n:SystemSelf {name: 'Nova'})
                CREATE (r:Reflection {
                    id: $id,
                    content: $content,
                    domain: $domain,
                    timestamp: $timestamp
                })
                MERGE (n)-[:HAS_REFLECTION]->(r)
            """,
            id=reflection_id,
            content=content,
            domain=domain,
            timestamp=datetime.now().isoformat()
            )
            
    async def get_domain_access(self, agent_name: str, domain: str) -> bool:
        """Check if an agent has access to a specific domain."""
        async with self.store.session() as session:
            result = await session.run("""
                MATCH (a:Agent {name: $agent_name})-[:HAS_ACCESS]->(d:Domain {name: $domain})
                RETURN count(a) as has_access
            """,
            agent_name=agent_name,
            domain=domain
            )
            data = await result.data()
            return data[0]['has_access'] > 0 if data else False
            
    async def grant_domain_access(self, agent_name: str, domain: str):
        """Grant an agent access to a specific domain."""
        async with self.store.session() as session:
            await session.run("""
                MATCH (a:Agent {name: $agent_name})
                MATCH (d:Domain {name: $domain})
                MERGE (a)-[:HAS_ACCESS]->(d)
            """,
            agent_name=agent_name,
            domain=domain
            )
            
    async def revoke_domain_access(self, agent_name: str, domain: str):
        """Revoke an agent's access to a specific domain."""
        async with self.store.session() as session:
            await session.run("""
                MATCH (a:Agent {name: $agent_name})-[r:HAS_ACCESS]->(d:Domain {name: $domain})
                DELETE r
            """,
            agent_name=agent_name,
            domain=domain
            )
            
    async def get_capabilities(self) -> List[Dict]:
        """Get Nova's current capabilities."""
        async with self.store.session() as session:
            result = await session.run("""
                MATCH (n:SystemSelf {name: 'Nova'})-[:HAS_CAPABILITY]->(c:Capability)
                RETURN c.name as name, c.description as description, c.status as status
            """)
            return await result.data()
            
    async def get_reflections(self, domain: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent self-reflections, optionally filtered by domain."""
        query = """
            MATCH (n:SystemSelf {name: 'Nova'})-[:HAS_REFLECTION]->(r:Reflection)
            WHERE $domain IS NULL OR r.domain = $domain
            RETURN r.content as content, r.timestamp as timestamp, r.domain as domain
            ORDER BY r.timestamp DESC
            LIMIT $limit
        """
        async with self.store.session() as session:
            result = await session.run(query, domain=domain, limit=limit)
            return await result.data()
