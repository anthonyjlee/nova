"""Memory consolidation system for NIA."""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..core.types.memory_types import Memory, Concept, Relationship
from ..core.neo4j.concept_store import ConceptStore

logger = logging.getLogger(__name__)

class ConsolidationPattern:
    """Base class for memory consolidation patterns."""
    
    def __init__(
        self,
        name: str,
        threshold: float = 0.7,
        domain_context: Optional[DomainContext] = None
    ):
        self.name = name
        self.threshold = threshold
        self.domain_context = domain_context or DomainContext(
            primary_domain=Domain.PROFESSIONAL,
            knowledge_vertical=None
        )
        
    async def extract_knowledge(
        self,
        memories: List[Memory],
        target_domain: Optional[DomainContext] = None
    ) -> Dict:
        """Extract knowledge using this pattern.
        
        Args:
            memories: List of memories to analyze
            target_domain: Optional target domain context for extraction
            
        Returns:
            Dict containing extracted knowledge with domain context
        """
        raise NotImplementedError
        
    def _validate_domain_transfer(
        self,
        source_domain: DomainContext,
        target_domain: DomainContext
    ) -> bool:
        """Validate knowledge transfer between domains."""
        # Always allow transfers within same domain
        if source_domain.primary_domain == target_domain.primary_domain:
            return True
            
        # Check if cross-domain operation is approved
        if source_domain.cross_domain and source_domain.cross_domain.get("approved"):
            if (source_domain.cross_domain.get("target_domain") == 
                target_domain.primary_domain):
                return True
                
        # Check knowledge vertical compatibility
        if (source_domain.knowledge_vertical and 
            target_domain.knowledge_vertical and
            source_domain.knowledge_vertical == target_domain.knowledge_vertical):
            return True
            
        return False

