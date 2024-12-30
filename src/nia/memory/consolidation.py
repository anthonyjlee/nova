"""Memory consolidation management for NIA."""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from nia.memory.memory_types import Memory

logger = logging.getLogger(__name__)

class ConsolidationPattern:
    """Base class for memory consolidation patterns."""
    
    def __init__(self, pattern_type: str, threshold: float = 0.7):
        self.type = pattern_type
        self.threshold = threshold
        
    async def find_matches(self, memories: List[Memory]) -> List[Dict]:
        """Find pattern matches in memories."""
        raise NotImplementedError

class ConceptPattern(ConsolidationPattern):
    """Pattern for extracting concepts from memories."""
    
    def __init__(self):
        super().__init__("concept", threshold=0.7)
        
    async def find_matches(self, memories: List[Memory]) -> List[Dict]:
        """Find concept patterns in memories."""
        concepts = []
        for memory in memories:
            # Extract concepts from memory content
            if hasattr(memory, "concepts"):
                for concept in memory.concepts:
                    concepts.append({
                        "type": concept.get("type", "Concept"),
                        "properties": {
                            "name": concept.get("name"),
                            "category": concept.get("category"),
                            "attributes": concept.get("attributes", {})
                        }
                    })
        return concepts

class RelationshipPattern(ConsolidationPattern):
    """Pattern for extracting relationships from memories."""
    
    def __init__(self):
        super().__init__("relationship", threshold=0.7)
        
    async def find_matches(self, memories: List[Memory]) -> List[Dict]:
        """Find relationship patterns in memories."""
        relationships = []
        for memory in memories:
            # Extract relationships from memory content
            if hasattr(memory, "relationships"):
                for rel in memory.relationships:
                    relationships.append({
                        "from": rel.get("from"),
                        "to": rel.get("to"),
                        "type": rel.get("type", "RELATED_TO"),
                        "properties": rel.get("properties", {})
                    })
        return relationships

class BeliefPattern(ConsolidationPattern):
    """Pattern for extracting beliefs from memories."""
    
    def __init__(self):
        super().__init__("belief", threshold=0.8)
        
    async def find_matches(self, memories: List[Memory]) -> List[Dict]:
        """Find belief patterns in memories."""
        beliefs = []
        for memory in memories:
            # Extract beliefs from memory content
            if hasattr(memory, "beliefs"):
                for belief in memory.beliefs:
                    beliefs.append({
                        "subject": belief.get("subject"),
                        "predicate": belief.get("predicate"),
                        "object": belief.get("object"),
                        "confidence": belief.get("confidence", 1.0)
                    })
        return beliefs

class ConsolidationManager:
    """Manages memory consolidation process."""
    
    def __init__(self, episodic, semantic):
        self.episodic = episodic
        self.semantic = semantic
        self.patterns = [
            ConceptPattern(),
            RelationshipPattern(),
            BeliefPattern()
        ]
        self.consolidation_rules = {
            "time_based": {
                "interval": timedelta(hours=1),
                "enabled": True
            },
            "volume_based": {
                "threshold": 100,
                "enabled": True
            },
            "importance_based": {
                "threshold": 0.8,
                "enabled": True
            }
        }
        self.last_consolidation = datetime.now()
        
    async def should_consolidate(self) -> bool:
        """Check if consolidation is needed based on multiple criteria."""
        if self.consolidation_rules["time_based"]["enabled"]:
            if await self._check_time_threshold():
                return True
                
        if self.consolidation_rules["volume_based"]["enabled"]:
            if await self._check_volume_threshold():
                return True
                
        if self.consolidation_rules["importance_based"]["enabled"]:
            if await self._check_importance_threshold():
                return True
                
        return False
        
    async def _check_time_threshold(self) -> bool:
        """Check if enough time has passed since last consolidation."""
        time_since_last = datetime.now() - self.last_consolidation
        return time_since_last >= self.consolidation_rules["time_based"]["interval"]
        
    async def _check_volume_threshold(self) -> bool:
        """Check if memory volume exceeds threshold."""
        pending_count = len(self.episodic.pending_consolidation)
        return pending_count >= self.consolidation_rules["volume_based"]["threshold"]
        
    async def _check_importance_threshold(self) -> bool:
        """Check if important memories need consolidation."""
        memories = await self.episodic.get_consolidation_candidates()
        importance_scores = [
            self._calculate_importance(memory)
            for memory in memories
        ]
        return max(importance_scores, default=0) > self.consolidation_rules["importance_based"]["threshold"]
        
    def _calculate_importance(self, memory: Memory) -> float:
        """Calculate importance score for a memory."""
        # Basic importance calculation - can be enhanced
        importance = 0.0
        
        # Check for key attributes
        if hasattr(memory, "importance"):
            importance = memory.importance
        
        # Check for relationships
        if hasattr(memory, "relationships") and memory.relationships:
            importance += 0.2
            
        # Check for concepts
        if hasattr(memory, "concepts") and memory.concepts:
            importance += 0.2
            
        # Check for beliefs
        if hasattr(memory, "beliefs") and memory.beliefs:
            importance += 0.2
            
        return min(importance, 1.0)
        
    async def extract_knowledge(self, memories: List[Memory]) -> Dict:
        """Extract semantic knowledge from episodic memories."""
        knowledge = {
            "concepts": [],
            "relationships": [],
            "beliefs": []
        }
        
        # Group related memories
        memory_groups = self._group_related_memories(memories)
        
        # Extract patterns from each group
        for group in memory_groups:
            # Apply each pattern matcher
            for pattern in self.patterns:
                matches = await pattern.find_matches(group)
                if matches:
                    knowledge[f"{pattern.type}s"].extend(matches)
                    
        return knowledge
        
    def _group_related_memories(self, memories: List[Memory]) -> List[List[Memory]]:
        """Group related memories together."""
        # Basic grouping by time proximity - can be enhanced
        groups = []
        current_group = []
        
        for memory in sorted(memories, key=lambda m: m.timestamp):
            if not current_group:
                current_group = [memory]
            else:
                # Check time proximity
                last_memory = current_group[-1]
                time_diff = memory.timestamp - last_memory.timestamp
                
                if time_diff <= timedelta(minutes=30):  # Configurable threshold
                    current_group.append(memory)
                else:
                    groups.append(current_group)
                    current_group = [memory]
                    
        if current_group:
            groups.append(current_group)
            
        return groups
