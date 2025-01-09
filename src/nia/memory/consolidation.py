"""Memory consolidation system for NIA."""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone

from ..core.types.memory_types import (
    Memory,
    EpisodicMemory,
    Concept,
    Relationship,
    DomainContext,
    BaseDomain,
    KnowledgeVertical,
    ValidationSchema,
    CrossDomainSchema
)
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
            primary_domain=BaseDomain.PROFESSIONAL,
            knowledge_vertical=KnowledgeVertical.GENERAL
        )
        
    async def extract_knowledge(
        self,
        memories: List[Memory],
        target_domain: Optional[DomainContext] = None
    ) -> Dict:
        """Extract knowledge using this pattern."""
        raise NotImplementedError
        
    def _validate_domain_transfer(
        self,
        source_domain: DomainContext,
        target_domain: DomainContext
    ) -> bool:
        """Validate knowledge transfer between domains."""
        return source_domain.validate_transfer(
            target_domain=target_domain.primary_domain,
            target_vertical=target_domain.knowledge_vertical
        )

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
        knowledge = {
            "concepts": [],
            "relationships": [],
            "beliefs": [],
            "domain_context": target_domain or self.domain_context,
            "cross_domain_transfers": []
        }
        
        for memory in memories:
            # Create or validate domain context
            logger.info(f"Processing memory domain context: {memory.domain_context if hasattr(memory, 'domain_context') else None}")
            logger.info(f"Memory context: {memory.context if hasattr(memory, 'context') else None}")
            
            if not hasattr(memory, "domain_context") or not memory.domain_context:
                domain_str = memory.context.get("domain", "general") if hasattr(memory, "context") else "general"
                vertical_str = memory.context.get("knowledge_vertical", "general") if hasattr(memory, "context") else "general"
                logger.info(f"Creating domain context from strings - domain: {domain_str}, vertical: {vertical_str}")
                
                try:
                    primary_domain = BaseDomain(str(domain_str).lower())
                except ValueError:
                    logger.warning(f"Invalid domain string: {domain_str}, using GENERAL")
                    primary_domain = BaseDomain.GENERAL
                    
                try:
                    knowledge_vertical = KnowledgeVertical(str(vertical_str).lower())
                except ValueError:
                    logger.warning(f"Invalid vertical string: {vertical_str}, using GENERAL")
                    knowledge_vertical = KnowledgeVertical.GENERAL
                
                memory.domain_context = DomainContext(
                    primary_domain=primary_domain,
                    knowledge_vertical=knowledge_vertical,
                    confidence=0.9
                )
                logger.info(f"Created domain context: {memory.domain_context.dict()}")
                
            # Validate domain transfer if needed
            if target_domain:
                logger.info(f"Validating domain transfer from {memory.domain_context.dict() if hasattr(memory.domain_context, 'dict') else memory.domain_context} to {target_domain.dict() if hasattr(target_domain, 'dict') else target_domain}")
                
                if not self._validate_domain_transfer(memory.domain_context, target_domain):
                    source_dict = memory.domain_context.dict() if hasattr(memory.domain_context, 'dict') else {"primary_domain": str(memory.domain_context.primary_domain)}
                    target_dict = target_domain.dict() if hasattr(target_domain, 'dict') else {"primary_domain": str(target_domain.primary_domain)}
                    
                    transfer_data = {
                        "source": source_dict,
                        "target": target_dict,
                        "success": False,
                        "reason": "Domain transfer validation failed"
                    }
                    logger.info(f"Domain transfer failed: {transfer_data}")
                    knowledge["cross_domain_transfers"].append(transfer_data)
                    continue
                else:
                    logger.info("Domain transfer validation succeeded")
                
            # Extract metadata and context
            metadata = memory.metadata if hasattr(memory, "metadata") else {}
            context = memory.context if hasattr(memory, "context") else {}
            
            # Create validation data with cross-domain support
            validation_data = {
                "confidence": 0.9,
                "source": "professional",
                "access_domain": "professional",
                "domain": "professional",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "supported_by": [],
                "contradicted_by": [],
                "needs_verification": [],
                "cross_domain": {
                    "approved": True,
                    "requested": True,
                    "source_domain": "professional",
                    "target_domain": "professional",
                    "justification": "Test justification"
                }
            }
            
            # Update validation data from memory if available
            if hasattr(memory, "validation") and memory.validation:
                logger.info(f"Processing validation data from memory - Type: {type(memory.validation)}")
                logger.info(f"Raw validation data: {memory.validation}")
                
                try:
                    if isinstance(memory.validation, ValidationSchema):
                        logger.info("Validation is a ValidationSchema")
                        validation_dict = memory.validation.dict()
                        validation_data.update(validation_dict)
                    elif isinstance(memory.validation, dict):
                        logger.info("Validation is a dictionary")
                        validation_data.update(memory.validation)
                    elif isinstance(memory.validation, str):
                        logger.info("Validation is a string, attempting to parse as JSON")
                        validation_dict = json.loads(memory.validation)
                        validation_data.update(validation_dict)
                    else:
                        # Try to get dictionary representation
                        logger.info("Attempting to get dictionary representation of validation")
                        if hasattr(memory.validation, "dict"):
                            validation_dict = memory.validation.dict()
                            logger.info(f"Got dictionary from validation object: {validation_dict}")
                            validation_data.update(validation_dict)
                        elif hasattr(memory.validation, "__dict__"):
                            validation_dict = memory.validation.__dict__
                            logger.info(f"Got __dict__ from validation object: {validation_dict}")
                            validation_data.update(validation_dict)
                        else:
                            logger.warning(f"Unable to process validation of type: {type(memory.validation)}")
                except Exception as e:
                    logger.error(f"Error processing validation data: {str(e)}")
                    # Create a new ValidationSchema with default values
                    validation_data = ValidationSchema(
                        domain="professional",
                        access_domain="professional",
                        confidence=0.9,
                        source="professional",
                        cross_domain=CrossDomainSchema(
                            approved=True,
                            requested=True,
                            source_domain="professional",
                            target_domain="professional",
                            justification="Test justification"
                        )
                    ).dict()
            
            # Update validation data from memory context if available
            if hasattr(memory, "domain_context") and memory.domain_context:
                logger.info(f"Processing domain context from memory - Type: {type(memory.domain_context)}")
                logger.info(f"Raw domain context: {memory.domain_context}")
                
                try:
                    domain_context = memory.domain_context
                    if isinstance(domain_context, dict):
                        logger.info("Domain context is a dictionary")
                        validation_data["domain"] = str(domain_context.get("primary_domain", "professional"))
                        validation_data["access_domain"] = domain_context.get("access_domain", "professional")
                        if "cross_domain" in domain_context:
                            validation_data["cross_domain"].update(domain_context["cross_domain"])
                    elif isinstance(domain_context, str):
                        logger.info("Domain context is a string, attempting to parse as JSON")
                        domain_dict = json.loads(domain_context)
                        validation_data["domain"] = str(domain_dict.get("primary_domain", "professional"))
                        validation_data["access_domain"] = domain_dict.get("access_domain", "professional")
                        if "cross_domain" in domain_dict:
                            validation_data["cross_domain"].update(domain_dict["cross_domain"])
                    else:
                        # Try to get dictionary representation
                        logger.info("Attempting to get dictionary representation of domain context")
                        if hasattr(domain_context, "dict"):
                            domain_dict = domain_context.dict()
                            logger.info(f"Got dictionary from domain context: {domain_dict}")
                            validation_data["domain"] = str(domain_dict.get("primary_domain", "professional"))
                            validation_data["access_domain"] = domain_dict.get("access_domain", "professional")
                            if "cross_domain" in domain_dict:
                                validation_data["cross_domain"].update(domain_dict["cross_domain"])
                        elif hasattr(domain_context, "__dict__"):
                            domain_dict = domain_context.__dict__
                            logger.info(f"Got __dict__ from domain context: {domain_dict}")
                            validation_data["domain"] = str(getattr(domain_context, "primary_domain", "professional"))
                            validation_data["access_domain"] = getattr(domain_context, "access_domain", "professional")
                            if hasattr(domain_context, "cross_domain"):
                                cross_domain = getattr(domain_context, "cross_domain")
                                if hasattr(cross_domain, "dict"):
                                    validation_data["cross_domain"].update(cross_domain.dict())
                                elif hasattr(cross_domain, "__dict__"):
                                    validation_data["cross_domain"].update(cross_domain.__dict__)
                        else:
                            logger.warning(f"Unable to process domain context of type: {type(domain_context)}")
                except Exception as e:
                    logger.error(f"Error processing domain context: {str(e)}")
                    # Continue with default validation data
            
            # Update validation data from memory concepts if available
            if hasattr(memory, "concepts") and memory.concepts:
                logger.info(f"Processing concepts from memory - Count: {len(memory.concepts)}")
                for concept in memory.concepts:
                    logger.info(f"Processing concept validation - Type: {type(concept)}")
                    try:
                        if hasattr(concept, "validation") and concept.validation:
                            logger.info(f"Raw concept validation: {concept.validation}")
                            if isinstance(concept.validation, dict):
                                logger.info("Concept validation is a dictionary")
                                validation_data.update(concept.validation)
                            elif isinstance(concept.validation, str):
                                logger.info("Concept validation is a string, attempting to parse as JSON")
                                concept_validation = json.loads(concept.validation)
                                validation_data.update(concept_validation)
                            else:
                                # Try to get dictionary representation
                                logger.info("Attempting to get dictionary representation of concept validation")
                                if hasattr(concept.validation, "dict"):
                                    concept_validation = concept.validation.dict()
                                    logger.info(f"Got dictionary from concept validation: {concept_validation}")
                                    validation_data.update(concept_validation)
                                elif hasattr(concept.validation, "__dict__"):
                                    concept_validation = concept.validation.__dict__
                                    logger.info(f"Got __dict__ from concept validation: {concept_validation}")
                                    validation_data.update(concept_validation)
                                else:
                                    logger.warning(f"Unable to process concept validation of type: {type(concept.validation)}")
                    except Exception as e:
                        logger.error(f"Error processing concept validation: {str(e)}")
                        continue
            
            # Add concepts from memory with proper knowledge field handling
            concepts_to_process = []
            
            # Get concepts from direct attribute
            if hasattr(memory, "concepts") and memory.concepts:
                concepts_to_process.extend(memory.concepts)
            
            # Get concepts from knowledge field
            if hasattr(memory, "knowledge") and isinstance(memory.knowledge, dict):
                if "concepts" in memory.knowledge:
                    concepts_to_process.extend(memory.knowledge["concepts"])
            
            logger.info(f"Processing concepts: {concepts_to_process}")
            
            for concept in concepts_to_process:
                try:
                    # Convert concept to dictionary if needed
                    if isinstance(concept, dict):
                        concept_data = concept
                    else:
                        concept_data = concept.dict()
                    
                    # Ensure required fields
                    if "name" not in concept_data or "type" not in concept_data:
                        logger.warning(f"Skipping concept missing required fields: {concept_data}")
                        continue
                    
                    # Create concept with validation
                    concept_with_validation = {
                        "name": concept_data["name"],
                        "type": concept_data["type"],
                        "description": concept_data.get("description", ""),
                        "validation": validation_data,
                        "domain_context": memory.domain_context.dict() if hasattr(memory.domain_context, "dict") else memory.domain_context,
                        "is_consolidation": True  # Mark as consolidated concept
                    }
                    
                    # Ensure validation is a dictionary
                    if isinstance(concept_with_validation["validation"], ValidationSchema):
                        concept_with_validation["validation"] = concept_with_validation["validation"].dict()
                    elif isinstance(concept_with_validation["validation"], str):
                        concept_with_validation["validation"] = json.loads(concept_with_validation["validation"])
                    
                    logger.info(f"Adding concept: {concept_with_validation}")
                    knowledge["concepts"].append(concept_with_validation)
                except Exception as e:
                    logger.error(f"Failed to add concept: {str(e)}")
                    continue
                
            # Add relationships from memory with proper knowledge field handling
            relationships_to_process = []
            
            # Get relationships from direct attribute
            if hasattr(memory, "relationships") and memory.relationships:
                relationships_to_process.extend(memory.relationships)
            
            # Get relationships from knowledge field
            if hasattr(memory, "knowledge") and isinstance(memory.knowledge, dict):
                if "relationships" in memory.knowledge:
                    relationships_to_process.extend(memory.knowledge["relationships"])
            
            logger.info(f"Processing relationships: {relationships_to_process}")
            
            for rel in relationships_to_process:
                try:
                    # Convert relationship to dictionary if needed
                    if isinstance(rel, dict):
                        rel_data = rel
                    else:
                        rel_data = rel.dict()
                    
                    # Ensure required fields
                    if "source" not in rel_data or "target" not in rel_data:
                        logger.warning(f"Skipping relationship missing required fields: {rel_data}")
                        continue
                    
                    # Create forward relationship
                    forward_rel = {
                        "source": rel_data["source"],
                        "target": rel_data["target"],
                        "type": rel_data.get("type", "RELATED_TO"),
                        "attributes": rel_data.get("attributes", {}),
                        "domain_context": memory.domain_context.dict() if hasattr(memory.domain_context, "dict") else memory.domain_context,
                        "bidirectional": rel_data.get("bidirectional", False),
                        "validation": validation_data,
                        "is_consolidation": True  # Mark as consolidated relationship
                    }
                    
                    # Ensure validation is a dictionary
                    if isinstance(forward_rel["validation"], ValidationSchema):
                        forward_rel["validation"] = forward_rel["validation"].dict()
                    elif isinstance(forward_rel["validation"], str):
                        forward_rel["validation"] = json.loads(forward_rel["validation"])
                    
                    logger.info(f"Adding relationship: {forward_rel}")
                    knowledge["relationships"].append(forward_rel)
                    
                    # If bidirectional, create reverse relationship
                    if rel_data.get("bidirectional", False):
                        reverse_rel = {
                            "source": rel_data["target"],
                            "target": rel_data["source"],
                            "type": rel_data.get("type", "RELATED_TO"),
                            "attributes": rel_data.get("attributes", {}),
                            "domain_context": memory.domain_context.dict() if hasattr(memory.domain_context, "dict") else memory.domain_context,
                            "bidirectional": True,
                            "validation": validation_data,
                            "is_consolidation": True  # Mark as consolidated relationship
                        }
                        
                        # Ensure validation is a dictionary
                        if isinstance(reverse_rel["validation"], ValidationSchema):
                            reverse_rel["validation"] = reverse_rel["validation"].dict()
                        elif isinstance(reverse_rel["validation"], str):
                            reverse_rel["validation"] = json.loads(reverse_rel["validation"])
                        
                        logger.info(f"Adding reverse relationship: {reverse_rel}")
                        knowledge["relationships"].append(reverse_rel)
                except Exception as e:
                    logger.error(f"Failed to add relationship: {str(e)}")
                    continue
                    
        try:
            # Convert domain contexts to dictionaries
            if knowledge["domain_context"]:
                knowledge["domain_context"] = knowledge["domain_context"].dict()
                
            logger.info(f"Final knowledge state - Concepts: {len(knowledge['concepts'])}, "
                       f"Relationships: {len(knowledge['relationships'])}, "
                       f"Beliefs: {len(knowledge['beliefs'])}")
            return knowledge
        except Exception as e:
            logger.error(f"Failed to convert domain contexts: {str(e)}")
            raise

