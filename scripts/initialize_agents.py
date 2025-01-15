"""Initialize default agents in the store."""

import asyncio
import sys
import os
import logging
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.memory.agent_store import AgentStore
from src.nia.core.types.memory_types import (
    Domain,
    BaseDomain,
    KnowledgeVertical, 
    Memory, 
    MemoryType,
    ValidationSchema,
    CrossDomainSchema,
    DomainContext
)
from src.nia.core.neo4j.base_store import Neo4jBaseStore

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Only show warnings and errors
logger = logging.getLogger(__name__)

# Create session-specific log directory
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("test_results/initialization_logs")
log_dir.mkdir(parents=True, exist_ok=True)

def log_breakpoint(phase: str, data: dict = None):
    """Log a breakpoint with optional data."""
    timestamp = datetime.now().isoformat()
    log_file = log_dir / f"session_{session_id}_{phase}.json"
    
    log_entry = {
        "timestamp": timestamp,
        "phase": phase,
        "data": data or {}
    }
    
    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2)
    
    # Only log phase transitions to console
    logger.warning(f"Phase complete: {phase}")

async def verify_prerequisites(session_id: str):
    """Verify that all prerequisites are in place."""
    store = Neo4jBaseStore()
    try:
        await store.connect()
        
        # Check Neo4j schema
        schema_result = await store.run_query("""
        SHOW CONSTRAINTS
        """)
        constraints = schema_result
        required_constraints = ["agent_id", "task_id", "task_state"]
        for constraint in required_constraints:
            if not any(c["name"] == constraint for c in constraints):
                raise ValueError(f"Missing required constraint: {constraint}")
                
        # Check basic concepts
        concept_result = await store.run_query("""
        MATCH (c:Concept)
        WHERE c.name IN ['Belief', 'Desire', 'Emotion']
        RETURN count(c) as count
        """)
        if not concept_result or not concept_result[0] or concept_result[0]["count"] < 3:
            raise ValueError("Missing basic concepts")
            
        # Check task structures
        task_result = await store.run_query("""
        MATCH (s:TaskState)
        RETURN count(s) as count
        """)
        if not task_result or not task_result[0] or task_result[0]["count"] < 4:
            raise ValueError("Missing task states")
            
        # Log successful verification
        log_breakpoint("prerequisites_check", {
            "session_id": session_id,
            "constraints": [c["name"] for c in constraints],
            "concepts": concept_result[0]["count"] if concept_result and concept_result[0] else 0,
            "task_states": task_result[0]["count"] if task_result and task_result[0] else 0
        })
        
        # Success logged to JSON, no need for console output
        return True
        
    except Exception as e:
        logger.error(f"Prerequisite check failed: {str(e)}")
        logger.error("""
        Please run the following scripts in order:
        1. python scripts/initialize.py
        2. python scripts/init_neo4j.py
        3. python scripts/initialize_graph.py
        4. python scripts/initialize_knowledge.py
        """)
        return False
    finally:
        await store.close()

