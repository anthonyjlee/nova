"""Nova's core validation functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationResult:
    """Container for validation results."""
    
    def __init__(
        self,
        is_valid: bool,
        validations: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.validations = validations
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class ValidationAgent:
    """Core validation functionality for Nova's ecosystem."""
    
    def __init__(
        self,
        llm=None,
        store=None,
        vector_store=None,
        domain: Optional[str] = None
    ):
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.domain = domain or "professional"  # Default to professional domain
        
    async def validate_content(
        self,
        content: Dict[str, Any],
        validation_type: str,
        metadata: Optional[Dict] = None
    ) -> ValidationResult:
        """Validate content with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar validations if vector store available
            similar_validations = []
            if self.vector_store:
                similar_validations = await self._get_similar_validations(
                    content,
                    validation_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "validation_type": validation_type,
                        "metadata": metadata,
                        "similar_validations": similar_validations
                    },
                    template="validation_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_validation(
                    content,
                    validation_type,
                    similar_validations
                )
                
            # Extract and validate results
            validations = self._extract_validations(analysis)
            issues = self._extract_issues(analysis)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(validations, issues)
            is_valid = self._determine_validity(validations, issues, confidence)
            
            return ValidationResult(
                is_valid=is_valid,
                validations=validations,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "validation_type": validation_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                validations=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_validations(
        self,
        content: Dict[str, Any],
        validation_type: str
    ) -> List[Dict]:
        """Get similar validations from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "validation",
                        "validation_type": validation_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar validations: {str(e)}")
        return []
            
    def _basic_validation(
        self,
        content: Dict[str, Any],
        validation_type: str,
        similar_validations: List[Dict]
    ) -> Dict:
        """Basic content validation without LLM."""
        validations = []
        issues = []
        
        # Basic validation rules
        validation_rules = {
            "structure": {
                "has_content": 0.8,
                "has_type": 0.7,
                "has_metadata": 0.6
            },
            "format": {
                "is_dict": 0.8,
                "has_required_fields": 0.7,
                "valid_types": 0.7
            },
            "domain": {
                "has_domain": 0.8,
                "domain_match": 0.7,
                "domain_consistency": 0.6
            }
        }
        
        # Check structure rules
        if validation_type == "structure":
            if "content" in content:
                validations.append({
                    "rule": "has_content",
                    "passed": True,
                    "confidence": validation_rules["structure"]["has_content"]
                })
            else:
                issues.append({
                    "type": "missing_content",
                    "severity": "high",
                    "description": "Content field is missing"
                })
                
            if "type" in content:
                validations.append({
                    "rule": "has_type",
                    "passed": True,
                    "confidence": validation_rules["structure"]["has_type"]
                })
            else:
                issues.append({
                    "type": "missing_type",
                    "severity": "medium",
                    "description": "Type field is missing"
                })
                
            if "metadata" in content:
                validations.append({
                    "rule": "has_metadata",
                    "passed": True,
                    "confidence": validation_rules["structure"]["has_metadata"]
                })
            else:
                issues.append({
                    "type": "missing_metadata",
                    "severity": "low",
                    "description": "Metadata field is missing"
                })
                
        # Check format rules
        elif validation_type == "format":
            if isinstance(content, dict):
                validations.append({
                    "rule": "is_dict",
                    "passed": True,
                    "confidence": validation_rules["format"]["is_dict"]
                })
            else:
                issues.append({
                    "type": "invalid_format",
                    "severity": "high",
                    "description": "Content must be a dictionary"
                })
                
            # Add similar validations as reference
            if similar_validations:
                validations.append({
                    "rule": "similar_formats",
                    "passed": True,
                    "confidence": 0.7,
                    "similar_count": len(similar_validations)
                })
                
        # Check domain rules
        elif validation_type == "domain":
            if "domain" in content:
                validations.append({
                    "rule": "has_domain",
                    "passed": True,
                    "confidence": validation_rules["domain"]["has_domain"]
                })
                
                if content["domain"] == self.domain:
                    validations.append({
                        "rule": "domain_match",
                        "passed": True,
                        "confidence": validation_rules["domain"]["domain_match"]
                    })
                else:
                    issues.append({
                        "type": "domain_mismatch",
                        "severity": "medium",
                        "description": f"Domain {content['domain']} does not match expected {self.domain}"
                    })
            else:
                issues.append({
                    "type": "missing_domain",
                    "severity": "high",
                    "description": "Domain field is missing"
                })
                
        return {
            "validations": validations,
            "issues": issues
        }
        
    def _extract_validations(self, analysis: Dict) -> List[Dict]:
        """Extract and validate validation results."""
        validations = analysis.get("validations", [])
        valid_validations = []
        
        for validation in validations:
            if isinstance(validation, dict) and "rule" in validation:
                valid_validation = {
                    "rule": str(validation["rule"]),
                    "passed": bool(validation.get("passed", False)),
                    "confidence": float(validation.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in validation:
                    valid_validation["description"] = str(validation["description"])
                if "details" in validation:
                    valid_validation["details"] = str(validation["details"])
                if "domain_relevance" in validation:
                    valid_validation["domain_relevance"] = float(validation["domain_relevance"])
                if "severity" in validation:
                    valid_validation["severity"] = str(validation["severity"])
                if "similar_count" in validation:
                    valid_validation["similar_count"] = int(validation["similar_count"])
                    
                valid_validations.append(valid_validation)
                
        return valid_validations
        
    def _extract_issues(self, analysis: Dict) -> List[Dict]:
        """Extract and validate issues."""
        issues = analysis.get("issues", [])
        valid_issues = []
        
        for issue in issues:
            if isinstance(issue, dict) and "type" in issue:
                valid_issue = {
                    "type": str(issue["type"]),
                    "severity": str(issue.get("severity", "medium")),
                    "description": str(issue.get("description", "Unknown issue"))
                }
                
                # Add optional fields
                if "details" in issue:
                    valid_issue["details"] = str(issue["details"])
                if "domain_impact" in issue:
                    valid_issue["domain_impact"] = float(issue["domain_impact"])
                if "suggested_fix" in issue:
                    valid_issue["suggested_fix"] = str(issue["suggested_fix"])
                if "related_rules" in issue:
                    valid_issue["related_rules"] = [str(r) for r in issue["related_rules"]]
                    
                valid_issues.append(valid_issue)
                
        return valid_issues
        
    def _calculate_confidence(
        self,
        validations: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall validation confidence."""
        if not validations:
            return 0.0
            
        # Base confidence from validation confidences
        validation_conf = sum(v.get("confidence", 0.5) for v in validations) / len(validations)
        
        # Issue impact on confidence
        issue_impact = 0.0
        if issues:
            severity_weights = {
                "low": 0.1,
                "medium": 0.3,
                "high": 0.5
            }
            
            total_impact = sum(
                severity_weights.get(i.get("severity", "medium"), 0.3)
                for i in issues
            )
            issue_impact = total_impact / len(issues)
            
        # Final confidence calculation
        return max(0.0, validation_conf - issue_impact)
        
    def _determine_validity(
        self,
        validations: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall validity based on validations and issues."""
        if not validations:
            return False
            
        # Check for critical issues
        has_critical_issues = any(
            i.get("severity") == "high"
            for i in issues
        )
        if has_critical_issues:
            return False
            
        # Check validation results
        passed_validations = sum(1 for v in validations if v.get("passed", False))
        validation_ratio = passed_validations / len(validations)
        
        # Consider both validation ratio and confidence
        return validation_ratio >= 0.7 and confidence >= 0.6
