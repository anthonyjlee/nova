"""Validation handling for Neo4j concepts."""

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
            "source": "system",
            "access_domain": "general",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": "general",
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

                # Copy required validation fields
                processed["source"] = str(validation.get("source", "system"))
                processed["access_domain"] = str(validation.get("access_domain", "general"))
                processed["domain"] = str(validation.get("domain", "general"))
                logger.info(f"Processed validation fields - Source: {processed['source']}, "
                          f"Access Domain: {processed['access_domain']}, "
                          f"Domain: {processed['domain']}")
                
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
        validation = {
            "confidence": float(concept.get("confidence", 0.0)),
            "source": str(concept.get("validation_source", "system")),
            "access_domain": str(concept.get("access_domain", "general")),
            "domain": str(concept.get("domain", "general")),
            "timestamp": str(concept.get("validation_timestamp", datetime.now(timezone.utc).isoformat())),
            "supported_by": concept.get("supported_by", []),
            "contradicted_by": concept.get("contradicted_by", []),
            "needs_verification": concept.get("needs_verification", [])
        }
        
        return validation
