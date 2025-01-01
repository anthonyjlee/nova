"""Nova's initialization protocol implementation."""

from typing import Dict, List, Optional
from datetime import datetime
import logging
from .self_model import NovaSelfModel

logger = logging.getLogger(__name__)

class NovaInitializer:
    """Handles Nova's initialization sequence and protocol."""
    
    def __init__(self, neo4j_store, vector_store):
        self.neo4j_store = neo4j_store
        self.vector_store = vector_store
        self.self_model = NovaSelfModel(neo4j_store)
        self.initialized = False
        
    async def initialize(self, user_context: Optional[Dict] = None):
        """Run the complete initialization sequence."""
        try:
            logger.info("Starting Nova initialization sequence...")
            
            # Step 1: Initialize self-model
            await self._init_self_model()
            
            # Step 2: Initialize memory systems
            await self._init_memory_systems()
            
            # Step 3: Process user context if provided
            if user_context:
                await self._process_user_context(user_context)
            
            # Step 4: Initialize domain separation
            await self._init_domains()
            
            # Step 5: Set up auto-approval rules
            await self._init_auto_approval()
            
            # Mark initialization as complete
            self.initialized = True
            await self.self_model.update_state("ready")
            logger.info("Nova initialization sequence completed successfully")
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            await self.self_model.update_state("error", {"error": str(e)})
            raise
            
    async def _init_self_model(self):
        """Initialize Nova's self-model and metacognitive capabilities."""
        logger.info("Initializing self-model...")
        await self.self_model.initialize()
        await self.self_model.record_reflection(
            "Initialization started. Self-model and metacognitive capabilities coming online."
        )
        
    async def _init_memory_systems(self):
        """Initialize and verify memory system connections."""
        logger.info("Initializing memory systems...")
        
        # Verify Neo4j connection
        try:
            async with self.neo4j_store.session() as session:
                await session.run("RETURN 1")
            logger.info("Neo4j connection verified")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}")
            raise
            
        # Verify vector store connection
        try:
            # Simple test operation
            test_id = await self.vector_store.store_vector(
                {"test": "connection"},
                {"metadata": "test"}
            )
            logger.info("Vector store connection verified")
        except Exception as e:
            logger.error(f"Vector store connection failed: {str(e)}")
            raise
            
    async def _process_user_context(self, context: Dict):
        """Process and store user context information."""
        logger.info("Processing user context...")
        
        # Record user preferences
        if "preferences" in context:
            await self.self_model.update_state(
                "processing_preferences",
                {"preferences": context["preferences"]}
            )
            
        # Store user environment info
        if "environment" in context:
            await self.self_model.record_reflection(
                f"User environment processed: {context['environment']}",
                domain="personal"
            )
            
        # Handle domain-specific context
        if "professional_context" in context:
            await self.self_model.record_reflection(
                f"Professional context established: {context['professional_context']}",
                domain="professional"
            )
            
    async def _init_domains(self):
        """Initialize domain separation and access controls."""
        logger.info("Initializing domain separation...")
        
        # Define default domain access for specialized agents
        domain_access = {
            "DialogueAgent": ["personal", "professional"],
            "EmotionAgent": ["personal"],
            "BeliefAgent": ["personal", "professional"],
            "ResearchAgent": ["professional"],
            "ReflectionAgent": ["personal", "professional"],
            "DesireAgent": ["personal"],
            "TaskAgent": ["professional"]
        }
        
        # Set up domain access for each agent
        for agent_name, domains in domain_access.items():
            for domain in domains:
                await self.self_model.grant_domain_access(agent_name, domain)
                
        await self.self_model.record_reflection(
            "Domain separation initialized with default access controls"
        )
        
    async def _init_auto_approval(self):
        """Initialize auto-approval rules and user proxy capabilities."""
        logger.info("Initializing auto-approval system...")
        
        # Define auto-approval rules in Neo4j
        async with self.neo4j_store.session() as session:
            await session.run("""
                MATCH (n:SystemSelf {name: 'Nova'})
                MERGE (r:AutoApprovalRules {
                    name: 'default',
                    created_at: $timestamp
                })
                SET r.rules = $rules
                MERGE (n)-[:HAS_RULES]->(r)
            """,
            timestamp=datetime.now().isoformat(),
            rules=[
                {
                    "type": "task_creation",
                    "domain": "professional",
                    "auto_approve": True,
                    "conditions": ["within_working_hours", "has_domain_access"]
                },
                {
                    "type": "memory_access",
                    "domain": "personal",
                    "auto_approve": False,
                    "conditions": ["explicit_user_consent"]
                },
                {
                    "type": "agent_communication",
                    "domain": "both",
                    "auto_approve": True,
                    "conditions": ["same_domain_access"]
                }
            ]
            )
            
        await self.self_model.record_reflection(
            "Auto-approval system initialized with default rules"
        )
        
    def is_initialized(self) -> bool:
        """Check if Nova has completed initialization."""
        return self.initialized
