"""Validation handling for Neo4j concepts."""

from typing import Dict, Optional

class ValidationHandler:
    """Handles validation data for concepts."""
    
    @staticmethod
    def process_validation(
        validation: Optional[Dict],
        is_consolidation: bool
    ) -> Optional[Dict]:
        """Process validation data based on consolidation status."""
        # Return None if no validation provided
        if not validation:
            return None

        # Create a copy to avoid modifying original
        validation = dict(validation)
        confidence = validation.get("confidence")

        if confidence is not None:
            try:
                confidence = float(confidence)
                # For consolidated concepts, ensure confidence >= 0.8
                if is_consolidation and confidence < 0.8:
                    validation["confidence"] = 0.8
            except (TypeError, ValueError):
                validation["confidence"] = 0.8 if is_consolidation else 0.5

        return validation

    @staticmethod
    def build_validation_query(
        validation: Optional[Dict],
        is_consolidation: bool,
        params: Dict,
        base_query: str
    ) -> str:
        """Build Neo4j query for validation fields."""
        validation_fields = [
            "confidence",
            "uncertainties",
            "supported_by",
            "contradicted_by",
            "needs_verification"
        ]
        
        # First remove all validation fields
        query = base_query + "\nREMOVE " + ", ".join(f"c.{field}" for field in validation_fields)
        
        # Then set only the fields that are present if validation is provided
        if validation:
            for field in validation_fields:
                if field in validation and validation[field] is not None:
                    params[field] = validation[field]
                    query += f"\nSET c.{field} = ${field}"

        return query

    @staticmethod
    def extract_validation(concept: Dict) -> Optional[Dict]:
        """Extract validation data from a concept record."""
        if concept.get("confidence") is not None:
            validation = {"confidence": concept["confidence"]}
            for field in ["uncertainties", "supported_by", "contradicted_by", "needs_verification"]:
                if concept.get(field):
                    validation[field] = concept[field]
            return validation
        return None