class TinyTroupePattern(ConsolidationPattern):
    """Pattern for extracting TinyTroupe-specific knowledge."""
    
    def __init__(self, domain_context: Optional[DomainContext] = None):
        super().__init__(
            "tinytroupe",
            threshold=0.7,
            domain_context=domain_context
        )
        
    async def extract_knowledge(
        self,
        memories: List[Memory],
        target_domain: Optional[DomainContext] = None
    ) -> Dict:
        """Extract TinyTroupe-specific knowledge from memories with domain awareness."""
        # Initialize knowledge with domain context
        knowledge = {
            "concepts": [],
            "relationships": [],
            "beliefs": [],
            "domain_context": target_domain or self.domain_context,
            "cross_domain_transfers": []
        }
        
        for memory in memories:
            # Skip memories without proper domain context
            if not memory.domain_context:
                continue
                
            # Validate domain transfer if needed
            if target_domain and not self._validate_domain_transfer(
                memory.domain_context,
                target_domain
            ):
                # Track failed transfer attempt
                knowledge["cross_domain_transfers"].append({
                    "source": memory.domain_context.dict(),
                    "target": target_domain.dict(),
                    "success": False,
                    "reason": "Domain transfer validation failed"
                })
                continue
                
            metadata = memory.get("metadata", {})
            
            # Extract agent-related concepts with domain context
            for agent in metadata.get("agents", []):
                knowledge["concepts"].append({
                    "name": agent["name"],
                    "type": "Agent",
                    "category": agent["type"],
                    "description": f"TinyTroupe agent specializing in {agent['type']}",
                    "attributes": {
                        "skills": agent["skills"],
                        "state": agent["state"]
                    },
                    "confidence": 0.9,
                    "domain_context": memory.domain_context.dict()
                })
                
            # Extract task-related concepts with domain context
            for task in metadata.get("tasks", []):
                knowledge["concepts"].append({
                    "name": task["name"],
                    "type": "Task",
                    "category": task["category"],
                    "description": task["description"],
                    "attributes": {
                        "status": task["status"],
                        "priority": task["priority"]
                    },
                    "confidence": 0.8,
                    "domain_context": memory.domain_context.dict()
                })
                
            # Extract agent relationships with domain context
            for interaction in metadata.get("interactions", []):
                knowledge["relationships"].append({
                    "from": interaction["source_agent"],
                    "to": interaction["target_agent"],
                    "type": interaction["type"],
                    "attributes": {
                        "timestamp": interaction["timestamp"],
                        "context": interaction["context"]
                    },
                    "domain_context": memory.domain_context.dict(),
                    "bidirectional": interaction.get("bidirectional", False)
                })
                
            # Extract beliefs about agent capabilities with domain context
            for observation in metadata.get("observations", []):
                if observation["type"] == "capability":
                    knowledge["beliefs"].append({
                        "subject": observation["agent"],
                        "predicate": "HAS_CAPABILITY",
                        "object": observation["capability"],
                        "confidence": observation["confidence"],
                        "domain_context": memory.domain_context.dict(),
                        "source": "capability_observation",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    
            # Add concepts and relationships from memory with domain context
            for concept in memory.get("concepts", []):
                if isinstance(concept, dict):
                    concept_data = concept
                else:
                    concept_data = concept.dict()
                    
                knowledge["concepts"].append({
                    **concept_data,
                    "domain_context": memory.domain_context.dict()
                })
                
            for rel in memory.get("relationships", []):
                if isinstance(rel, dict):
                    rel_data = rel
                else:
                    rel_data = rel.dict()
                    
                knowledge["relationships"].append({
                    **rel_data,
                    "domain_context": memory.domain_context.dict()
                })
                    
        return knowledge

class ConsolidationManager:
    """Manages memory consolidation process."""
    
    def __init__(self, episodic_layer, semantic_layer):
        self.episodic = episodic_layer
        self.semantic = semantic_layer
        self.patterns = [
            TinyTroupePattern()  # Add TinyTroupe pattern by default
        ]
        self.last_consolidation = datetime.now()
        self.consolidation_interval = timedelta(minutes=5)
        self.importance_threshold = 0.8
        
    async def should_consolidate(self) -> bool:
        """Determine if consolidation should occur."""
        # Check time-based trigger
        time_elapsed = datetime.now() - self.last_consolidation
        if time_elapsed >= self.consolidation_interval:
            return True
            
        # Check importance-based trigger
        candidates = await self.episodic.get_consolidation_candidates()
        if any(m.get("importance", 0) >= self.importance_threshold 
               and not m.get("consolidated", False)
               for m in candidates):
            return True
            
        # Check volume-based trigger
        if len(candidates) >= 10:  # Consolidate every 10 memories
            return True
            
        return False
        
    async def extract_knowledge(
        self,
        memories: List[Memory],
        target_domain: Optional[DomainContext] = None
    ) -> Dict:
        """Extract knowledge from memories using all patterns with domain awareness."""
        consolidated = {
            "concepts": [],
            "relationships": [],
            "beliefs": [],
            "domain_context": target_domain,
            "cross_domain_transfers": [],
            "knowledge_verticals": set()
        }
        
        # Group memories by domain
        domain_groups = {}
        for memory in memories:
            if not memory.domain_context:
                continue
                
            domain_key = (
                memory.domain_context.primary_domain,
                memory.domain_context.knowledge_vertical
            )
            if domain_key not in domain_groups:
                domain_groups[domain_key] = []
            domain_groups[domain_key].append(memory)
            
            # Track knowledge verticals
            if memory.domain_context.knowledge_vertical:
                consolidated["knowledge_verticals"].add(
                    memory.domain_context.knowledge_vertical
                )
        
        # Process each domain group
        for (primary_domain, knowledge_vertical), domain_memories in domain_groups.items():
            domain_context = DomainContext(
                primary_domain=primary_domain,
                knowledge_vertical=knowledge_vertical
            )
            
            # Apply each pattern to domain-specific memories
            for pattern in self.patterns:
                try:
                    knowledge = await pattern.extract_knowledge(
                        domain_memories,
                        target_domain=target_domain
                    )
                    
                    # Track cross-domain transfers
                    consolidated["cross_domain_transfers"].extend(
                        knowledge.get("cross_domain_transfers", [])
                    )
                    
                    # Merge knowledge while avoiding duplicates and maintaining domain context
                    for concept in knowledge["concepts"]:
                        if not any(
                            c["name"] == concept["name"] and
                            c["domain_context"] == concept["domain_context"]
                            for c in consolidated["concepts"]
                        ):
                            consolidated["concepts"].append(concept)
                            
                    for rel in knowledge["relationships"]:
                        if not any(
                            r["from"] == rel["from"] and
                            r["to"] == rel["to"] and
                            r["type"] == rel["type"] and
                            r["domain_context"] == rel["domain_context"]
                            for r in consolidated["relationships"]
                        ):
                            consolidated["relationships"].append(rel)
                            
                    for belief in knowledge["beliefs"]:
                        if not any(
                            b["subject"] == belief["subject"] and
                            b["predicate"] == belief["predicate"] and
                            b["object"] == belief["object"] and
                            b["domain_context"] == belief["domain_context"]
                            for b in consolidated["beliefs"]
                        ):
                            consolidated["beliefs"].append(belief)
                            
                except Exception as e:
                    logger.error(
                        f"Error applying pattern {pattern.name} to domain {domain_context}: {str(e)}"
                    )
                    continue
                    
        # Convert knowledge verticals set to list for serialization
        consolidated["knowledge_verticals"] = list(consolidated["knowledge_verticals"])
                
        return consolidated
        
    def add_pattern(
        self,
        pattern: ConsolidationPattern,
        domain_context: Optional[DomainContext] = None
    ):
        """Add a new consolidation pattern with optional domain context."""
        if domain_context:
            pattern.domain_context = domain_context
        self.patterns.append(pattern)
        
    def remove_pattern(
        self,
        pattern_name: str,
        domain_context: Optional[DomainContext] = None
    ):
        """Remove a consolidation pattern by name and optional domain context."""
        if domain_context:
            self.patterns = [
                p for p in self.patterns 
                if not (p.name == pattern_name and p.domain_context == domain_context)
            ]
        else:
            self.patterns = [p for p in self.patterns if p.name != pattern_name]
            
    async def get_domain_patterns(
        self,
        domain_context: DomainContext
    ) -> List[ConsolidationPattern]:
        """Get patterns applicable to a specific domain context."""
        return [
            p for p in self.patterns
            if (
                # Pattern matches primary domain
                p.domain_context.primary_domain == domain_context.primary_domain or
                # Pattern matches knowledge vertical
                (p.domain_context.knowledge_vertical and
                 p.domain_context.knowledge_vertical == domain_context.knowledge_vertical) or
                # Pattern is general (no knowledge vertical)
                not p.domain_context.knowledge_vertical
            )
        ]
