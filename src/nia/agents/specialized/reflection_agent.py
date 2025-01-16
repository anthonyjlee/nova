"""TinyTroupe reflection agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.reflection import ReflectionAgent as NovaReflectionAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ReflectionAgent(NovaReflectionAgent, TinyTroupeAgent):
    """Reflection agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize reflection agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaReflectionAgent first
        NovaReflectionAgent.__init__(
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
            attributes=attributes,
            agent_type="reflection"
        )
        
        # Initialize reflection-specific attributes
        self._initialize_reflection_attributes()
        
    def _initialize_reflection_attributes(self):
        """Initialize reflection-specific attributes."""
        attributes = {
            "occupation": "Reflection Analyst",
            "desires": [
                "Understand patterns",
                "Track learning progress",
                "Ensure insight quality",
                "Maintain domain boundaries"
            ],
            "emotions": {
                "baseline": "contemplative",
                "towards_analysis": "introspective",
                "towards_domain": "mindful"
            },
            "capabilities": [
                "reflection_analysis",
                "pattern_recognition",
                "domain_validation",
                "learning_assessment"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on reflection analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "insight":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on learning needs
                if concept.get("type") == "learning_need":
                    self.desires.append(f"Explore {concept['name']}")
                    
                # Update emotions based on domain relevance
                if "domain_relevance" in concept:
                    relevance = float(concept["domain_relevance"])
                    if relevance > 0.8:
                        self.emotions.update({
                            "domain_state": "highly_relevant"
                        })
                    elif relevance < 0.3:
                        self.emotions.update({
                            "domain_state": "low_relevance"
                        })
                    
        return response
        
    async def analyze_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Analyze reflection and store results with domain awareness."""
        try:
            # Get debug flags
            debug_flags = metadata.get("debug_flags", {}) if metadata else {}
            
            # Validate domain access if specified
            if target_domain:
                await self.validate_domain_access(target_domain)
                
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content="Starting reflection analysis with validation tracking",
                    importance=0.8,
                    context={"type": "validation_log"}
                )
                
            # Analyze reflection with validation context
            result = await self.analyze_reflection(
                content,
                metadata={
                    "domain": target_domain or self.domain,
                    "validation_context": metadata.get("validation_result"),
                    "debug_flags": debug_flags
                }
            )
            
            # Track validation patterns
            if result.patterns and metadata and "validation_result" in metadata:
                validation_patterns = self._extract_validation_patterns(
                    result.patterns,
                    metadata["validation_result"]
                )
                
                if debug_flags.get("log_validation"):
                    await self.store_memory(
                        content=f"Validation patterns identified: {validation_patterns}",
                        importance=0.8,
                        context={"type": "validation_log"}
                    )
                    
                result.patterns["validation"] = validation_patterns
        
            # Store reflection analysis with validation context
            await self.store_memory(
                content={
                    "type": "reflection_analysis",
                    "content": content,
                    "analysis": {
                        "insights": result.insights,
                        "confidence": result.confidence,
                        "patterns": result.patterns,
                        "validation_patterns": validation_patterns if "validation_patterns" in locals() else [],
                        "timestamp": datetime.now().isoformat()
                    }
                },
                importance=0.8,
                context={
                    "type": "reflection",
                    "domain": target_domain or self.domain,
                    "validation_context": metadata.get("validation_result") if metadata else None
                }
            )
        
            # Record reflections with validation awareness
            if result.confidence > 0.8:
                await self.record_reflection(
                    f"High confidence reflection analysis with validation in {self.domain} domain",
                    domain=self.domain
                )
            elif result.confidence < 0.3:
                await self.record_reflection(
                    f"Low confidence reflection analysis - validation review needed in {self.domain} domain",
                    domain=self.domain
                )
                
            # Record validation-specific reflections
            if "validation_patterns" in locals():
                recurring_patterns = [p for p in validation_patterns if p.get("frequency", 0) > 2]
                if recurring_patterns:
                    await self.record_reflection(
                        f"Recurring validation patterns identified in {self.domain} domain: {recurring_patterns}",
                        domain=self.domain
                    )
                    
                critical_patterns = [p for p in validation_patterns if p.get("severity") == "high"]
                if critical_patterns:
                    await self.record_reflection(
                        f"Critical validation patterns require attention in {self.domain} domain: {critical_patterns}",
                        domain=self.domain
                    )
        
            return result
            
        except Exception as e:
            error_msg = f"Error in reflection analysis: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags.get("log_validation"):
                await self.store_memory(
                    content=error_msg,
                    importance=0.9,
                    context={"type": "validation_error"}
                )
                
            raise
            
    def _extract_validation_patterns(
        self,
        reflection_patterns: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract validation patterns from reflection and validation results.
        
        Args:
            reflection_patterns: Patterns from reflection analysis
            validation_result: Results from schema validation
            
        Returns:
            List of validation patterns with metadata
        """
        patterns = []
        
        # Track schema validation patterns
        if validation_result.get("issues"):
            for issue in validation_result["issues"]:
                pattern = {
                    "type": "schema_validation",
                    "description": issue.get("description"),
                    "severity": issue.get("severity", "low"),
                    "frequency": 1  # Initial occurrence
                }
                
                # Check if similar pattern exists
                existing = next(
                    (p for p in patterns if 
                     p["type"] == pattern["type"] and
                     p["description"] == pattern["description"]),
                    None
                )
                
                if existing:
                    existing["frequency"] += 1
                else:
                    patterns.append(pattern)
                    
        # Track reflection patterns related to validation
        for theme in reflection_patterns.get("recurring_themes", []):
            if any(kw in theme.lower() for kw in ["valid", "schema", "type", "format"]):
                pattern = {
                    "type": "reflection_validation",
                    "description": theme,
                    "severity": "medium",
                    "frequency": reflection_patterns.get("theme_frequencies", {}).get(theme, 1)
                }
                patterns.append(pattern)
                
        return patterns
        
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
                f"ReflectionAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
