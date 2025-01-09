"""Validation handling for Neo4j concepts."""

import json
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ValidationHandler:
    """Handles validation data for concepts."""
    
    @staticmethod
    def process_validation(
        validation: Optional[Dict],
        is_consolidation: bool
    ) -> Dict:
        """Process validation data based on consolidation status.
        
        Returns a dict with primitive validation fields suitable for Neo4j storage.
        """
        # Initialize default validation with required fields
        processed = {
            "confidence": 0.8 if is_consolidation else 0.5,
            "source": "professional",
            "access_domain": "professional",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": "professional",
            "supported_by": [],
            "contradicted_by": [],
            "needs_verification": []
        }

        if not validation:
            return processed

        try:
            logger.info(f"Processing validation data: {validation}")
            logger.info(f"Is consolidation: {is_consolidation}")
            
            if isinstance(validation, dict):
                # Extract primitive fields
                if "confidence" in validation:
                    try:
                        confidence = float(validation["confidence"])
                        # For consolidated concepts, ensure confidence >= 0.8
                        if is_consolidation:
                            processed["confidence"] = max(0.8, confidence)
                        else:
                            processed["confidence"] = confidence
                        logger.info(f"Processed confidence: {processed['confidence']}")
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Failed to process confidence: {str(e)}")
                        pass

                # Copy required validation fields, preserving original values
                processed["source"] = str(validation.get("source", processed["source"]))
                processed["access_domain"] = str(validation.get("access_domain", processed["access_domain"]))
                processed["domain"] = str(validation.get("domain", processed["domain"]))
                
                # Handle cross_domain data
                if "cross_domain" in validation:
                    if isinstance(validation["cross_domain"], dict):
                        processed["cross_domain"] = {
                            "approved": validation["cross_domain"].get("approved", False),
                            "requested": validation["cross_domain"].get("requested", False),
                            "source_domain": validation["cross_domain"].get("source_domain"),
                            "target_domain": validation["cross_domain"].get("target_domain"),
                            "justification": validation["cross_domain"].get("justification")
                        }
                elif "context" in validation and isinstance(validation["context"], dict):
                    # Extract cross-domain info from memory context
                    if "cross_domain" in validation["context"]:
                        context_cross_domain = validation["context"]["cross_domain"]
                        if isinstance(context_cross_domain, dict):
                            processed["cross_domain"] = {
                                "approved": context_cross_domain.get("approved", False),
                                "requested": context_cross_domain.get("requested", False),
                                "source_domain": context_cross_domain.get("source_domain"),
                                "target_domain": context_cross_domain.get("target_domain"),
                                "justification": context_cross_domain.get("justification")
                            }
                
                logger.info(f"Processed validation fields - Source: {processed['source']}, "
                          f"Access Domain: {processed['access_domain']}, "
                          f"Domain: {processed['domain']}, "
                          f"Cross Domain: {processed.get('cross_domain')}")
                
                # Copy validation lists
                processed["supported_by"] = validation.get("supported_by", [])
                processed["contradicted_by"] = validation.get("contradicted_by", [])
                processed["needs_verification"] = validation.get("needs_verification", [])
                logger.info(f"Processed validation lists - Supported: {len(processed['supported_by'])}, "
                          f"Contradicted: {len(processed['contradicted_by'])}, "
                          f"Needs Verification: {len(processed['needs_verification'])}")
                
                # Use provided timestamp or current time
                if "timestamp" in validation:
                    try:
                        # Validate timestamp format
                        datetime.fromisoformat(validation["timestamp"].replace('Z', '+00:00'))
                        processed["timestamp"] = validation["timestamp"]
                        logger.info(f"Using provided timestamp: {processed['timestamp']}")
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Failed to process timestamp: {str(e)}")
                        pass

            elif isinstance(validation, list):
                # Convert list to dict and process
                logger.info("Converting validation list to dict")
                return ValidationHandler.process_validation(dict(validation), is_consolidation)
            else:
                logger.warning(f"Unexpected validation type: {type(validation)}")

        except Exception as e:
            logger.error(f"Error processing validation: {str(e)}")
            logger.error(f"Validation data that caused error: {validation}")

        logger.info(f"Final processed validation: {processed}")
        return processed

    @staticmethod
    def extract_validation(concept: Dict) -> Dict:
        """Extract validation data from a concept record.
        
        Returns a dict with validation fields from primitive concept properties.
        """
        # Try to get validation from validation_json first
        validation = {}
        try:
            if concept.get("validation"):
                validation = json.loads(concept["validation"])
        except (json.JSONDecodeError, TypeError):
            pass

        # Fill in any missing fields with stored primitive values
        if not validation:
            validation = {
                "confidence": float(concept.get("confidence", 0.0)),
                "source": str(concept.get("validation_source", "professional")),
                "access_domain": str(concept.get("access_domain", "professional")),
                "domain": str(concept.get("domain", "professional")),
                "timestamp": str(concept.get("validation_timestamp", datetime.now(timezone.utc).isoformat())),
                "supported_by": concept.get("supported_by", []),
                "contradicted_by": concept.get("contradicted_by", []),
                "needs_verification": concept.get("needs_verification", [])
            }

        # Ensure cross-domain information is present
        if "cross_domain" not in validation:
            if concept.get("cross_domain_approved") is not None:
                validation["cross_domain"] = {
                    "approved": concept.get("cross_domain_approved", False),
                    "requested": concept.get("cross_domain_requested", False),
                    "source_domain": concept.get("cross_domain_source", None),
                    "target_domain": concept.get("cross_domain_target", None),
                    "justification": concept.get("cross_domain_justification", "")
                }
            else:
                validation["cross_domain"] = {
                    "approved": False,
                    "requested": False
                }
        
        return validation
