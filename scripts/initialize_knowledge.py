#!/usr/bin/env python3
"""Initialize test knowledge graph data."""

import asyncio
import sys
import os
import json
from pathlib import Path
import logging
from datetime import datetime, timezone

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.neo4j.concept_store import ConceptStore
from src.nia.core.types.memory_types import (
    ValidationSchema,
    CrossDomainSchema,
    BaseDomain,
    KnowledgeVertical
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_task_structures(store: ConceptStore):
    """Initialize task-specific structures in Neo4j."""
    logger.info("Initializing task structures")
    
    # Create task state nodes matching TaskState enum
    states = [
        {
            "name": "PENDING",
            "description": "New or unstarted tasks",
            "value": "pending"
        },
        {
            "name": "IN_PROGRESS",
            "description": "Tasks currently being worked on",
            "value": "in_progress"
        },
        {
            "name": "BLOCKED",
            "description": "Tasks blocked by dependencies",
            "value": "blocked"
        },
        {
            "name": "COMPLETED",
            "description": "Finished tasks",
            "value": "completed"
        }
    ]
    
    for state in states:
        validation = ValidationSchema(
            domain=BaseDomain.GENERAL,
            access_domain=BaseDomain.GENERAL,
            confidence=1.0,
            source="system"
        ).dict()
        validation["metadata"] = {
            "enum_name": state["name"],
            "value": state["value"]
        }
        # Create task state directly instead of as a concept
        await store.run_query(
            """
            CREATE (s:TaskState {
                name: $name,
                description: $description,
                value: $value
            })
            """,
            {
                "name": f"TaskState_{state['value']}",
                "description": state["description"],
                "value": state["value"]
            }
        )
    
    # Create task constraints
    # Create task constraints
    await store.run_query("""
        CREATE CONSTRAINT task_id IF NOT EXISTS
        FOR (t:Task) REQUIRE t.id IS UNIQUE
    """)
    
    await store.run_query("""
        CREATE CONSTRAINT task_state IF NOT EXISTS
        FOR (s:TaskState) REQUIRE s.name IS UNIQUE
    """)
    
    # Create task templates matching frontend schema
    templates = [
        {
            "name": "development_task",
            "type": "entity",  # Task templates are entities in our concept model
            "description": "Software development task template",
            "domain": BaseDomain.PROFESSIONAL,
            "metadata": {
                "template": True,
                "category": "development",
                "default_state": "pending",
                "workspace": "professional",
                "priority": "medium",
                "capabilities": ["development", "coding", "testing"],
                "validation_rules": {
                    "requires_review": True,
                    "requires_testing": True
                }
            }
        },
        {
            "name": "organization_task",
            "type": "entity",  # Task templates are entities in our concept model
            "description": "Personal organization task template",
            "domain": BaseDomain.PERSONAL,
            "metadata": {
                "template": True,
                "category": "organization",
                "default_state": "pending",
                "workspace": "personal",
                "priority": "medium",
                "capabilities": ["organization", "planning", "tracking"],
                "validation_rules": {
                    "requires_review": False,
                    "requires_testing": False
                }
            }
        }
    ]
    
    for template in templates:
        validation = ValidationSchema(
            domain=template["domain"],
            access_domain=template["domain"],
            confidence=1.0,
            source="system"
        ).dict()
        validation["metadata"] = template["metadata"]
        await store.store_concept(
            name=template["name"],
            type=template["type"],
            description=template["description"],
            validation=validation
        )
    
    logger.info("Task structures initialized successfully")

async def clear_all_data(store: ConceptStore):
    """Clear all data from Neo4j."""
    logger.info("Clearing all existing data...")
    # Delete all nodes except the basic concepts
    await store.run_query("""
        MATCH (n)
        WHERE (NOT n:Concept OR NOT n.name IN ['Belief', 'Desire', 'Emotion'])
        DETACH DELETE n
    """)
    logger.info("All data cleared")

async def initialize_knowledge():
    """Initialize test knowledge graph data."""
    store = None
    try:
        store = ConceptStore(uri="bolt://localhost:7687", user="neo4j", password="password")
        await store.connect()
        logger.info("Connected to Neo4j")
        
        # Clear existing data
        await clear_all_data(store)
            
        logger.info("Knowledge graph is empty, initializing with test data")
        
        # Create test concepts with domain organization
        concepts = [
            # Technology Domain
            {
                "name": "Software Development",
                "type": "entity",
                "description": "The process of creating and maintaining software",
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
            {
                "name": "Python",
                "type": "entity",
                "description": "A high-level programming language",
                "validation": ValidationSchema(
                    domain=BaseDomain.PROFESSIONAL,
                    access_domain=BaseDomain.PROFESSIONAL,
                    confidence=1.0,
                    source="system"
                ).dict()
            },
            {
                "name": "Neo4j",
                "type": "entity",
                "description": "A graph database management system",
                "validation": ValidationSchema(
                    domain=BaseDomain.PROFESSIONAL,
                    access_domain=BaseDomain.PROFESSIONAL,
                    confidence=1.0,
                    source="system"
                ).dict()
            },
            
            # Personal Domain
            {
                "name": "Task Management",
                "type": "action",
                "description": "Organizing and prioritizing work",
                "validation": ValidationSchema(
                    domain=BaseDomain.PERSONAL,
                    access_domain=BaseDomain.PERSONAL,
                    confidence=0.8,
                    source="system",
                    cross_domain=CrossDomainSchema(
                        approved=True,
                        source_domain=BaseDomain.PERSONAL,
                        target_domain=BaseDomain.PROFESSIONAL
                    )
                ).dict()
            },
            {
                "name": "Time Management",
                "type": "action",
                "description": "Effective use of time for productivity",
                "validation": ValidationSchema(
                    domain=BaseDomain.PERSONAL,
                    access_domain=BaseDomain.PERSONAL,
                    confidence=0.8,
                    source="system"
                ).dict()
            },
            
            # Cross-Domain Concepts
            {
                "name": "Problem Solving",
                "type": "action",
                "description": "Ability to analyze and solve complex problems",
                "validation": ValidationSchema(
                    domain=BaseDomain.GENERAL,
                    access_domain=BaseDomain.GENERAL,
                    confidence=0.9,
                    source="system",
                    cross_domain=CrossDomainSchema(
                        approved=True,
                        requested=True,
                        source_domain=BaseDomain.PROFESSIONAL,
                        target_domain=BaseDomain.PERSONAL
                    )
                ).dict()
            }
        ]
        
        # Store concepts
        for concept in concepts:
            logger.info(f"Storing concept: {concept['name']}")
            await store.store_concept(
                name=concept["name"],
                type=concept["type"],
                description=concept["description"],
                validation=concept["validation"]
            )
            
        # Create relationships
        relationships = [
            # Technology relationships
            ("Python", "Software Development", "part_of"),
            ("Neo4j", "Software Development", "part_of"),
            
            # Skill relationships
            ("Task Management", "Time Management", "related_to"),
            ("Problem Solving", "Software Development", "required_for"),
            ("Problem Solving", "Task Management", "enhances"),
            
            # Cross-domain relationships
            ("Time Management", "Software Development", "improves"),
            ("Task Management", "Problem Solving", "requires")
        ]
        
        # Store relationships
        for source, target, rel_type in relationships:
            logger.info(f"Creating relationship: {source} -{rel_type}-> {target}")
            await store.store_relationship(
                source,
                target,
                rel_type
            )
            
        logger.info("Successfully initialized knowledge graph")
        
        # Create domain nodes
        domains = ["tasks", "professional", "personal"]
        for domain in domains:
            await store.run_query(
                """
                MERGE (d:Domain {name: $name})
                SET d.created = datetime()
                """,
                {"name": domain}
            )
            # Create access rule for domain
            await store.run_query(
                """
                MATCH (d:Domain {name: $name})
                MERGE (d)-[:HAS_RULE]->(r:AccessRule {type: 'domain_access'})
                SET r.created = datetime()
                """,
                {"name": domain}
            )
            
        # Initialize task structures
        await initialize_task_structures(store)
        
    except Exception as e:
        logger.error(f"Error initializing knowledge graph: {str(e)}")
        raise
    finally:
        await store.close()

async def create_test_data(store: ConceptStore):
    """Create test data for validation."""
    try:
        # Create test tasks
        test_tasks = [
            {
                "id": "TEST-001",
                "label": "Test Development Task",
                "type": "task",
                "status": "pending",
                "domain": "professional",
                "description": "A test task for development",
                "metadata": json.dumps({
                    "priority": "high",
                    "estimated_hours": 4
                })
            },
            {
                "id": "TEST-002",
                "label": "Test Personal Task",
                "type": "task",
                "status": "in_progress",
                "domain": "personal",
                "description": "A test task for organization",
                "metadata": json.dumps({
                    "priority": "medium",
                    "category": "organization"
                })
            }
        ]

        for task in test_tasks:
            await store.run_query(
                """
                CREATE (t:Task)
                SET t += $props
                """,
                {"props": task}
            )

        # Create test relationships
        await store.run_query(
            """
            MATCH (t1:Task {id: 'TEST-001'})
            MATCH (t2:Task {id: 'TEST-002'})
            CREATE (t1)-[:BLOCKS]->(t2)
            """
        )

        logger.info("Test data created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create test data: {str(e)}")
        return False

async def verify_initialization():
    """Verify that all required structures are properly initialized."""
    store = ConceptStore(uri="bolt://localhost:7687", user="neo4j", password="password")
    await store.connect()
    logger.info("Connected to Neo4j")
    try:
        # Check task states
        result = await store.run_query(
            "MATCH (s:TaskState) RETURN count(s) as count"
        )
        if not result or result[0]["count"] != 4:
            logger.error("Task states not properly initialized")
            return False
            
        # Check task templates
        result = await store.run_query(
            "MATCH (t:Concept) WHERE t.name IN ['development_task', 'organization_task'] RETURN count(t) as count"
        )
        if not result or result[0]["count"] < 2:
            logger.error("Task templates not properly initialized")
            return False
            
        # Check constraints
        result = await store.run_query(
            "SHOW CONSTRAINTS"
        )
        required_constraints = ["task_id", "task_state"]
        for constraint in required_constraints:
            if not any(c["name"] == constraint for c in result):
                logger.error(f"Missing required constraint: {constraint}")
                return False

        # Check domain boundaries
        result = await store.run_query(
            """
            MATCH (d:Domain)
            WHERE d.name IN ['tasks', 'professional', 'personal']
            RETURN count(d) as count
            """
        )
        if not result or result[0]["count"] != 3:
            logger.error("Domain boundaries not properly initialized")
            return False

        # Check access rules
        result = await store.run_query(
            """
            MATCH (d:Domain)-[:HAS_RULE]->(r:AccessRule)
            WHERE r.type = 'domain_access'
            RETURN count(r) as count
            """
        )
        if not result or result[0]["count"] != 3:
            logger.error("Access rules not properly initialized")
            return False

        # Create and verify test data
        if not await create_test_data(store):
            logger.error("Failed to create test data")
            return False

        # Verify test data
        result = await store.run_query(
            """
            MATCH (t:Task)
            WHERE t.id IN ['TEST-001', 'TEST-002']
            RETURN count(t) as count
            """
        )
        if not result or result[0]["count"] != 2:
            logger.error("Test data not properly created")
            return False

        logger.info("All required structures and test data verified successfully")
        return True
            
    except Exception as e:
        logger.error(f"Error verifying initialization: {str(e)}")
        return False
    finally:
        await store.close()

async def main():
    """Main execution function."""
    store = None
    try:
        store = ConceptStore(uri="bolt://localhost:7687", user="neo4j", password="password")
        await store.connect()
        await initialize_knowledge()
        # Verify initialization
        if not await verify_initialization():
            sys.exit(1)
    finally:
        if store:
            await store.close()

if __name__ == "__main__":
    asyncio.run(main())
