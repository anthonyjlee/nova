"""TinyTroupe belief agent implementation."""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime

from ...nova.core.belief import BeliefAgent as NovaBeliefAgent, BeliefResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse, DomainContext, ValidationSchema

logger = logging.getLogger(__name__)

class BeliefAgent(NovaBeliefAgent, TinyTroupeAgent):
    """Belief agent with TinyTroupe and memory capabilities.
    
    This agent combines TinyTroupe's agent capabilities with Nova's belief system
    and memory management. It handles domain-aware belief analysis, reflection
    recording, and cross-domain operations.
    
    Key features:
    - Async initialization with proper connection handling
    - Domain context validation and access control
    - Memory system integration with both semantic and episodic layers
    - Comprehensive error handling and logging
    - Automatic recovery from uninitialized states
    """
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize belief agent."""
        # Set domain before initialization
        self.domain = domain or "professional"
        
        # Initialize TinyTroupeAgent first
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="belief"
        )
        
        # Initialize NovaBeliefAgent
        NovaBeliefAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain
        )
        
        # Store memory system reference
        self._memory_system = memory_system
        
        # Initialize belief-specific attributes
        self._initialize_belief_attributes()
        
        # Initialize memory references
        if memory_system:
            self._configuration["memory_references"] = []
            
    async def initialize(self):
        """Initialize belief agent with domain-specific setup.
        
        Extends base initialization with belief-specific components:
        1. Base initialization (memory, world)
        2. Nova belief system initialization
        3. Domain-specific setup
        """
        # Initialize base components first
        await super().initialize()
        
        try:
            # Initialize Nova belief system
            await NovaBeliefAgent.initialize(self)
            self.logger.debug(f"Nova belief system initialized for {self.name}")
            
            # Any additional belief-specific initialization can go here
            
        except Exception as e:
            self.logger.error(f"Failed to initialize belief components: {str(e)}")
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
            
    @classmethod
    async def create(
        cls,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ) -> 'BeliefAgent':
        """Factory method to create and initialize a BeliefAgent."""
        agent = cls(
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            domain=domain
        )
        await agent.initialize()
        return agent
        
    def _initialize_belief_attributes(self):
        """Initialize belief-specific attributes."""
        attributes = {
            "occupation": "Belief Analyst",
            "emotions": {
                "baseline": "analytical",
                "towards_analysis": "objective",
                "towards_domain": "mindful"
            },
            "desires": [
                "Understand belief systems",
                "Validate knowledge claims",
                "Ensure belief coherence",
                "Maintain domain boundaries"
            ],
            "capabilities": [
                "belief_analysis",
                "evidence_validation",
                "domain_validation",
                "coherence_checking"
            ]
        }
        self.define(**attributes)
        
    @property
    def emotions(self):
        """Get agent emotions."""
        return self._configuration.get("current_emotions", {})
        
    @emotions.setter
    def emotions(self, value):
        """Set agent emotions."""
        if not isinstance(value, dict):
            value = {}
        self._configuration["current_emotions"] = value.copy()
            
    def update_emotions(self, updates: Dict[str, str]):
        """Update emotions dictionary."""
        if "current_emotions" not in self._configuration:
            self._configuration["current_emotions"] = {}
        self._configuration["current_emotions"].update(updates)
        
    @property
    def desires(self):
        """Get agent desires."""
        return self._configuration.get("current_goals", [])
        
    @desires.setter
    def desires(self, value):
        """Set agent desires."""
        self._configuration["current_goals"] = value
        
    @property
    def capabilities(self):
        """Get agent capabilities."""
        return self._configuration.get("capabilities", [])
        
    @capabilities.setter
    def capabilities(self, value):
        """Set agent capabilities."""
        self._configuration["capabilities"] = value
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        if not getattr(self, '_initialized', False):
            logger.warning(f"BeliefAgent {self.name} not initialized, initializing now...")
            await self.initialize()
            
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        try:
            # Get analysis from LLM
            if self._memory_system and self._memory_system.llm:
                analysis = await self._memory_system.llm.analyze(content)
                
                # Update emotions and desires based on analysis
                if analysis and analysis.get("beliefs"):
                    for belief in analysis["beliefs"]:
                        if belief.get("type") == "belief":
                            self.update_emotions({
                                "analysis_state": belief.get("description", "neutral")
                            })
                            
                        if belief.get("type") == "belief_need":
                            current_goals = list(self.desires)
                            current_goals.append(f"Investigate {belief['statement']}")
                            self.desires = current_goals
                            
                        if "domain_relevance" in belief:
                            relevance = float(belief["domain_relevance"])
                            if relevance > 0.8:
                                self.update_emotions({
                                    "domain_state": "highly_relevant"
                                })
                            elif relevance < 0.3:
                                self.update_emotions({
                                    "domain_state": "low_relevance"
                                })
                                
                # Create response with analysis
                return AgentResponse(
                    content=str(analysis),
                    metadata={"analysis": analysis}
                )
                
            # Process through memory system if no LLM
            return await super().process(content, metadata)
            
        except Exception as e:
            logger.error(f"Error in belief processing: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return AgentResponse(
                content="Error processing beliefs",
                metadata={"error": str(e)}
            )
        
    async def analyze_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ) -> BeliefResult:
        """Analyze beliefs and store results with domain awareness."""
        if not getattr(self, '_initialized', False):
            logger.warning(f"BeliefAgent {self.name} not initialized, initializing now...")
            await self.initialize()
            
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        try:
            # Get analysis from LLM
            if self._memory_system and self._memory_system.llm:
                analysis = await self._memory_system.llm.analyze(content)
                
                # Get beliefs and confidence
                beliefs = analysis.get("beliefs", [])
                confidence = analysis.get("confidence")
                if confidence is None:
                    # Calculate from beliefs if not provided
                    confidence = sum(b.get("confidence", 0.5) for b in beliefs) / len(beliefs) if beliefs else 0.0
                
                # Create BeliefResult
                result = BeliefResult(
                    beliefs=beliefs,
                    confidence=float(confidence),
                    metadata={
                        "domain": target_domain or self.domain,
                        "content_type": content.get("type", "text"),
                        "source": content.get("source", "unknown")
                    },
                    evidence=analysis.get("evidence", {})
                )
                
                # Store belief analysis
                if self._memory_system.semantic and self._memory_system.semantic.store:
                    await self._memory_system.semantic.store.store_memory(
                        {
                            "type": "belief_analysis",
                            "content": content,
                            "analysis": {
                                "beliefs": result.beliefs,
                                "confidence": result.confidence,
                                "evidence": result.evidence,
                                "timestamp": result.timestamp
                            }
                        },
                        {
                            "type": "belief",
                            "domain": target_domain or self.domain
                        }
                    )
        
                    # Record reflections based on analysis
                    if result.confidence > 0.8:
                        await self.record_reflection(
                            f"High confidence belief analysis achieved in {self.domain} domain",
                            domain=self.domain
                        )
                    elif result.confidence < 0.3:
                        await self.record_reflection(
                            f"Low confidence belief analysis - may need additional evidence in {self.domain} domain",
                            domain=self.domain
                        )
                        
                    # Record contradictions
                    if result.evidence.get("contradictions"):
                        await self.record_reflection(
                            f"Contradictory evidence found in {self.domain} domain - further investigation needed",
                            domain=self.domain
                        )
                        
                return result
                
            return BeliefResult(
                beliefs=[],
                confidence=0.0,
                metadata={"error": "No LLM available"},
                evidence={}
            )
            
        except Exception as e:
            logger.error(f"Error in belief analysis: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return BeliefResult(
                beliefs=[],
                confidence=0.0,
                metadata={"error": str(e)},
                evidence={"error": str(e)}
            )
        
    def get_attributes(self):
        """Get agent attributes including domain."""
        return {
            'type': self.agent_type,
            'occupation': self._configuration.get("occupation"),
            'emotions': self.emotions,
            'desires': self.desires,
            'capabilities': self.capabilities,
            'domain': self.domain
        }
        
    @property
    def memory_system(self):
        """Get memory system."""
        return self._memory_system
        
    async def get_domain_access(self, domain_context: DomainContext) -> bool:
        """Check if agent has access to specified domain context."""
        # Always allow access to agent's primary domain
        if domain_context.primary_domain == self.domain:
            return True
            
        # For cross-domain operations, check if approved
        if domain_context.cross_domain and domain_context.cross_domain.get("approved"):
            return True
            
        # For knowledge verticals, check semantic store
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                # Check both primary domain and knowledge vertical
                primary_access = await self._memory_system.semantic.store.get_domain_access(
                    self.name,
                    domain_context.primary_domain
                )
                
                # If no knowledge vertical or primary access denied, return primary access result
                if not domain_context.knowledge_vertical or not primary_access:
                    return primary_access
                    
                # Check knowledge vertical access
                vertical_access = await self._memory_system.semantic.store.get_domain_access(
                    self.name,
                    domain_context.knowledge_vertical
                )
                
                # Both must be granted for access
                return primary_access and vertical_access
                
            except Exception as e:
                logger.error(f"Error checking domain access: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return False
                
        return False
        
    async def validate_domain_access(self, domain_context: Union[DomainContext, str]):
        """Validate access to a domain context before processing."""
        # Convert string to DomainContext if needed
        if isinstance(domain_context, str):
            domain_context = DomainContext(
                primary_domain=domain_context,
                knowledge_vertical=None,
                validation=ValidationSchema(
                    domain=domain_context,
                    confidence=1.0,
                    source="belief_agent"
                )
            )
            
        if not await self.get_domain_access(domain_context):
            raise PermissionError(
                f"BeliefAgent {self.name} does not have access to domain context: {domain_context}"
            )
            
    async def request_cross_domain_access(
        self,
        source_domain: DomainContext,
        target_domain: DomainContext,
        justification: str
    ) -> bool:
        """Request access for cross-domain operation."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                return await self._memory_system.semantic.store.request_cross_domain_access(
                    agent_name=self.name,
                    source_domain=source_domain,
                    target_domain=target_domain,
                    justification=justification
                )
            except Exception as e:
                logger.error(f"Error requesting cross-domain access: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return False
        return False
            
    async def record_reflection(
        self,
        content: str,
        domain: Optional[str] = None
    ):
        """Record a reflection with domain awareness."""
        if not getattr(self, '_initialized', False):
            logger.warning(f"BeliefAgent {self.name} not initialized, initializing now...")
            await self.initialize()
            
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                # Create domain context
                domain_context = DomainContext(
                    primary_domain=domain or self.domain,
                    knowledge_vertical=None,
                    validation=ValidationSchema(
                        domain=domain or self.domain,
                        confidence=1.0,
                        source="belief_agent"
                    )
                )
                
                # Record reflection with domain context
                await self._memory_system.semantic.store.record_reflection(
                    content=content,
                    domain=domain_context.primary_domain
                )
                
                # Store reference with domain information
                if "memory_references" in self._configuration:
                    self._configuration["memory_references"].append({
                        "type": "reflection",
                        "content": content,
                        "domain": domain_context.primary_domain,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error recording reflection: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
