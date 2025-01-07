"""Memory consolidation system for NIA."""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..core.types.memory_types import Memory, Concept, Relationship
from ..core.neo4j.concept_store import ConceptStore

logger = logging.getLogger(__name__)

class ConsolidationPattern:
    """Base class for memory consolidation patterns."""
    
    def __init__(self, name: str, threshold: float = 0.7):
        self.name = name
        self.threshold = threshold
        
    async def extract_knowledge(self, memories: List[Memory]) -> Dict:
        """Extract knowledge using this pattern."""
        raise NotImplementedError

class TinyTroupePattern(ConsolidationPattern):
    """Pattern for extracting TinyTroupe-specific knowledge."""
    
    def __init__(self):
        super().__init__("tinytroupe", threshold=0.7)
        
    async def extract_knowledge(self, memories: List[Memory]) -> Dict:
        """Extract TinyTroupe-specific knowledge from memories."""
        knowledge = {
            "concepts": [],
            "relationships": [],
            "beliefs": []
        }
        
        for memory in memories:
            metadata = memory.get("metadata", {})
            
            # Extract agent-related concepts
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
                    "confidence": 0.9
                })
                
            # Extract task-related concepts
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
                    "confidence": 0.8
                })
                
            # Extract agent relationships
            for interaction in metadata.get("interactions", []):
                knowledge["relationships"].append({
                    "from": interaction["source_agent"],
                    "to": interaction["target_agent"],
                    "type": interaction["type"],
                    "attributes": {
                        "timestamp": interaction["timestamp"],
                        "context": interaction["context"]
                    }
                })
                
            # Extract beliefs about agent capabilities
            for observation in metadata.get("observations", []):
                if observation["type"] == "capability":
                    knowledge["beliefs"].append({
                        "subject": observation["agent"],
                        "predicate": "HAS_CAPABILITY",
                        "object": observation["capability"],
                        "confidence": observation["confidence"]
                    })
                    
            # Add concepts and relationships from memory
            for concept in memory.get("concepts", []):
                knowledge["concepts"].append({
                    "name": concept["name"],
                    "type": concept["type"],
                    "category": concept["category"],
                    "description": concept["description"],
                    "attributes": concept["attributes"],
                    "confidence": concept["confidence"]
                })
                
            for rel in memory.get("relationships", []):
                knowledge["relationships"].append({
                    "from": rel["from_concept"],
                    "to": rel["to_concept"],
                    "type": rel["type"],
                    "attributes": rel.get("properties", {})
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
        
    async def extract_knowledge(self, memories: List[Memory]) -> Dict:
        """Extract knowledge from memories using all patterns."""
        consolidated = {
            "concepts": [],
            "relationships": [],
            "beliefs": []
        }
        
        # Apply each pattern
        for pattern in self.patterns:
            try:
                knowledge = await pattern.extract_knowledge(memories)
                
                # Merge knowledge while avoiding duplicates
                for concept in knowledge["concepts"]:
                    if not any(c["name"] == concept["name"] for c in consolidated["concepts"]):
                        consolidated["concepts"].append(concept)
                        
                for rel in knowledge["relationships"]:
                    if not any(r["from"] == rel["from"] and r["to"] == rel["to"] 
                              and r["type"] == rel["type"] for r in consolidated["relationships"]):
                        consolidated["relationships"].append(rel)
                        
                for belief in knowledge["beliefs"]:
                    if not any(b["subject"] == belief["subject"] and b["predicate"] == belief["predicate"]
                              and b["object"] == belief["object"] for b in consolidated["beliefs"]):
                        consolidated["beliefs"].append(belief)
                        
            except Exception as e:
                logger.error(f"Error applying pattern {pattern.name}: {str(e)}")
                continue
                
        return consolidated
        
    def add_pattern(self, pattern: ConsolidationPattern):
        """Add a new consolidation pattern."""
        self.patterns.append(pattern)
        
    def remove_pattern(self, pattern_name: str):
        """Remove a consolidation pattern by name."""
        self.patterns = [p for p in self.patterns if p.name != pattern_name]