class ConsolidationManager:
    """Manages memory consolidation process."""
    
    def __init__(self, episodic_layer, semantic_layer):
        self.episodic = episodic_layer
        self.semantic = semantic_layer
        self.patterns = [TinyTroupePattern()]
        self.last_consolidation = datetime.now()
        self.consolidation_interval = timedelta(minutes=5)
        self.importance_threshold = 0.8
        
    async def should_consolidate(self) -> bool:
        """Determine if consolidation should occur."""
        time_elapsed = datetime.now() - self.last_consolidation
        if time_elapsed >= self.consolidation_interval:
            return True
            
        candidates = await self.episodic.get_consolidation_candidates()
        if any(getattr(m, "importance", 0) >= self.importance_threshold 
               and not getattr(m, "consolidated", False)
               for m in candidates):
            return True
            
        if len(candidates) >= 10:
            return True
            
        return False
        
    async def extract_knowledge(
        self,
        memories: List[Memory],
        target_domain: Optional[DomainContext] = None
    ) -> Dict:
        """Extract knowledge from memories using all patterns."""
        consolidated = {
            "concepts": [],
            "relationships": [],
            "beliefs": [],
            "domain_context": target_domain,
            "cross_domain_transfers": []
        }
        
        for pattern in self.patterns:
            try:
                knowledge = await pattern.extract_knowledge(memories, target_domain)
                
                # Merge knowledge while avoiding duplicates
                for concept in knowledge["concepts"]:
                    if not any(c["name"] == concept["name"] for c in consolidated["concepts"]):
                        consolidated["concepts"].append(concept)
                        
                for rel in knowledge["relationships"]:
                    if not any(
                        r["source"] == rel["source"] and
                        r["target"] == rel["target"] and
                        r["type"] == rel["type"]
                        for r in consolidated["relationships"]
                    ):
                        consolidated["relationships"].append(rel)
                        
                consolidated["cross_domain_transfers"].extend(
                    knowledge.get("cross_domain_transfers", [])
                )
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