async def initialize_agents(session_id: str = None):
    """Initialize default agents in the store."""
    if session_id is None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_store = None
    try:
        # Verify prerequisites
        if not await verify_prerequisites(session_id):
            logger.error("Prerequisites check failed")
            return
            
        agent_store = AgentStore()
        await agent_store.connect()
        # First clean up existing data
        cleanup_query = """
        MATCH (n:Agent)
        DETACH DELETE n
        """
        await agent_store.run_query(cleanup_query)
        # Success logged to JSON, no need for console output
        
        # Initialize all implemented agents
        default_agents = [
            # Nova Team (Core) - Matching AgentType.SYSTEM
            {
                "id": "nova-team",
                "name": "NovaTeam",
                "type": "system",  # AgentType.SYSTEM
                "workspace": "system",  # AgentWorkspace.SYSTEM
                "domain": "general",  # AgentDomain.GENERAL
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "system",
                    "capabilities": [
                        "task_detection",
                        "thread_management",
                        "agent_spawning",
                        "memory_coordination",
                        "swarm_orchestration",
                        "emergent_task_detection",
                        "llm_integration",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query",
                        "memory_consolidate"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 1.0,
                    "specialization": "coordination",
                    "visualization": {
                        "position": "center",
                        "category": "orchestrator"
                    },
                    "memory_access": {
                        "episodic": True,
                        "semantic": True,
                        "consolidation": True
                    },
                    "swarm_patterns": [
                        "hierarchical",
                        "parallel",
                        "sequential",
                        "mesh"
                    ],
                    "thread_capabilities": {
                        "sub_threads": True,
                        "summarization": True,
                        "message_tracking": True,
                        "status_management": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.GENERAL,
                        access_domain=BaseDomain.GENERAL,
                        confidence=1.0,
                        source="system",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            source_domain=BaseDomain.GENERAL,
                            target_domain=BaseDomain.PROFESSIONAL
                        )
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "COORDINATES",  # AgentRelationType.COORDINATES
                        "target_id": "task-agent-1",
                        "properties": {"type": "functional"}
                    },
                    {
                        "type": "COORDINATES",
                        "target_id": "thread-agent-1",
                        "properties": {"type": "functional"}
                    }
                ]
            },
            
            # Task Management Agent - Matching AgentType.AGENT
            {
                "id": "task-agent-1",
                "name": "TaskAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "tasks",  # AgentDomain.TASKS
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "task",
                    "capabilities": [
                        "task_coordination",
                        "thread_management",
                        "resource_management",
                        "dependency_tracking",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "specialization": "task_management",
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "task_capabilities": {
                        "creation": True,
                        "assignment": True,
                        "tracking": True,
                        "resource_allocation": True,
                        "dependency_management": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.9,
                        source="system",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            source_domain=BaseDomain.PROFESSIONAL,
                            target_domain=BaseDomain.GENERAL
                        )
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "MANAGES",  # AgentRelationType.MANAGES
                        "target_id": "thread-agent-1",
                        "properties": {"type": "task_management"}
                    }
                ]
            },
            
            # Thread Management Agent - Matching AgentType.AGENT
            {
                "id": "thread-agent-1",
                "name": "ThreadAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "chat",  # AgentDomain.CHAT
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "thread",
                    "capabilities": [
                        "thread_coordination",
                        "message_management",
                        "summarization",
                        "layer_sync",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "specialization": "thread_management",
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "thread_capabilities": {
                        "creation": True,
                        "sub_threads": True,
                        "message_tracking": True,
                        "summarization": True,
                        "status_management": True,
                        "layer_sync": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.9,
                        source="system",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            source_domain=BaseDomain.PROFESSIONAL,
                            target_domain=BaseDomain.GENERAL
                        )
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "MANAGES",  # AgentRelationType.MANAGES
                        "target_id": "dialogue-agent-1",
                        "properties": {"type": "thread_management"}
                    }
                ]
            },
            
            # Communication Agent - Matching AgentType.AGENT
            {
                "id": "dialogue-agent-1",
                "name": "DialogueAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "chat",  # AgentDomain.CHAT
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "dialogue",
                    "capabilities": [
                        "thread_context",
                        "message_routing",
                        "conversation_tracking",
                        "llm_integration",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.8,
                    "specialization": "communication",
                    "memory_access": {
                        "episodic": True
                    },
                    "thread_capabilities": {
                        "message_posting": True,
                        "context_tracking": True,
                        "summarization": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.8,
                        source="system"
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "COLLABORATES_WITH",  # AgentRelationType.COLLABORATES_WITH
                        "target_id": "thread-agent-1",
                        "properties": {"type": "communication"}
                    }
                ]
            },
            
            # Coordination Agent - Matching AgentType.AGENT
            {
                "id": "coordination-agent-1",
                "name": "CoordinationAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "general",  # AgentDomain.GENERAL
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "coordination",
                    "capabilities": [
                        "agent_coordination",
                        "message_handling",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "specialization": "coordination",
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.9,
                        source="system",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            source_domain=BaseDomain.PROFESSIONAL,
                            target_domain=BaseDomain.GENERAL
                        )
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "COORDINATES",  # AgentRelationType.COORDINATES
                        "target_id": "analytics-agent-1",
                        "properties": {"type": "coordination"}
                    },
                    {
                        "type": "COORDINATES",  # AgentRelationType.COORDINATES
                        "target_id": "parsing-agent-1",
                        "properties": {"type": "coordination"}
                    }
                ]
            },
            # Analytics Agent - Matching AgentType.AGENT
            {
                "id": "analytics-agent-1",
                "name": "AnalyticsAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "analysis",  # AgentDomain.ANALYSIS
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "analytics",
                    "capabilities": [
                        "metrics_tracking",
                        "data_analysis",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "specialization": "analytics",
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.9,
                        source="system"
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "ASSISTS",  # AgentRelationType.ASSISTS
                        "target_id": "coordination-agent-1",
                        "properties": {"type": "analytics"}
                    },
                    {
                        "type": "COLLABORATES_WITH",  # AgentRelationType.COLLABORATES_WITH
                        "target_id": "parsing-agent-1",
                        "properties": {"type": "data_processing"}
                    }
                ]
            },
            # Parsing Agent - Matching AgentType.AGENT
            {
                "id": "parsing-agent-1",
                "name": "ParsingAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "analysis",  # AgentDomain.ANALYSIS
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "parsing",
                    "capabilities": [
                        "content_parsing",
                        "data_extraction",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "specialization": "parsing",
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.9,
                        source="system"
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "ASSISTS",  # AgentRelationType.ASSISTS
                        "target_id": "coordination-agent-1",
                        "properties": {"type": "parsing"}
                    },
                    {
                        "type": "COLLABORATES_WITH",  # AgentRelationType.COLLABORATES_WITH
                        "target_id": "analytics-agent-1",
                        "properties": {"type": "data_processing"}
                    }
                ]
            },
            # Orchestration Agent - Matching AgentType.AGENT
            {
                "id": "orchestration-agent-1",
                "name": "OrchestrationAgent",
                "type": "agent",  # AgentType.AGENT
                "workspace": "personal",  # AgentWorkspace.PERSONAL
                "domain": "general",  # AgentDomain.GENERAL
                "status": "active",  # AgentStatus.ACTIVE
                "metadata": {
                    "type": "orchestration",
                    "capabilities": [
                        "task_orchestration",
                        "agent_coordination",
                        "memory_store",
                        "memory_recall",
                        "memory_reflect",
                        "memory_query"
                    ],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "specialization": "orchestration",
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "validation": ValidationSchema(
                        domain=BaseDomain.PROFESSIONAL,
                        access_domain=BaseDomain.PROFESSIONAL,
                        confidence=0.9,
                        source="system",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            source_domain=BaseDomain.PROFESSIONAL,
                            target_domain=BaseDomain.GENERAL
                        )
                    ).dict()
                },
                "relationships": [
                    {
                        "type": "COORDINATES",  # AgentRelationType.COORDINATES
                        "target_id": "coordination-agent-1",
                        "properties": {"type": "orchestration"}
                    },
                    {
                        "type": "DELEGATES_TO",  # AgentRelationType.DELEGATES_TO
                        "target_id": "task-agent-1",
                        "properties": {"type": "task_execution"}
                    }
                ]
            }
        ]
        
        # Store each agent
        for agent in default_agents:
            # Progress tracked in JSON logs
            success = await agent_store.store_agent(agent)
            if success:
                # Success logged to JSON, no need for console
                # Log successful agent creation
                log_breakpoint(f"agent_creation_{agent['id']}", {
                    "session_id": session_id,
                    "agent_id": agent["id"],
                    "agent_type": agent["type"],
                    "domain": agent["domain"],
                    "capabilities": agent["metadata"]["capabilities"]
                })
            else:
                logger.error(f"Failed to store agent: {agent['name']}")
                
        # Create agent visualization relationships
        # Progress tracked in JSON logs
        
        # First create constraint in a separate query
        try:
            constraint_query = """
            CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:AgentNode) REQUIRE a.id IS UNIQUE
            """
            await agent_store.run_query(constraint_query)
            # Success logged to JSON, no need for console output
        except Exception as e:
            logger.error(f"Error creating constraint: {str(e)}")
            
        # Then create visualization nodes and relationships
        try:
            # Create visualization nodes
            viz_query = """
            // Match Nova team and create visualization node
            MATCH (nova:Agent {id: 'nova-team'})
            MERGE (novaViz:AgentNode {id: nova.id})
            SET novaViz = nova.metadata.visualization;
            
            // Create visualization nodes for all agents
            MATCH (agent:Agent)
            WHERE agent.id <> 'nova-team'
            MERGE (agentViz:AgentNode {id: agent.id})
            SET agentViz = agent.metadata.visualization;
            """
            await agent_store.run_query(viz_query)
            # Success logged to JSON, no need for console
            # Log visualization structure
            log_breakpoint("visualization_creation", {
                "session_id": session_id,
                "nodes": {
                    "nova": "center",
                    "inner": [a["id"] for a in default_agents if a["metadata"]["visualization"]["position"] == "inner"],
                    "outer": [a["id"] for a in default_agents if a["metadata"]["visualization"]["position"] == "outer"]
                }
            })
            
            # Create relationships in separate queries
            relationship_queries = [
                # Connect Nova to inner circle agents
                """
                MATCH (novaViz:AgentNode {position: 'center'})
                MATCH (innerAgent:AgentNode {position: 'inner'})
                MERGE (novaViz)-[:COORDINATES {type: 'visualization'}]->(innerAgent)
                """,
                
                # Connect Nova to outer circle agents
                """
                MATCH (novaViz:AgentNode {position: 'center'})
                MATCH (outerAgent:AgentNode {position: 'outer'})
                MERGE (novaViz)-[:COORDINATES {type: 'visualization'}]->(outerAgent)
                """,
                
                # Connect agents within same category
                """
                MATCH (a:AgentNode)
                MATCH (b:AgentNode)
                WHERE a.category = b.category AND a <> b
                MERGE (a)-[:COLLABORATES {type: 'visualization'}]->(b)
                """
            ]
            
            for i, query in enumerate(relationship_queries, 1):
                try:
                    await agent_store.run_query(query)
                    # Success logged to JSON, no need for console
                except Exception as e:
                    logger.error(f"Error creating relationship set {i}: {str(e)}")
                    
            # Success logged to JSON, no need for console
        except Exception as e:
            logger.error(f"Error creating visualization structure: {str(e)}")
            
        # Create functional relationships
        try:
            functional_queries = [
                # Nova Team coordinates all agents
                """
                MATCH (nova:Agent {id: 'nova-team'})
                MATCH (agent:Agent)
                WHERE agent.id <> 'nova-team'
                MERGE (nova)-[:COORDINATES {type: 'functional'}]->(agent)
                """,
                
                # Task management relationships
                """
                MATCH (task:Agent {agentType: 'task'})
                MATCH (agent:Agent)
                WHERE agent.id <> task.id 
                AND 'task_participation' IN agent.metadata.capabilities
                MERGE (task)-[:MANAGES_TASKS {type: 'functional'}]->(agent)
                """,
                
                # Thread management relationships
                """
                MATCH (thread:Agent {agentType: 'thread'})
                MATCH (agent:Agent)
                WHERE 'thread_context' IN agent.metadata.capabilities
                MERGE (thread)-[:MANAGES_THREADS {type: 'functional'}]->(agent)
                """,
                
                # Memory sync relationships
                """
                MATCH (a:Agent)
                MATCH (b:Agent)
                WHERE 'layer_sync' IN a.metadata.capabilities
                AND 'layer_sync' IN b.metadata.capabilities
                AND a <> b
                MERGE (a)-[:SYNCS_MEMORY {type: 'functional'}]->(b)
                """,
                
                # Memory operations relationships
                """
                MATCH (a:Agent)
                MATCH (b:Agent)
                WHERE 'memory_store' IN a.metadata.capabilities
                AND 'memory_store' IN b.metadata.capabilities
                AND a <> b
                MERGE (a)-[:SHARES_MEMORY {type: 'functional'}]->(b)
                """
            ]
            
            for i, query in enumerate(functional_queries, 1):
                try:
                    await agent_store.run_query(query)
                    # Progress tracked in JSON logs
                except Exception as e:
                    logger.error(f"Error creating functional relationship set {i}: {str(e)}")
                    
            # Success logged to JSON, no need for console
            # Log relationship creation
            log_breakpoint("relationship_creation", {
                "session_id": session_id,
                "relationships": {
                    "coordinates": len([q for q in functional_queries if "COORDINATES" in q]),
                    "manages_tasks": len([q for q in functional_queries if "MANAGES_TASKS" in q]),
                    "manages_threads": len([q for q in functional_queries if "MANAGES_THREADS" in q]),
                    "syncs_memory": len([q for q in functional_queries if "SYNCS_MEMORY" in q]),
                    "shares_memory": len([q for q in functional_queries if "SHARES_MEMORY" in q])
                }
            })
        except Exception as e:
            logger.error(f"Error creating functional relationships: {str(e)}")
            
        # Verify agents and relationships
        all_agents = await agent_store.get_all_agents()
        # Success details logged to JSON, no need for console listing
            
        # Verify relationships
        rel_query = """
        MATCH (a:Agent)-[r]->(b)
        RETURN count(r) as rel_count
        """
        try:
            result = await agent_store.run_query(rel_query)
            if result and result[0]:
                # Log final verification
                log_breakpoint("verification", {
                    "session_id": session_id,
                    "total_agents": len(all_agents),
                    "total_relationships": result[0]["rel_count"],
                    "agent_types": {
                        agent_type: len([a for a in all_agents if a["type"] == agent_type])
                        for agent_type in set(a["type"] for a in all_agents)
                    }
                })
        except Exception as e:
            logger.error(f"Error counting relationships: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error initializing agents: {str(e)}")
        raise
    finally:
        if agent_store is not None:
            await agent_store.close()

if __name__ == "__main__":
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    asyncio.run(initialize_agents(session_id))
