"""TinyTroupe parsing agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.parsing import NovaParser, ParseResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ParsingAgent(TinyTroupeAgent, NovaParser):
    """Parsing agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize parsing agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="parsing"
        )
        
        # Initialize NovaParser
        NovaParser.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize parsing-specific attributes
        self._initialize_parsing_attributes()
        
    def _initialize_parsing_attributes(self):
        """Initialize parsing-specific attributes."""
        self.define(
            occupation="Content Parser",
            desires=[
                "Extract structured information",
                "Identify key concepts",
                "Validate content structure"
            ],
            emotions={
                "baseline": "analytical",
                "towards_content": "focused"
            },
            domain=self.domain,
            capabilities=[
                "text_parsing",
                "concept_extraction",
                "key_point_identification",
                "schema_validation"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on parsing analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on content complexity
                if concept.get("type") == "complexity":
                    self.emotions.update({
                        "content_complexity": concept.get("description", "moderate")
                    })
                    
                # Update desires based on parsing needs
                if concept.get("type") == "validation_need":
                    self.desires.append(f"Validate {concept['name']}")
                    
        return response
        
    async def parse_and_store(self, text: str, context: Optional[Dict] = None) -> ParseResult:
        """Parse text and store results with domain awareness."""
        # Parse text using NovaParser
        result = await self.parse_text(text)
        
        # Prepare context with domain
        context = context or {}
        context.update({
            "type": "parsing_result",
            "domain": self.domain,
            "agent": self.name
        })
        
        # Store parsing memory
        await self.store_memory(
            content={
                "text": text,
                "analysis": {
                    "concepts": result.concepts,
                    "key_points": result.key_points,
                    "confidence": result.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.6,
            context=context
        )
        
        # Record reflection if confidence is notable
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence parsing result achieved for text in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence parsing result - may need additional validation in {self.domain} domain",
                domain=self.domain
            )
        
        return result
        
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
            
    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            return await self.memory_system.semantic.store.get_domain_access(
                self.name,
                domain
            )
        return False
        
    async def validate_domain_access(self, domain: str):
        """Validate access to a domain before processing."""
        if not await self.get_domain_access(domain):
            raise PermissionError(
                f"ParsingAgent {self.name} does not have access to domain: {domain}"
            )
