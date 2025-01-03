"""TinyTroupe parsing agent implementation."""

import json
import re
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
    """Parsing agent with TinyTroupe and memory capabilities,
    flexible enough to handle different LLM JSON or partial JSON outputs."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None,
        llm_type: str = "generic"
    ):
        """Initialize parsing agent.
        
        Args:
            llm_type: identifies which LLM or brand we might be dealing with
                     (e.g. "openai", "anthropic", "cohere", etc.)
        """
        # Set domain before initialization
        self.domain = domain or "professional"
        
        # Initialize NovaParser first
        NovaParser.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain
        )
        
        # Prepare initial attributes
        base_attributes = {
            "type": "parsing",
            "occupation": "Content Parser",
            "domain": self.domain,
            "desires": [
                "Extract structured information",
                "Identify key concepts",
                "Validate content structure"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_content": "focused",
                "content_complexity": "moderate"
            },
            "capabilities": [
                "text_parsing",
                "concept_extraction",
                "key_point_identification",
                "schema_validation"
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
            agent_type="parsing"
        )
        
        # Store memory system reference
        self._memory_system = memory_system
        
        # Additional param for multi-LLM parse logic
        self.llm_type = llm_type
        
    def get_attributes(self) -> Dict[str, Any]:
        """Get agent attributes."""
        attrs = {
            "type": self.agent_type,
            "occupation": self._configuration.get("occupation"),
            "domain": self.domain,
            "desires": self._configuration.get("current_goals", []),
            "emotions": self._configuration.get("current_emotions", {}),
            "capabilities": self._configuration.get("capabilities", [])
        }
        return attrs
        
    @property
    def emotions(self) -> Dict[str, str]:
        """Get agent emotions."""
        return self._configuration.get("current_emotions", {})
        
    @emotions.setter
    def emotions(self, value: Dict[str, str]):
        """Set agent emotions."""
        if not isinstance(value, dict):
            value = {}
        self._configuration["current_emotions"] = value
        
    def update_emotions(self, updates: Dict[str, str]):
        """Update emotions dictionary."""
        current = dict(self.emotions)
        current.update(updates)
        self.emotions = current
        
    @property
    def desires(self) -> List[str]:
        """Get agent desires."""
        return self._configuration.get("current_goals", [])
        
    @desires.setter
    def desires(self, value: List[str]):
        """Set agent desires."""
        if not isinstance(value, list):
            value = []
        self._configuration["current_goals"] = value
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems."""
        metadata = metadata or {}
        metadata["domain"] = self.domain
        metadata["llm_type"] = self.llm_type
        
        try:
            # Get analysis from LLM
            if self._memory_system and self._memory_system.llm:
                raw_analysis = await self._memory_system.llm.analyze(content)
                
                # Parse the raw analysis using multi-LLM strategies
                analysis = self._multi_llm_parse(raw_analysis, self.llm_type)
                
                # Update emotions and desires based on analysis
                if analysis and analysis.get("concepts"):
                    for concept in analysis["concepts"]:
                        if concept.get("type") == "complexity":
                            self.update_emotions({
                                "content_complexity": concept.get("description", "moderate")
                            })
                            
                        if concept.get("type") == "validation_need":
                            current_goals = list(self.desires)
                            current_goals.append(f"Validate {concept['statement']}")
                            self.desires = current_goals
                            
                # Create response with analysis
                return AgentResponse(
                    content=str(analysis),
                    metadata={"analysis": analysis}
                )
                
            # Process through memory system if no LLM
            return await super().process(content, metadata)
            
        except Exception as e:
            logger.error(f"Error in parsing: {str(e)}")
            return AgentResponse(
                content="Error processing content",
                metadata={
                    "error": str(e),
                    "concepts": [{
                        "statement": "Error occurred during parsing",
                        "type": "error",
                        "confidence": 0.0
                    }]
                }
            )
            
    async def parse_and_store(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> ParseResult:
        """Parse text with multi-LLM support."""
        try:
            # Get analysis from LLM
            if self._memory_system and self._memory_system.llm:
                raw_analysis = await self._memory_system.llm.analyze({"text": text})
                
                # Parse using multi-LLM strategies
                analysis = self._multi_llm_parse(raw_analysis, self.llm_type)
                
                # Create ParseResult
                result = ParseResult(
                    concepts=analysis.get("concepts", []),
                    key_points=analysis.get("key_points", []),
                    confidence=analysis.get("confidence", 0.5),
                    metadata={
                        "domain": self.domain,
                        "content_type": "text",
                        "source": context.get("source", "unknown") if context else "unknown",
                        "llm_type": self.llm_type
                    },
                    structure=analysis.get("structure", {})
                )
                
                # Store parse result if memory system available
                context = context or {}
                context.update({
                    "type": "parsing_result",
                    "domain": self.domain,
                    "agent": self.name
                })
                
                if self._memory_system and hasattr(self._memory_system, "episodic"):
                    await self._memory_system.episodic.store.store_memory({
                        "text": text,
                        "analysis": {
                            "concepts": result.concepts,
                            "key_points": result.key_points,
                            "confidence": result.confidence,
                            "timestamp": datetime.now().isoformat()
                        },
                        "importance": 0.6,
                        "context": context
                    })
                
                # Record reflection based on confidence
                if result.confidence > 0.8:
                    await self.record_reflection(
                        f"High confidence parsing result for text in {self.domain} domain",
                        domain=self.domain
                    )
                elif result.confidence < 0.3:
                    await self.record_reflection(
                        f"Low confidence parsing result - additional validation needed in {self.domain} domain",
                        domain=self.domain
                    )
                    
                return result
                
            # Fallback to basic parsing if no LLM
            return ParseResult(
                concepts=[{
                    "statement": "No LLM available for parsing",
                    "type": "error",
                    "confidence": 0.0
                }],
                key_points=[{
                    "statement": "No LLM available for parsing",
                    "type": "error",
                    "confidence": 0.0
                }],
                confidence=0.0,
                metadata={"error": "No LLM available"},
                structure={}
            )
            
        except Exception as e:
            logger.error(f"Error in parsing: {str(e)}")
            return ParseResult(
                concepts=[{
                    "statement": f"Error occurred during parsing: {str(e)}",
                    "type": "error",
                    "confidence": 0.0
                }],
                key_points=[{
                    "statement": f"Error occurred during parsing: {str(e)}",
                    "type": "error",
                    "confidence": 0.0
                }],
                confidence=0.0,
                metadata={"error": str(e)},
                structure={"error": str(e)}
            )
            
    def _multi_llm_parse(self, raw_analysis: Dict[str, Any], llm_type: str) -> Dict[str, Any]:
        """Parse raw LLM output using different strategies based on LLM type."""
        # For raw analysis from LLM, just return it
        if isinstance(raw_analysis, dict):
            return self._map_parsed_to_result(raw_analysis)
            
        # For text output, try parsing as JSON
        if isinstance(raw_analysis, str):
            # Strategy 1: Strict JSON
            if llm_type in ["openai", "cohere"]:
                parsed = self._try_strict_json(raw_analysis)
                if parsed:
                    return self._map_parsed_to_result(parsed)
                    
            # Strategy 2: Loose JSON
            if llm_type in ["anthropic", "generic"]:
                parsed = self._try_loose_json(raw_analysis)
                if parsed:
                    return self._map_parsed_to_result(parsed)
                    
        # Fallback: Minimal parse
        return self._fallback_parse(str(raw_analysis))
        
    def _try_strict_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt strict JSON parse from start to finish."""
        text = text.strip()
        try:
            data = json.loads(text)
            return data
        except json.JSONDecodeError:
            logger.warning("Strict JSON parse failed")
            return None
            
    def _try_loose_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Find and parse JSON block from text that might contain other content."""
        # Find first { and last } with balanced brackets
        text = text.strip()
        if not text:
            return None
            
        start = text.find('{')
        if start == -1:
            return None
            
        # Track bracket balance
        balance = 0
        end = -1
        
        for i in range(start, len(text)):
            if text[i] == '{':
                balance += 1
            elif text[i] == '}':
                balance -= 1
                if balance == 0:
                    end = i + 1
                    break
                    
        if end == -1:
            return None
            
        try:
            json_block = text[start:end]
            data = json.loads(json_block)
            return data
        except json.JSONDecodeError:
            logger.warning("Loose JSON parse found block but failed to decode")
            return None
        
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Create minimal structured output when JSON parsing fails."""
        return {
            "raw_text": text,
            "concepts": [{
                "statement": "Failed to parse structured content",
                "type": "error",
                "confidence": 0.2
            }],
            "key_points": [{
                "statement": "Failed to parse structured content",
                "type": "error",
                "confidence": 0.2
            }],
            "confidence": 0.2
        }
        
    def _map_parsed_to_result(self, parsed_data: Dict[str, Any], fallback: bool = False) -> Dict[str, Any]:
        """Map parsed dictionary to standard format, handling field variations."""
        # Handle different field names that LLMs might use
        concepts = parsed_data.get("concepts") or parsed_data.get("ideas") or []
        key_points = parsed_data.get("key_points") or parsed_data.get("main_points") or []
        confidence = parsed_data.get("confidence", 0.5)
        structure = parsed_data.get("structure") or {}
        
        # If fallback parse, reduce confidence
        if fallback:
            confidence = min(confidence, 0.3)
            
        return {
            "concepts": concepts,
            "key_points": key_points,
            "confidence": confidence,
            "structure": structure
        }
        
    @property
    def memory_system(self):
        """Get memory system."""
        return self._memory_system
        
    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
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
                f"ParsingAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self._memory_system and hasattr(self._memory_system, "semantic"):
            try:
                await self._memory_system.semantic.store.record_reflection(
                    content,
                    domain=domain or self.domain
                )
            except Exception as e:
                logger.error(f"Error recording reflection: {str(e)}")
