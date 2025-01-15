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
        concept_data = await concept_result.single()
        if concept_data["count"] < 3:
            raise ValueError("Missing basic concepts")
            
        # Check task structures
        task_result = await store.run_query("""
        MATCH (s:TaskState)
        RETURN count(s) as count
        """)
        task_data = await task_result.single()
        if task_data["count"] < 4:
            raise ValueError("Missing task states")
            
        # Log successful verification
        log_breakpoint("prerequisites_check", {
            "session_id": session_id,
            "constraints": [c["name"] for c in constraints],
            "concepts": concept_data["count"],
            "task_states": task_data["count"]
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

async def create_system_thread(memory_system, session_id: str):
    """Create system thread for Nova Team if it doesn't exist."""
    thread_id = "00000000-0000-4000-a000-000000000001"  # Fixed ID for system thread
    
    # Check if thread exists in episodic memory
    episodic_exists = await memory_system.get_experience_by_thread(thread_id)
    
    # Check if thread exists in semantic memory
    semantic_exists = False
    if memory_system.semantic:
        semantic_exists = await memory_system.semantic.get_memory_by_thread(thread_id)
    
    if episodic_exists and (semantic_exists or not memory_system.semantic):
        # Thread already exists in required layers
        log_breakpoint("system_thread_exists", {
            "session_id": session_id,
            "thread_id": thread_id,
            "episodic_exists": True,
            "semantic_exists": semantic_exists,
            "semantic_enabled": bool(memory_system.semantic)
        })
        return thread_id
        
    # Create memory content
    memory_content = {
        "thread_id": thread_id,
        "name": "Nova Team Thread",
        "type": "system",
        "domain": BaseDomain.SYSTEM,
        "messages": [],
        "participants": []
    }
    
    # Create thread memory
    memory_id = str(uuid.uuid4())
    domain_context = DomainContext(
        primary_domain=BaseDomain.SYSTEM,
        knowledge_vertical=KnowledgeVertical.TECHNOLOGY,
        validation=ValidationSchema(
            domain=BaseDomain.SYSTEM,
            access_domain=BaseDomain.SYSTEM,
            confidence=1.0,
            source="system",
            cross_domain=CrossDomainSchema(
                approved=True,
                source_domain=BaseDomain.SYSTEM,
                target_domain=BaseDomain.PROFESSIONAL
            )
        )
    )
    
    thread_memory = Memory(
        id=memory_id,
        content=memory_content,
        type=MemoryType.EPISODIC,
        importance=1.0,
        timestamp=datetime.now(timezone.utc),
        context={
            "domain": BaseDomain.SYSTEM,
            "source": "system",
            "type": MemoryType.EPISODIC.value,
            "workspace": "system"
        },
        consolidated=False,
        domain_context=domain_context
    )
    
    try:
        # Store in episodic if needed
        if not episodic_exists:
            await memory_system.store_experience(thread_memory)
            
        # Store in semantic if enabled and needed
        if memory_system.semantic and not semantic_exists:
            await memory_system.semantic.store_memory(thread_memory)
            
        # Log thread creation/update
        log_breakpoint("system_thread_creation", {
            "session_id": session_id,
            "thread_id": thread_id,
            "memory_id": memory_id,
            "episodic_stored": not episodic_exists,
            "semantic_stored": bool(memory_system.semantic and not semantic_exists)
        })
        
        return thread_id
    except Exception as e:
        logger.error(f"Failed to create/update system thread: {str(e)}")
        raise

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
        
        # Initialize memory system
        memory_system = agent_store.memory_system
        await memory_system.initialize()
        
        # Create system thread
        system_thread_id = await create_system_thread(memory_system, session_id)
        # First clean up existing data
        cleanup_query = """
        MATCH (n:Agent)
        DETACH DELETE n
        """
        await agent_store.run_query(cleanup_query)
        # Success logged to JSON, no need for console output
        
        # Initialize all implemented agents
        default_agents = [
            # Nova Team (Core)
            {
                "id": "nova-team",
                "name": "NovaTeam",
                "type": "nova",
                "workspace": "system",
                "domain": BaseDomain.SYSTEM,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "type": "agent-team",
                    "system": True,
                    "pinned": True,
                    "description": "Core Nova coordination team",
                    "capabilities": {
                        "task_detection": True,
                        "thread_management": True,
                        "agent_spawning": True,
                        "memory_coordination": True,
                        "swarm_orchestration": True,
                        "emergent_task_detection": True,
                        "llm_integration": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True,
                            "consolidate": True
                        }
                    },
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
                        domain=BaseDomain.SYSTEM,
                        access_domain=BaseDomain.SYSTEM,
                        confidence=1.0,
                        source="system",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            source_domain=BaseDomain.SYSTEM,
                            target_domain=BaseDomain.PROFESSIONAL
                        )
                    ).dict()
                },
                "skills": [
                    "task_orchestration",
                    "team_coordination",
                    "emergent_task_detection",
                    "memory_management",
                    "agent_lifecycle_management",
                    "thread_coordination",
                    "memory_consolidation"
                ]
            },
            
            # Task Management Agents
            {
                "id": "task-agent-1",
                "name": "TaskAgent",
                "type": "task",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "inner",
                        "category": "management"
                    },
                    "capabilities": {
                        "task_coordination": True,
                        "thread_management": True,
                        "resource_management": True,
                        "dependency_tracking": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
                    "memory_access": {
                        "episodic": True,
                        "semantic": True
                    },
                    "swarm_patterns": [
                        "hierarchical",
                        "parallel"
                    ],
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
                            target_domain=BaseDomain.SYSTEM
                        )
                    ).dict()
                },
                "skills": [
                    "task_tracking",
                    "dependency_management",
                    "resource_allocation",
                    "thread_coordination",
                    "memory_management"
                ]
            },
            
            # Thread Management Agents
            {
                "id": "thread-agent-1",
                "name": "ThreadAgent",
                "type": "thread",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "inner",
                        "category": "management"
                    },
                    "capabilities": {
                        "thread_coordination": True,
                        "message_management": True,
                        "summarization": True,
                        "layer_sync": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
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
                            target_domain=BaseDomain.SYSTEM
                        )
                    ).dict()
                },
                "skills": [
                    "thread_management",
                    "message_coordination",
                    "summarization",
                    "memory_sync",
                    "memory_management"
                ]
            },
            
            # Communication Agents
            {
                "id": "dialogue-agent-1",
                "name": "DialogueAgent",
                "type": "dialogue",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "outer",
                        "category": "communication"
                    },
                    "capabilities": {
                        "thread_context": True,
                        "message_routing": True,
                        "conversation_tracking": True,
                        "llm_integration": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
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
                "skills": [
                    "conversation_management",
                    "context_tracking",
                    "thread_management",
                    "message_routing",
                    "memory_management"
                ]
            },
            
            # Base Agents
            {
                "id": "coordination-agent-1",
                "name": "CoordinationAgent",
                "type": "coordination",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "inner",
                        "category": "management"
                    },
                    "capabilities": {
                        "agent_coordination": True,
                        "message_handling": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
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
                            target_domain=BaseDomain.SYSTEM
                        )
                    ).dict()
                },
                "skills": [
                    "agent_coordination",
                    "message_handling",
                    "memory_management"
                ]
            },
            {
                "id": "analytics-agent-1",
                "name": "AnalyticsAgent",
                "type": "analytics",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    },
                    "capabilities": {
                        "metrics_tracking": True,
                        "data_analysis": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
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
                "skills": [
                    "metrics_tracking",
                    "data_analysis",
                    "memory_management"
                ]
            },
            {
                "id": "parsing-agent-1",
                "name": "ParsingAgent",
                "type": "parsing",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    },
                    "capabilities": {
                        "content_parsing": True,
                        "data_extraction": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
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
                "skills": [
                    "content_parsing",
                    "data_extraction",
                    "memory_management"
                ]
            },
            {
                "id": "orchestration-agent-1",
                "name": "OrchestrationAgent",
                "type": "orchestration",
                "workspace": "system",
                "domain": BaseDomain.PROFESSIONAL,
                "knowledge_vertical": KnowledgeVertical.TECHNOLOGY,
                "status": "active",
                "metadata": {
                    "visualization": {
                        "position": "inner",
                        "category": "management"
                    },
                    "capabilities": {
                        "task_orchestration": True,
                        "agent_coordination": True,
                        "memory_operations": {
                            "store": True,
                            "recall": True,
                            "reflect": True,
                            "query": True
                        }
                    },
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
                            target_domain=BaseDomain.SYSTEM
                        )
                    ).dict()
                },
                "skills": [
                    "task_orchestration",
                    "agent_coordination",
                    "memory_management"
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
                MATCH (task:Agent {type: 'task'})
                MATCH (agent:Agent)
                WHERE agent.id <> task.id AND agent.metadata.capabilities.task_participation = true
                MERGE (task)-[:MANAGES_TASKS {type: 'functional'}]->(agent)
                """,
                
                # Thread management relationships
                """
                MATCH (thread:Agent {type: 'thread'})
                MATCH (agent:Agent)
                WHERE agent.metadata.capabilities.thread_context = true
                MERGE (thread)-[:MANAGES_THREADS {type: 'functional'}]->(agent)
                """,
                
                # Memory sync relationships
                """
                MATCH (a:Agent)
                MATCH (b:Agent)
                WHERE a.metadata.capabilities.layer_sync = true 
                AND b.metadata.capabilities.layer_sync = true
                AND a <> b
                MERGE (a)-[:SYNCS_MEMORY {type: 'functional'}]->(b)
                """,
                
                # Memory operations relationships
                """
                MATCH (a:Agent)
                MATCH (b:Agent)
                WHERE a.metadata.capabilities.memory_operations.store = true
                AND b.metadata.capabilities.memory_operations.store = true
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
        await agent_store.close()

if __name__ == "__main__":
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    asyncio.run(initialize_agents(session_id))
