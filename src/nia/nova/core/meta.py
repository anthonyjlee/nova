"""Nova's core meta-orchestration functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MetaResult:
    """Container for meta-orchestration results."""
    
    def __init__(
        self,
        response: str,
        concepts: List[Dict],
        key_points: List[str],
        confidence: float,
        metadata: Optional[Dict] = None
    ):
        self.response = response
        self.concepts = concepts
        self.key_points = key_points
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

class MetaAgent:
    """Core meta-orchestration functionality for Nova's ecosystem."""
    
    def __init__(
        self,
        llm=None,
        store=None,
        vector_store=None,
        agents: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.agents = agents or {}
        self.domain = domain or "professional"  # Default to professional domain
        
    async def process_interaction(
        self,
        content: Any,
        metadata: Optional[Dict] = None
    ) -> MetaResult:
        """Process an interaction through meta-orchestration."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get agent responses
            agent_responses = await self._gather_agent_responses(content, metadata)
            
            # Synthesize responses
            if self.llm:
                synthesis = await self.llm.analyze(
                    {
                        "content": content,
                        "responses": agent_responses,
                        "metadata": metadata
                    },
                    template="meta_synthesis",
                    max_tokens=1500
                )
            else:
                synthesis = self._basic_synthesis(content, agent_responses)
                
            # Extract concepts and key points
            concepts = self._extract_concepts(synthesis)
            key_points = self._extract_key_points(synthesis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(concepts, agent_responses)
            
            return MetaResult(
                response=synthesis.get("response", ""),
                concepts=concepts,
                key_points=key_points,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "agent_count": len(agent_responses),
                    "source_length": len(str(content))
                }
            )
            
        except Exception as e:
            logger.error(f"Meta-orchestration error: {str(e)}")
            return MetaResult(
                response="Error during meta-orchestration",
                concepts=[],
                key_points=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
            
    async def _gather_agent_responses(
        self,
        content: Any,
        metadata: Dict
    ) -> Dict[str, Any]:
        """Gather responses from all relevant agents."""
        responses = {}
        
        for agent_name, agent in self.agents.items():
            try:
                # Check domain access if agent supports it
                if hasattr(agent, "get_domain_access"):
                    if not await agent.get_domain_access(metadata["domain"]):
                        logger.debug(f"Agent {agent_name} does not have access to domain {metadata['domain']}")
                        continue
                        
                # Get agent response
                response = await agent.process(content, metadata)
                if response:
                    responses[agent_name] = response
                    
            except Exception as e:
                logger.error(f"Error getting response from {agent_name}: {str(e)}")
                
        return responses
        
    def _basic_synthesis(
        self,
        content: Any,
        agent_responses: Dict[str, Any]
    ) -> Dict:
        """Basic synthesis without LLM."""
        # Collect all concepts and key points
        all_concepts = []
        all_key_points = []
        
        for agent_name, response in agent_responses.items():
            if hasattr(response, "concepts"):
                all_concepts.extend(response.concepts)
            if hasattr(response, "key_points"):
                all_key_points.extend(response.key_points)
                
        # Basic deduplication
        unique_concepts = {
            (c.get("name", ""), c.get("type", "")): c
            for c in all_concepts
        }.values()
        
        unique_points = list(set(all_key_points))
        
        return {
            "response": "Synthesized response from multiple agents",
            "concepts": list(unique_concepts),
            "key_points": unique_points
        }
        
    def _extract_concepts(self, synthesis: Dict) -> List[Dict]:
        """Extract and validate concepts from synthesis."""
        concepts = synthesis.get("concepts", [])
        valid_concepts = []
        
        for concept in concepts:
            if isinstance(concept, dict) and "name" in concept:
                valid_concept = {
                    "name": str(concept["name"]),
                    "type": str(concept.get("type", "synthesis")),
                    "confidence": float(concept.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in concept:
                    valid_concept["description"] = str(concept["description"])
                if "source" in concept:
                    valid_concept["source"] = str(concept["source"])
                    
                valid_concepts.append(valid_concept)
                
        return valid_concepts
        
    def _extract_key_points(self, synthesis: Dict) -> List[str]:
        """Extract and validate key points from synthesis."""
        key_points = synthesis.get("key_points", [])
        valid_points = []
        
        for point in key_points:
            if point and isinstance(point, str):
                valid_points.append(point.strip())
                
        return valid_points
        
    def _calculate_confidence(
        self,
        concepts: List[Dict],
        agent_responses: Dict[str, Any]
    ) -> float:
        """Calculate overall synthesis confidence."""
        if not concepts and not agent_responses:
            return 0.0
            
        # Concept confidence
        concept_conf = 0.0
        if concepts:
            confidences = [c.get("confidence", 0.5) for c in concepts]
            concept_conf = sum(confidences) / len(confidences)
            
        # Agent response confidence
        agent_conf = 0.0
        agent_confidences = []
        for response in agent_responses.values():
            if hasattr(response, "confidence"):
                agent_confidences.append(float(response.confidence))
        if agent_confidences:
            agent_conf = sum(agent_confidences) / len(agent_confidences)
            
        # Weighted average (concepts weighted more heavily)
        if concepts and agent_responses:
            return (0.6 * concept_conf) + (0.4 * agent_conf)
        elif concepts:
            return concept_conf
        else:
            return agent_conf
            
    async def record_synthesis(
        self,
        result: MetaResult,
        importance: float = 0.7
    ):
        """Record synthesis result in memory system."""
        if self.store:
            try:
                await self.store.store_memory(
                    content={
                        "type": "synthesis",
                        "response": result.response,
                        "concepts": result.concepts,
                        "key_points": result.key_points,
                        "confidence": result.confidence,
                        "metadata": result.metadata,
                        "timestamp": result.timestamp
                    },
                    importance=importance,
                    domain=self.domain
                )
            except Exception as e:
                logger.error(f"Error recording synthesis: {str(e)}")
