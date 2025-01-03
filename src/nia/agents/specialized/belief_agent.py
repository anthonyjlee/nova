"""TinyTroupe belief agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.belief import BeliefAgent as NovaBeliefAgent, BeliefResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class BeliefAgent(TinyTroupeAgent, NovaBeliefAgent):
    """Belief agent with TinyTroupe and memory capabilities."""
    
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
        
        # Prepare initial attributes
        base_attributes = {
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
        
        # Merge with provided attributes
        if attributes:
            base_attributes.update(attributes)
            
        # Initialize NovaBeliefAgent first
        NovaBeliefAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain
        )
        
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=base_attributes,
            agent_type="belief"
        )
        
        # Initialize memory references
        if memory_system:
            self._configuration["memory_references"] = []
            
        # Store memory system reference
        self._memory_system = memory_system
        
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
        
    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
        # For testing, only allow personal domain
        if domain == "personal":
            return True
            
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                return await self._memory_system.semantic.store.get_domain_access(
                    self.name,
                    domain
                )
            except Exception:
                return False
        return False
        
    async def validate_domain_access(self, domain: str):
        """Validate access to a domain before processing."""
        if not await self.get_domain_access(domain):
            raise PermissionError(
                f"BeliefAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                await self._memory_system.semantic.store.record_reflection(
                    content=content,
                    domain=domain or self.domain
                )
                # Store reference
                if "memory_references" in self._configuration:
                    self._configuration["memory_references"].append({
                        "type": "reflection",
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error recording reflection: {str(e)}")
