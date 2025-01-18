#!/usr/bin/env python3
"""Initialize task system including states and workflows."""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from src.nia.core.neo4j.base_store import Neo4jBaseStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskInitializer(Neo4jBaseStore):
    """Initialize task system components."""
    
    def __init__(self):
        """Initialize task system."""
        super().__init__(uri="bolt://localhost:7687", user="neo4j", password="password")
        self.logger = logging.getLogger("task_init")
        
    async def initialize(self):
        """Initialize all task components."""
        try:
            # Connect to Neo4j
            await self.connect()
            
            # 1. Initialize task states
            await self._initialize_task_states()
            
            # 2. Set up task constraints
            await self._setup_task_constraints()
            
            # 3. Initialize task workflows
            await self._initialize_workflows()
            
            # 4. Initialize task orchestration
            await self._initialize_orchestration()
            
            self.logger.info("Task system initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize task system: {str(e)}")
            raise
            
    async def _initialize_task_states(self):
        """Initialize task states."""
        try:
            self.logger.info("Initializing task states...")
            
            states = [
                {
                    "name": "pending",
                    "description": "New or unstarted tasks",
                    "metadata": {
                        "can_transition_to": ["in_progress"],
                        "requires_approval": False,
                        "auto_transition": False
                    }
                },
                {
                    "name": "in_progress",
                    "description": "Tasks currently being worked on",
                    "metadata": {
                        "can_transition_to": ["blocked", "completed"],
                        "requires_approval": False,
                        "auto_transition": False
                    }
                },
                {
                    "name": "blocked",
                    "description": "Tasks blocked by dependencies",
                    "metadata": {
                        "can_transition_to": ["in_progress"],
                        "requires_approval": True,
                        "auto_transition": False
                    }
                },
                {
                    "name": "completed",
                    "description": "Finished tasks",
                    "metadata": {
                        "can_transition_to": [],
                        "requires_approval": True,
                        "auto_transition": False
                    }
                }
            ]
            
            # Create task states
            for state in states:
                await self.run_query(
                    """
                    CREATE (s:TaskState {
                        name: $name,
                        description: $description,
                        metadata: $metadata,
                        created_at: datetime()
                    })
                    """,
                    state
                )
            
            self.logger.info("Task states initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize task states: {str(e)}")
            raise
            
    async def _setup_task_constraints(self):
        """Set up task constraints."""
        try:
            self.logger.info("Setting up task constraints...")
            
            # Create task ID constraint
            await self.run_query(
                """
                CREATE CONSTRAINT task_id IF NOT EXISTS
                FOR (t:Task) REQUIRE t.id IS UNIQUE
                """
            )
            
            # Create task state name constraint
            await self.run_query(
                """
                CREATE CONSTRAINT task_state_name IF NOT EXISTS
                FOR (s:TaskState) REQUIRE s.name IS UNIQUE
                """
            )
            
            # Create task group ID constraint
            await self.run_query(
                """
                CREATE CONSTRAINT task_group_id IF NOT EXISTS
                FOR (g:TaskGroup) REQUIRE g.id IS UNIQUE
                """
            )
            
            # Create indexes
            await self.run_query(
                """
                CREATE INDEX task_status IF NOT EXISTS
                FOR (t:Task)
                ON (t.status)
                """
            )
            
            await self.run_query(
                """
                CREATE INDEX task_priority IF NOT EXISTS
                FOR (t:Task)
                ON (t.priority)
                """
            )
            
            self.logger.info("Task constraints set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up task constraints: {str(e)}")
            raise
            
    async def _initialize_workflows(self):
        """Initialize task workflows."""
        try:
            self.logger.info("Initializing task workflows...")
            
            # Create workflow rules
            await self.run_query(
                """
                CREATE (w:WorkflowRule {
                    name: 'dependency_check',
                    description: 'Check dependencies before state transitions',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "check_dependencies": True,
                        "auto_block_on_dependency": True,
                        "auto_unblock_on_dependency_complete": True,
                        "notify_on_block": True,
                        "notify_on_unblock": True
                    }
                }
            )
            
            # Create state transition rules
            await self.run_query(
                """
                CREATE (r:TransitionRule {
                    name: 'state_transition',
                    description: 'Rules for task state transitions',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "validate_transitions": True,
                        "require_approval_for_completion": True,
                        "allow_reopen": False,
                        "track_transition_history": True
                    }
                }
            )
            
            self.logger.info("Task workflows initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize task workflows: {str(e)}")
            raise
            
    async def _initialize_orchestration(self):
        """Initialize task orchestration."""
        try:
            self.logger.info("Initializing task orchestration...")
            
            # Create orchestration rules
            await self.run_query(
                """
                CREATE (r:OrchestrationRule {
                    name: 'task_orchestration',
                    description: 'Rules for task orchestration and coordination',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "proposal": {
                            "requires_approval": True,
                            "auto_approve_threshold": 0.8,
                            "validation": {
                                "required_fields": ["title", "description"],
                                "optional_fields": ["priority", "assignee", "due_date"]
                            }
                        },
                        "approval": {
                            "roles": ["admin", "manager", "lead"],
                            "auto_approval": {
                                "enabled": True,
                                "confidence_threshold": 0.9,
                                "domain_restrictions": ["system", "security"]
                            }
                        },
                        "creation": {
                            "validation": {
                                "required_fields": ["title", "description", "type"],
                                "optional_fields": ["priority", "assignee", "tags"]
                            },
                            "defaults": {
                                "priority": "medium",
                                "status": "pending"
                            }
                        },
                        "transitions": {
                            "validation": {
                                "required_fields": ["new_state"],
                                "optional_fields": ["reason", "metadata"]
                            },
                            "allowed_transitions": {
                                "pending": ["in_progress"],
                                "in_progress": ["blocked", "completed"],
                                "blocked": ["in_progress"],
                                "completed": []
                            },
                            "requires_approval": {
                                "to_completed": True,
                                "to_blocked": True
                            }
                        }
                    }
                }
            )
            
            # Create workflow patterns
            await self.run_query(
                """
                CREATE (p:WorkflowPattern {
                    name: 'task_patterns',
                    description: 'Common task workflow patterns',
                    config: $config,
                    created_at: datetime()
                })
                """,
                {
                    "config": {
                        "standard": {
                            "steps": ["propose", "approve", "create", "execute", "complete"],
                            "roles": ["proposer", "approver", "assignee"],
                            "validations": ["proposal", "approval", "completion"]
                        },
                        "expedited": {
                            "steps": ["create", "execute", "complete"],
                            "roles": ["creator", "assignee"],
                            "validations": ["creation", "completion"],
                            "conditions": {
                                "priority": "high",
                                "auto_approve": True
                            }
                        },
                        "collaborative": {
                            "steps": ["propose", "discuss", "approve", "create", "execute", "review", "complete"],
                            "roles": ["proposer", "reviewer", "approver", "assignee"],
                            "validations": ["proposal", "discussion", "approval", "completion"],
                            "requirements": {
                                "min_reviewers": 2,
                                "consensus_threshold": 0.75
                            }
                        }
                    }
                }
            )
            
            self.logger.info("Task orchestration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize task orchestration: {str(e)}")
            raise

async def create_test_data(store: Neo4jBaseStore):
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

async def verify_initialization(store: Neo4jBaseStore):
    """Verify that all required structures are properly initialized."""
    try:
        # Check task states
        result = await store.run_query(
            "MATCH (s:TaskState) RETURN count(s) as count"
        )
        if not result or result[0]["count"] != 4:
            logger.error("Task states not properly initialized")
            return False
            
        # Check workflow patterns
        result = await store.run_query(
            "MATCH (p:WorkflowPattern) RETURN count(p) as count"
        )
        if not result or result[0]["count"] < 1:
            logger.error("Workflow patterns not properly initialized")
            return False
            
        # Check constraints
        result = await store.run_query(
            "SHOW CONSTRAINTS"
        )
        required_constraints = ["task_id", "task_state_name", "task_group_id"]
        for constraint in required_constraints:
            if not any(c["name"] == constraint for c in result):
                logger.error(f"Missing required constraint: {constraint}")
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

async def main():
    """Main entry point."""
    initializer = TaskInitializer()
    try:
        await initializer.initialize()
        # Verify initialization
        if not await verify_initialization(initializer):
            sys.exit(1)
    except Exception as e:
        logger.error(f"Task initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
