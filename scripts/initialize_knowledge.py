#!/usr/bin/env python3
"""Initialize test knowledge graph data."""

import asyncio
import sys
import os
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
    
    # Create task state nodes
    states = [
        {"name": "pending", "description": "New or unstarted tasks"},
        {"name": "in_progress", "description": "Tasks currently being worked on"},
        {"name": "blocked", "description": "Tasks blocked by dependencies"},
        {"name": "completed", "description": "Finished tasks"}
    ]
    
    for state in states:
        await store.store_concept(
            name=f"TaskState_{state['name']}",
            type="task_state",
            description=state["description"],
            validation=ValidationSchema(
                domain=BaseDomain.SYSTEM,
                access_domain=BaseDomain.SYSTEM,
                confidence=1.0,
                source="system"
            ).dict()
        )
    
    # Create task constraints
    async with store.driver.session() as session:
        await session.run("""
            CREATE CONSTRAINT task_id IF NOT EXISTS
            FOR (t:Task) REQUIRE t.id IS UNIQUE
        """)
        
        await session.run("""
            CREATE CONSTRAINT task_state IF NOT EXISTS
            FOR (s:TaskState) REQUIRE s.name IS UNIQUE
        """)
    
    # Create task templates
    templates = [
        {
            "name": "development_task",
            "type": "task_template",
            "description": "Software development task template",
            "domain": BaseDomain.PROFESSIONAL,
            "metadata": {
                "template": True,
                "category": "development",
                "default_state": "pending"
            }
        },
        {
            "name": "organization_task",
            "type": "task_template",
            "description": "Personal organization task template",
            "domain": BaseDomain.PERSONAL,
            "metadata": {
                "template": True,
                "category": "organization",
                "default_state": "pending"
            }
        }
    ]
    
    for template in templates:
        await store.store_concept(
            name=template["name"],
            type=template["type"],
            description=template["description"],
            validation=ValidationSchema(
                domain=template["domain"],
                access_domain=template["domain"],
                confidence=1.0,
                source="system"
            ).dict(),
            metadata=template["metadata"]
        )
    
    logger.info("Task structures initialized successfully")

async def initialize_knowledge():
    """Initialize test knowledge graph data if empty."""
    try:
        store = ConceptStore()
        
        # Check if concepts already exist
        query = "MATCH (c:Concept) RETURN count(c) as count"
        async with store.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            if record and record["count"] > 0:
                logger.info("Knowledge graph already contains concepts, skipping initialization")
                return
            
        logger.info("Knowledge graph is empty, initializing with test data")
        
        # Create test concepts with domain organization
        concepts = [
            # Technology Domain
            {
                "name": "Software Development",
                "type": "domain",
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
                "type": "technology",
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
                "type": "technology",
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
                "type": "skill",
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
                "type": "skill",
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
                "type": "skill",
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
            await store.store_concept_relationship(
                source,
                target,
                rel_type
            )
            
        logger.info("Successfully initialized knowledge graph")
        
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
                "metadata": {
                    "priority": "high",
                    "estimated_hours": 4
                }
            },
            {
                "id": "TEST-002",
                "label": "Test Personal Task",
                "type": "task",
                "status": "in_progress",
                "domain": "personal",
                "description": "A test task for organization",
                "metadata": {
                    "priority": "medium",
                    "category": "organization"
                }
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
    store = ConceptStore()
    try:
        async with store.driver.session() as session:
            # Check task states
            result = await session.run(
                "MATCH (s:TaskState) RETURN count(s) as count"
            )
            record = await result.single()
            if record["count"] != 4:
                logger.error("Task states not properly initialized")
                return False
                
            # Check task templates
            result = await session.run(
                "MATCH (t:Concept) WHERE t.type = 'task_template' RETURN count(t) as count"
            )
            record = await result.single()
            if record["count"] < 2:
                logger.error("Task templates not properly initialized")
                return False
                
            # Check constraints
            result = await session.run(
                "SHOW CONSTRAINTS"
            )
            constraints = [record async for record in result]
            required_constraints = ["task_id", "task_state"]
            for constraint in required_constraints:
                if not any(c["name"] == constraint for c in constraints):
                    logger.error(f"Missing required constraint: {constraint}")
                    return False

            # Check domain boundaries
            result = await session.run(
                """
                MATCH (d:Domain)
                WHERE d.name IN ['tasks', 'professional', 'personal']
                RETURN count(d) as count
                """
            )
            record = await result.single()
            if record["count"] != 3:
                logger.error("Domain boundaries not properly initialized")
                return False

            # Check access rules
            result = await session.run(
                """
                MATCH (d:Domain)-[:HAS_RULE]->(r:AccessRule)
                WHERE r.type = 'domain_access'
                RETURN count(r) as count
                """
            )
            record = await result.single()
            if record["count"] != 3:
                logger.error("Access rules not properly initialized")
                return False

            # Create and verify test data
            if not await create_test_data(store):
                logger.error("Failed to create test data")
                return False

            # Verify test data
            result = await session.run(
                """
                MATCH (t:Task)
                WHERE t.id IN ['TEST-001', 'TEST-002']
                RETURN count(t) as count
                """
            )
            record = await result.single()
            if record["count"] != 2:
                logger.error("Test data not properly created")
                return False

            logger.info("All required structures and test data verified successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying initialization: {str(e)}")
        return False
    finally:
        await store.close()

if __name__ == "__main__":
    asyncio.run(initialize_knowledge())
    # Verify initialization
    if not asyncio.run(verify_initialization()):
        sys.exit(1)
