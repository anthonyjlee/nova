"""TinyTroupe self model agent implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...nova.core.self_model import SelfModelAgent as NovaSelfModelAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class SelfModelAgent(NovaSelfModelAgent, TinyTroupeAgent):
    """Self model agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize self model agent."""
        # Set domain before initialization
        self.domain = domain or "professional"
        
        # Initialize NovaSelfModelAgent first
        NovaSelfModelAgent.__init__(
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
            agent_type="self_model"
        )
        
        # Initialize self model-specific attributes
        self._initialize_self_model_attributes()
        
        # Initialize memory references
        if memory_system:
            self._configuration["memory_references"] = []
            
        # Store memory system reference
        self._memory_system = memory_system
        
    def _initialize_self_model_attributes(self):
        """Initialize self model-specific attributes."""
        attributes = {
            "occupation": "Self Model Analyst",
            "emotions": {
                "baseline": "introspective",
                "towards_analysis": "objective",
                "towards_domain": "mindful"
            },
            "desires": [
                "Understand self model",
                "Maintain self consistency",
                "Track self development",
                "Ensure model accuracy"
            ],
            "capabilities": [
                "self_analysis",
                "model_validation",
                "consistency_checking",
                "development_tracking"
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
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        try:
            # Get analysis from LLM
            if self._memory_system and self._memory_system.llm:
                analysis = await self._memory_system.llm.analyze(content)
                
                # Update emotions and desires based on analysis
                if analysis and analysis.get("self_model"):
                    for model in analysis["self_model"]:
                        if model.get("type") == "self_insight":
                            self.update_emotions({
                                "analysis_state": model.get("description", "neutral")
                            })
                            
                        if model.get("type") == "development_need":
                            current_goals = list(self.desires)
                            current_goals.append(f"Develop {model['aspect']}")
                            self.desires = current_goals
                            
                        if "model_confidence" in model:
                            confidence = float(model["model_confidence"])
                            if confidence > 0.8:
                                self.update_emotions({
                                    "model_state": "highly_confident"
                                })
                            elif confidence < 0.3:
                                self.update_emotions({
                                    "model_state": "low_confidence"
                                })
                                
                # Create response with analysis
                return AgentResponse(
                    content=str(analysis),
                    metadata={"analysis": analysis}
                )
                
            # Process through memory system if no LLM
            return await super().process(content, metadata)
            
        except Exception as e:
            logger.error(f"Error in self model processing: {str(e)}")
            return AgentResponse(
                content="Error processing self model",
                metadata={"error": str(e)}
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
