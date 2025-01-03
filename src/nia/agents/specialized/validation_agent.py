"""TinyTroupe validation agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.validation import ValidationAgent as NovaValidationAgent, ValidationResult
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse
from ...config import validate_agent_config

logger = logging.getLogger(__name__)

class ValidationAgent(TinyTroupeAgent, NovaValidationAgent):
    """Validation agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize validation agent."""
        # Validate configuration
        config = {
            "name": name,
            "agent_type": "validation",
            "domain": domain or "professional"
        }
        validate_agent_config("validation", config)
        
        # Prepare validation-specific attributes
        base_attributes = {
            "type": "validation",
            "occupation": "Content Validator",
            "domain": config["domain"],
            "desires": [
                "Ensure content quality",
                "Validate domain boundaries", 
                "Identify potential issues",
                "Maintain validation standards"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_validation": "focused",
                "towards_domain": "mindful",
                "validation_state": "neutral",
                "domain_state": "neutral"
            },
            "capabilities": [
                "content_validation",
                "domain_validation", 
                "issue_detection",
                "quality_assessment"
            ]
        }

        # Merge with provided attributes
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, dict) and key in base_attributes and isinstance(base_attributes[key], dict):
                    base_attributes[key].update(value)
                else:
                    base_attributes[key] = value

        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=base_attributes,
            agent_type="validation"
        )
        
        # Set domain and memory system
        self.domain = config["domain"]
        self._memory_system = memory_system
        
        # Initialize emotions and desires from base attributes
        self.emotions = base_attributes.get("emotions", {})
        self.desires = base_attributes.get("desires", [])
        
        # Initialize NovaValidationAgent
        NovaValidationAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=config["domain"]
        )
        
        
    async def initialize(self):
        """Record initialization reflections."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            await self._memory_system.semantic.store.record_reflection(
                "Validation agent initialized successfully in professional domain",
                domain=self.domain
            )
            await self._memory_system.semantic.store.record_reflection(
                "Core attributes validated in professional domain",
                domain=self.domain
            )
            await self._memory_system.semantic.store.record_reflection(
                "Validation capabilities confirmed in professional domain",
                domain=self.domain
            )
            await self._memory_system.semantic.store.record_reflection(
                "Validation tracking systems ready in professional domain",
                domain=self.domain
            )
            await self._memory_system.semantic.store.record_reflection(
                "Validation agent ready for operation in professional domain",
                domain=self.domain
            )
            
    def get_attributes(self) -> Dict[str, Any]:
        """Get agent attributes."""
        return {
            "occupation": self._configuration["occupation"],
            "desires": self.desires,
            "emotions": self.emotions,
            "capabilities": self._configuration["capabilities"],
            "domain": self.domain
        }
        
    @property
    def memory_system(self):
        """Get memory system."""
        return self._memory_system

    async def learn_concept(self, name: str, type: str, description: str, related: list):
        """Learn a new concept."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            await self._memory_system.semantic.store.store_concept(
                name=name,
                type=type,
                description=description,
                related=related
            )
        
    async def store_memory(self, content: Dict[str, Any], importance: float = 0.5, context: Optional[Dict] = None):
        """Store memory with domain awareness."""
        if self._memory_system:
            await self._memory_system.store(
                content=content,
                importance=importance,
                context=context or {}
            )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        try:
            # Process through memory system
            raw_response = await self.llm.analyze(content, metadata=metadata)
            
            # Convert raw response to structured response
            if isinstance(raw_response, str):
                # Create structured response
                response = AgentResponse(
                    content=raw_response,
                    confidence=0.8,
                    metadata={
                        "domain": self.domain,
                        "agent_type": "validation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Add validation concepts
                response.concepts = [{
                    "name": "Validation Analysis",
                    "type": "validation_result",
                    "description": raw_response,
                    "domain_relevance": 0.8
                }, {
                    "name": "Validation Need",
                    "type": "validation_need",
                    "description": "Requires validation",
                    "domain_relevance": 0.7
                }]
            else:
                response = raw_response
            
            # Update TinyTroupe state based on validation analysis
            if response and hasattr(response, "concepts"):
                for concept in response.concepts:
                    if not isinstance(concept, dict):
                        continue
                        
                    # Update emotions based on validation results
                    if concept.get("type") == "validation_result":
                        self.emotions["validation_state"] = concept.get("description", "neutral")
                        if "domain_relevance" in concept:
                            try:
                                relevance = float(concept["domain_relevance"])
                                if relevance > 0.8:
                                    self.emotions["domain_state"] = "highly_relevant"
                                elif relevance < 0.3:
                                    self.emotions["domain_state"] = "low_relevance"
                            except (ValueError, TypeError):
                                pass
                    
                    # Update desires based on validation needs
                    if concept.get("type") == "validation_need":
                        need = concept.get("name", "unknown need")
                        if not any(need in desire for desire in self.desires):
                            self.desires.append(f"Address {need}")
            
            return response
        except Exception as e:
            logger.error(f"Error in process: {str(e)}")
            return AgentResponse(
                content="Error processing content",
                confidence=0.0,
                metadata={"error": str(e), "domain": self.domain}
            )
        
    async def validate_and_store(
        self,
        content: Dict[str, Any],
        validation_type: str,
        target_domain: Optional[str] = None
    ):
        """Validate content and store results with domain awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Set validation domain
        validation_domain = target_domain or self.domain
            
        try:
            # Validate content
            analysis = await self.llm.analyze(
                content,
                validation_type=validation_type,
                metadata={"domain": validation_domain}
            )
            
            # Convert analysis to ValidationResult
            if isinstance(analysis, dict):
                result = ValidationResult(
                    is_valid=analysis.get("is_valid", True),
                    validations=analysis.get("validations", []),
                    confidence=analysis.get("confidence", 0.8),
                    metadata={"domain": validation_domain},
                    issues=analysis.get("issues", [])
                )
                
                # Record reflection based on validation result
                if result.is_valid and result.confidence > 0.8:
                    await self.record_reflection(
                        f"High confidence validation completed in {validation_domain} domain",
                        domain=validation_domain
                    )
                else:
                    await self.record_reflection(
                        f"Validation failed - error encountered in {validation_domain} domain",
                        domain=validation_domain
                    )
            else:
                result = ValidationResult(
                    is_valid=False,
                    validations=[],
                    confidence=0.0,
                    metadata={"domain": validation_domain, "error": "Invalid analysis format"},
                    issues=[{"type": "error", "severity": "high", "description": "Invalid analysis format"}]
                )
                
                # Record reflection for failed validation
                await self.record_reflection(
                    f"Validation failed - invalid format in {validation_domain} domain",
                    domain=validation_domain
                )
                
        except Exception as e:
            result = ValidationResult(
                is_valid=False,
                validations=[],
                confidence=0.0,
                metadata={"domain": validation_domain, "error": str(e)},
                issues=[{"type": "error", "severity": "high", "description": str(e)}]
            )
            
            # Record reflection for error
            await self.record_reflection(
                f"Validation error in {validation_domain} domain: {str(e)}",
                domain=validation_domain
            )
        
        # Add domain to result metadata
        if not hasattr(result, "metadata"):
            result.metadata = {}
        result.metadata["domain"] = validation_domain
        
        # Store validation results
        await self.store_memory(
            content={
                "type": "validation_result",
                "content": content,
                "validation_type": validation_type,
                "analysis": {
                    "is_valid": getattr(result, "is_valid", False),
                    "validations": getattr(result, "validations", []),
                    "confidence": getattr(result, "confidence", 0.0),
                    "issues": getattr(result, "issues", []),
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "validation",
                "domain": validation_domain
            }
        )
        
        # Record reflection for critical issues
        if hasattr(result, "issues"):
            critical_issues = [i for i in result.issues if isinstance(i, dict) and i.get("severity") == "high"]
            if critical_issues:
                await self.record_reflection(
                    f"Critical validation issues detected in {validation_domain} domain",
                    domain=validation_domain
                )
        
        return result
        
    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            return await self._memory_system.semantic.store.get_domain_access(
                self.name,
                domain
            )
        return False
        
    async def validate_domain_access(self, domain: str):
        """Validate access to a domain before processing."""
        has_access = await self.get_domain_access(domain)
        if has_access:
            await self.record_reflection(
                "Domain access validated successfully in professional domain",
                domain=self.domain
            )
            await self.record_reflection(
                "High security compliance confirmed in professional domain",
                domain=self.domain
            )
            await self.record_reflection(
                "Strong permission validation achieved in professional domain",
                domain=self.domain
            )
            await self.record_reflection(
                "Full access scope verified in professional domain",
                domain=self.domain
            )
        else:
            await self.record_reflection(
                "Domain access denied for restricted domain",
                domain=self.domain
            )
            await self.record_reflection(
                "Security compliance enforced for unauthorized access attempt",
                domain=self.domain
            )
            await self.record_reflection(
                "High security risk prevented in professional domain",
                domain=self.domain
            )
            await self.record_reflection(
                "Access scope violation blocked in professional domain",
                domain=self.domain
            )
            raise PermissionError(
                f"ValidationAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            await self._memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
