"""Nova's core response processing functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from nia.core.feature_flags import FeatureFlags
from .validation import ValidationPattern, ValidationResult, ValidationTracker

logger = logging.getLogger(__name__)

class ResponseValidationPattern(ValidationPattern):
    """Response-specific validation pattern."""
    response_type: str
    component_type: Optional[str] = None
    structure_type: Optional[str] = None

class ResponseResult(BaseModel):
    """Container for response processing results."""
    components: List[Dict]
    confidence: float
    metadata: Dict[str, Any] = {}
    structure: Dict[str, Any] = {}
    validation: Optional[ValidationResult] = None
    timestamp: str = datetime.now().isoformat()

class ResponseAgent:
    """Core response processing functionality for Nova's ecosystem."""
    
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
        self.validation_tracker = ValidationTracker()
        
    async def analyze_response(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None,
        debug_flags: Optional[FeatureFlags] = None
    ) -> ResponseResult:
        """Analyze response with domain and validation awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.debug(f"Analyzing response - content: {content}")
                
            # Get similar responses if vector store available
            similar_responses = []
            if self.vector_store:
                similar_responses = await self._get_similar_responses(
                    content,
                    debug_flags
                )
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata,
                        "similar_responses": similar_responses
                    },
                    template="response_analysis",
                    max_tokens=1000
                )
            else:
                analysis = await self._basic_analysis(
                    content,
                    similar_responses,
                    debug_flags
                )
                
            # Extract and validate components with validation tracking
            components = await self._extract_components(analysis, debug_flags)
            structure = await self._extract_structure(analysis, debug_flags)
            
            # Track validation patterns
            validation_issues = []
            
            # Validate components
            if not components:
                issue = {
                    "type": "missing_components",
                    "severity": "high",
                    "description": "Response has no valid components"
                }
                validation_issues.append(issue)
                
                if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                    logger.warning(f"Missing components detected: {issue}")
                    
            # Validate structure
            required_structure = ["sequence", "dependencies"]
            for req in required_structure:
                if req not in structure:
                    issue = {
                        "type": "missing_structure",
                        "severity": "medium",
                        "description": f"Response missing required structure: {req}"
                    }
                    validation_issues.append(issue)
                    
                    if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                        logger.warning(f"Missing structure detected: {issue}")
                        
            # Create validation result
            validation_result = ValidationResult(
                is_valid=len(validation_issues) == 0,
                issues=validation_issues,
                metadata={
                    "response_type": content.get("type", "unknown"),
                    "domain": self.domain,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Calculate confidence with validation awareness
            confidence = self._calculate_confidence(
                components,
                structure,
                validation_result
            )
            
            # Create response result
            result = ResponseResult(
                components=components,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown"),
                    "validation_timestamp": datetime.now().isoformat()
                },
                structure=structure,
                validation=validation_result
            )
            
            if debug_flags:
                if await debug_flags.is_debug_enabled('log_validation'):
                    logger.debug(f"Response analysis result: {result.dict()}")
                    
                    # Log critical patterns
                    critical_patterns = self.validation_tracker.get_critical_patterns()
                    if critical_patterns:
                        logger.warning(f"Critical response patterns detected: {critical_patterns}")
                        
                if not result.validation.is_valid and await debug_flags.is_debug_enabled('strict_mode'):
                    raise ValueError(f"Response validation failed: {validation_issues}")
                    
            return result
            
        except Exception as e:
            error_msg = f"Response analysis error: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.error(error_msg)
                
            return ResponseResult(
                components=[],
                confidence=0.0,
                metadata={
                    "error": str(e),
                    "domain": self.domain
                },
                structure={},
                validation=ValidationResult(
                    is_valid=False,
                    issues=[{
                        "type": "error",
                        "severity": "high",
                        "description": str(e)
                    }]
                )
            )
            
    async def _get_similar_responses(
        self,
        content: Dict[str, Any],
        debug_flags: Optional[FeatureFlags] = None
    ) -> List[Dict]:
        """Get similar responses from vector store with validation."""
        try:
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.debug(f"Finding similar responses for content: {content}")
                
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "response"
                    }
                )
                
                if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                    logger.debug(f"Found {len(results)} similar responses")
                    
                return results
                
        except Exception as e:
            error_msg = f"Error getting similar responses: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.error(error_msg)
                
        return []
            
    async def _basic_analysis(
        self,
        content: Dict[str, Any],
        similar_responses: List[Dict],
        debug_flags: Optional[FeatureFlags] = None
    ) -> Dict:
        """Basic response analysis with validation tracking."""
        components = []
        structure = {}
        validation_issues = []
        
        # Basic component extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic component indicators and their confidences
        component_indicators = {
            "statement": 0.8,
            "question": 0.8,
            "instruction": 0.7,
            "explanation": 0.7,
            "suggestion": 0.7,
            "clarification": 0.7,
            "reference": 0.6,
            "example": 0.6
        }
        
        # Check for component indicators with validation
        for indicator, base_confidence in component_indicators.items():
            if indicator in text:
                # Extract the component statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                component_statement = text[start_idx:end_idx].strip()
                if component_statement:
                    components.append({
                        "statement": component_statement,
                        "type": f"inferred_{indicator}",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                else:
                    issue = {
                        "type": "empty_component",
                        "severity": "medium",
                        "description": f"Empty {indicator} component detected"
                    }
                    validation_issues.append(issue)
                    
                    if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                        logger.warning(f"Empty component detected: {issue}")
                    
        # Add similar responses as structure with validation
        if similar_responses:
            structure["similar_responses"] = [
                {
                    "content": s.get("content", {}).get("content", ""),
                    "similarity": s.get("similarity", 0.0),
                    "timestamp": s.get("timestamp", "")
                }
                for s in similar_responses
            ]
        else:
            issue = {
                "type": "no_similar_responses",
                "severity": "low",
                "description": "No similar responses found"
            }
            validation_issues.append(issue)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.info(f"No similar responses: {issue}")
                
        return {
            "components": components,
            "structure": structure,
            "validation_issues": validation_issues
        }
        
    async def _extract_components(
        self,
        analysis: Dict,
        debug_flags: Optional[FeatureFlags] = None
    ) -> List[Dict]:
        """Extract and validate components with debug logging."""
        try:
            components = analysis.get("components", [])
            valid_components = []
            validation_issues = []
            
            for component in components:
                if isinstance(component, dict) and "statement" in component:
                    valid_component = {
                        "statement": str(component["statement"]),
                        "type": str(component.get("type", "component")),
                        "confidence": float(component.get("confidence", 0.5))
                    }
                    
                    # Add optional fields
                    if "description" in component:
                        valid_component["description"] = str(component["description"])
                    if "source" in component:
                        valid_component["source"] = str(component["source"])
                    if "domain_relevance" in component:
                        valid_component["domain_relevance"] = float(component["domain_relevance"])
                    if "intent" in component:
                        valid_component["intent"] = str(component["intent"])
                    if "context" in component:
                        valid_component["context"] = str(component["context"])
                    if "role" in component:
                        valid_component["role"] = str(component["role"])
                        
                    valid_components.append(valid_component)
                else:
                    issue = {
                        "type": "invalid_component",
                        "severity": "medium",
                        "description": "Component missing required fields"
                    }
                    validation_issues.append(issue)
                    
                    if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                        logger.warning(f"Invalid component detected: {issue}")
                        
            # Track validation patterns
            for issue in validation_issues:
                pattern = ResponseValidationPattern(
                    type=issue["type"],
                    description=issue["description"],
                    severity=issue["severity"],
                    response_type="component",
                    component_type=component.get("type"),
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    metadata={
                        "domain": self.domain
                    }
                )
                self.validation_tracker.add_issue(pattern.dict())
                    
            return valid_components
            
        except Exception as e:
            error_msg = f"Error extracting components: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.error(error_msg)
                
            return []
        
    async def _extract_structure(
        self,
        analysis: Dict,
        debug_flags: Optional[FeatureFlags] = None
    ) -> Dict:
        """Extract and validate structure with debug logging."""
        try:
            structure = analysis.get("structure", {})
            valid_structure = {}
            validation_issues = []
            
            if isinstance(structure, dict):
                # Extract similar responses with validation
                if "similar_responses" in structure:
                    valid_responses = []
                    for response in structure["similar_responses"]:
                        if isinstance(response, dict):
                            valid_response = {
                                "content": str(response.get("content", "")),
                                "similarity": float(response.get("similarity", 0.0)),
                                "timestamp": str(response.get("timestamp", ""))
                            }
                            valid_responses.append(valid_response)
                        else:
                            issue = {
                                "type": "invalid_similar_response",
                                "severity": "low",
                                "description": "Similar response has invalid format"
                            }
                            validation_issues.append(issue)
                            
                    valid_structure["similar_responses"] = valid_responses
                    
                # Extract sequence with validation
                if "sequence" in structure:
                    valid_sequence = []
                    for step in structure["sequence"]:
                        if isinstance(step, str):
                            valid_sequence.append(step)
                        else:
                            issue = {
                                "type": "invalid_sequence_step",
                                "severity": "medium",
                                "description": "Sequence step must be string"
                            }
                            validation_issues.append(issue)
                            
                    valid_structure["sequence"] = valid_sequence
                    
                # Extract dependencies with validation
                if "dependencies" in structure:
                    valid_dependencies = []
                    for dep in structure["dependencies"]:
                        if isinstance(dep, str):
                            valid_dependencies.append(dep)
                        else:
                            issue = {
                                "type": "invalid_dependency",
                                "severity": "medium",
                                "description": "Dependency must be string"
                            }
                            validation_issues.append(issue)
                            
                    valid_structure["dependencies"] = valid_dependencies
                    
                # Extract domain factors with validation
                if "domain_factors" in structure:
                    valid_factors = {}
                    for key, value in structure["domain_factors"].items():
                        if isinstance(key, str) and isinstance(value, (str, int, float, bool)):
                            valid_factors[key] = value
                        else:
                            issue = {
                                "type": "invalid_domain_factor",
                                "severity": "low",
                                "description": "Domain factor has invalid format"
                            }
                            validation_issues.append(issue)
                            
                    valid_structure["domain_factors"] = valid_factors
                    
                # Extract quality factors with validation
                if "quality_factors" in structure:
                    valid_quality = []
                    for factor in structure["quality_factors"]:
                        if isinstance(factor, dict):
                            valid_factor = {
                                "factor": str(factor.get("factor", "")),
                                "weight": float(factor.get("weight", 0.5))
                            }
                            valid_quality.append(valid_factor)
                        else:
                            issue = {
                                "type": "invalid_quality_factor",
                                "severity": "low",
                                "description": "Quality factor has invalid format"
                            }
                            validation_issues.append(issue)
                            
                    valid_structure["quality_factors"] = valid_quality
                    
            # Track validation patterns
            for issue in validation_issues:
                pattern = ResponseValidationPattern(
                    type=issue["type"],
                    description=issue["description"],
                    severity=issue["severity"],
                    response_type="structure",
                    structure_type=list(structure.keys())[0] if structure else None,
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    metadata={
                        "domain": self.domain
                    }
                )
                self.validation_tracker.add_issue(pattern.dict())
                
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                if validation_issues:
                    logger.warning(f"Structure validation issues: {validation_issues}")
                    
            return valid_structure
            
        except Exception as e:
            error_msg = f"Error extracting structure: {str(e)}"
            logger.error(error_msg)
            
            if debug_flags and await debug_flags.is_debug_enabled('log_validation'):
                logger.error(error_msg)
                
            return {}
        
    def _calculate_confidence(
        self,
        components: List[Dict],
        structure: Dict,
        validation_result: ValidationResult
    ) -> float:
        """Calculate overall response analysis confidence with validation."""
        if not components:
            return 0.0
            
        # Base confidence from component confidences
        component_conf = sum(c.get("confidence", 0.5) for c in components) / len(components)
        
        # Structure confidence factors
        structure_conf = 0.0
        structure_weight = 0.0
        
        # Similar responses boost confidence
        if "similar_responses" in structure:
            resp_count = len(structure["similar_responses"])
            resp_conf = min(1.0, resp_count * 0.2)  # Cap at 1.0
            structure_conf += resp_conf
            structure_weight += 1
            
        # Sequence boosts confidence
        if "sequence" in structure:
            seq_count = len(structure["sequence"])
            seq_conf = min(1.0, seq_count * 0.15)  # Cap at 1.0
            structure_conf += seq_conf
            structure_weight += 1
            
        # Dependencies boost confidence
        if "dependencies" in structure:
            dep_count = len(structure["dependencies"])
            dep_conf = min(1.0, dep_count * 0.1)  # Cap at 1.0
            structure_conf += dep_conf
            structure_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in structure:
            domain_conf = min(1.0, len(structure["domain_factors"]) * 0.1)
            structure_conf += domain_conf
            structure_weight += 1
            
        # Quality factors boost confidence
        if "quality_factors" in structure:
            quality_conf = min(1.0, len(structure["quality_factors"]) * 0.15)
            structure_conf += quality_conf
            structure_weight += 1
            
        # Calculate final structure confidence
        if structure_weight > 0:
            structure_conf = structure_conf / structure_weight
            
            # Validation impact
            validation_impact = 0.0
            if validation_result:
                severity_weights = {
                    "low": 0.1,
                    "medium": 0.3,
                    "high": 0.5
                }
                
                total_impact = sum(
                    severity_weights.get(i.get("severity", "medium"), 0.3)
                    for i in validation_result.issues
                )
                validation_impact = total_impact / len(validation_result.issues) if validation_result.issues else 0.0
                
            # Weighted combination with validation impact
            base_conf = (0.6 * component_conf) + (0.4 * structure_conf)
            return max(0.0, base_conf - validation_impact)
        else:
            return component_conf
