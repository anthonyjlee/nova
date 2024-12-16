"""
Neo4j-based memory store implementation.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)

class Neo4jMemoryStore:
    """Neo4j-based memory store with graph visualization."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password"
    ):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self._ensure_constraints()
    
    def _ensure_constraints(self) -> None:
        """Ensure required constraints exist."""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                "CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE"
            ]
            for constraint in constraints:
                session.run(constraint)
    
    async def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a memory in Neo4j."""
        memory_id = f"{memory_type}_{datetime.now().isoformat()}"
        
        # Create memory node
        query = """
        CREATE (m:Memory {
            id: $memory_id,
            type: $memory_type,
            content: $content,
            metadata: $metadata,
            created_at: datetime()
        })
        RETURN m
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                memory_id=memory_id,
                memory_type=memory_type,
                content=json.dumps(content),
                metadata=json.dumps(metadata or {})
            )
        
        # Extract and store concepts
        await self._extract_concepts(memory_id, content)
        
        return memory_id
    
    async def _extract_concepts(self, memory_id: str, content: Dict[str, Any]) -> None:
        """Extract and store concepts from memory content."""
        # Extract concepts based on memory content
        concepts = []
        
        if isinstance(content, dict):
            # Extract from beliefs
            if 'beliefs' in content:
                beliefs = content['beliefs']
                if isinstance(beliefs, dict):
                    if 'core_belief' in beliefs:
                        concepts.append({
                            'type': 'belief',
                            'content': beliefs['core_belief']
                        })
            
            # Extract from insights
            if 'insights' in content:
                insights = content['insights']
                if isinstance(insights, list):
                    for insight in insights:
                        concepts.append({
                            'type': 'insight',
                            'content': insight
                        })
            
            # Extract from patterns
            if 'patterns' in content:
                patterns = content['patterns']
                if isinstance(patterns, list):
                    for pattern in patterns:
                        concepts.append({
                            'type': 'pattern',
                            'content': pattern
                        })
        
        # Store concepts and relationships
        for concept in concepts:
            concept_id = f"{concept['type']}_{hash(concept['content'])}"
            
            query = """
            MERGE (c:Concept {id: $concept_id})
            ON CREATE SET
                c.type = $concept_type,
                c.content = $concept_content,
                c.created_at = datetime()
            WITH c
            MATCH (m:Memory {id: $memory_id})
            MERGE (m)-[r:HAS_CONCEPT]->(c)
            ON CREATE SET r.created_at = datetime()
            """
            
            with self.driver.session() as session:
                session.run(
                    query,
                    concept_id=concept_id,
                    concept_type=concept['type'],
                    concept_content=concept['content'],
                    memory_id=memory_id
                )
    
    async def store_task_execution(
        self,
        task_id: str,
        task_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> None:
        """Store task execution in Neo4j."""
        query = """
        CREATE (t:Task {
            id: $task_id,
            type: $task_type,
            content: $content,
            metadata: $metadata,
            created_at: datetime()
        })
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                task_id=task_id,
                task_type=task_type,
                content=json.dumps(content),
                metadata=json.dumps(metadata or {})
            )
    
    async def link_task_memory(self, task_id: str, memory_id: str) -> None:
        """Create relationship between task and memory."""
        query = """
        MATCH (t:Task {id: $task_id})
        MATCH (m:Memory {id: $memory_id})
        MERGE (t)-[r:GENERATED]->(m)
        ON CREATE SET r.created_at = datetime()
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                task_id=task_id,
                memory_id=memory_id
            )
    
    async def get_related_memories(
        self,
        content: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Get related memories using graph traversal."""
        # First, find concepts related to content
        concept_query = """
        MATCH (c:Concept)
        WHERE c.content CONTAINS $content
        WITH c
        MATCH (c)<-[r:HAS_CONCEPT]-(m:Memory)
        WHERE $memory_type IS NULL OR m.type = $memory_type
        RETURN m
        ORDER BY m.created_at DESC
        LIMIT $limit
        """
        
        memories = []
        with self.driver.session() as session:
            result = session.run(
                concept_query,
                content=content,
                memory_type=memory_type,
                limit=limit
            )
            
            for record in result:
                memory = record["m"]
                memories.append({
                    'id': memory['id'],
                    'type': memory['type'],
                    'content': json.loads(memory['content']),
                    'metadata': json.loads(memory['metadata']),
                    'created_at': memory['created_at']
                })
        
        return memories
    
    async def get_memory_graph(
        self,
        memory_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get memory graph for visualization."""
        query = """
        MATCH path = (m:Memory {id: $memory_id})-[*1..$depth]-(n)
        RETURN path
        """
        
        nodes = []
        edges = []
        
        with self.driver.session() as session:
            result = session.run(
                query,
                memory_id=memory_id,
                depth=depth
            )
            
            for record in result:
                path = record["path"]
                
                # Add nodes
                for node in path.nodes:
                    node_data = dict(node)
                    node_data['labels'] = list(node.labels)
                    nodes.append(node_data)
                
                # Add edges
                for rel in path.relationships:
                    edges.append({
                        'from': rel.start_node['id'],
                        'to': rel.end_node['id'],
                        'type': rel.type,
                        'properties': dict(rel)
                    })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def close(self) -> None:
        """Close Neo4j connection."""
        self.driver.close()
