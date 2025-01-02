"""Nova's core schema functionality."""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, ValidationError, create_model

logger = logging.getLogger(__name__)

class SchemaResult:
    """Container for schema operation results."""
    
    def __init__(
        self,
        is_valid: bool,
        schema: Dict,
        validations: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None
    ):
        self.is_valid = is_valid
        self.schema = schema
        self.validations = validations
        self.confidence = confidence
        self.metadata = metadata or {}
        self.issues = issues or []
        self.timestamp = datetime.now().isoformat()

class SchemaAgent:
    """Core schema functionality for Nova's ecosystem."""
    
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
        
    async def analyze_schema(
        self,
        content: Dict[str, Any],
        schema_type: str,
        metadata: Optional[Dict] = None
    ) -> SchemaResult:
        """Analyze schema with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get similar schemas if vector store available
            similar_schemas = []
            if self.vector_store:
                similar_schemas = await self._get_similar_schemas(
                    content,
                    schema_type
                )
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "schema_type": schema_type,
                        "metadata": metadata,
                        "similar_schemas": similar_schemas
                    },
                    template="schema_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(
                    content,
                    schema_type,
                    similar_schemas
                )
                
            # Extract and validate components
            schema = self._extract_schema(analysis)
            validations = self._extract_validations(analysis)
            issues = self._extract_issues(analysis)
            
            # Calculate confidence and validity
            confidence = self._calculate_confidence(schema, validations, issues)
            is_valid = self._determine_validity(schema, validations, issues, confidence)
            
            return SchemaResult(
                is_valid=is_valid,
                schema=schema,
                validations=validations,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "schema_type": schema_type,
                    "content_type": content.get("type", "unknown"),
                    "source": metadata.get("source", "unknown")
                },
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Schema analysis error: {str(e)}")
            return SchemaResult(
                is_valid=False,
                schema={},
                validations=[],
                confidence=0.0,
                metadata={"error": str(e)},
                issues=[{"type": "error", "description": str(e)}]
            )
            
    async def _get_similar_schemas(
        self,
        content: Dict[str, Any],
        schema_type: str
    ) -> List[Dict]:
        """Get similar schemas from vector store."""
        try:
            if "content" in content:
                results = await self.vector_store.search(
                    content["content"],
                    limit=5,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "schema",
                        "schema_type": schema_type
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting similar schemas: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        content: Dict[str, Any],
        schema_type: str,
        similar_schemas: List[Dict]
    ) -> Dict:
        """Basic schema analysis without LLM."""
        schema = {}
        validations = []
        issues = []
        
        # Basic schema rules
        schema_rules = {
            "data": {
                "has_fields": 0.8,
                "has_types": 0.7,
                "has_constraints": 0.6
            },
            "api": {
                "has_endpoints": 0.8,
                "has_methods": 0.7,
                "has_responses": 0.7
            },
            "model": {
                "has_attributes": 0.8,
                "has_relations": 0.7,
                "has_validations": 0.6
            }
        }
        
        # Check schema type rules
        if schema_type in schema_rules:
            type_rules = schema_rules[schema_type]
            
            # Extract basic schema structure
            if isinstance(content, dict):
                schema = {
                    "type": schema_type,
                    "fields": {},
                    "constraints": {},
                    "metadata": {}
                }
                
                # Add fields from content
                for key, value in content.items():
                    if isinstance(value, dict) and "type" in value:
                        schema["fields"][key] = {
                            "type": value["type"],
                            "required": value.get("required", False),
                            "constraints": value.get("constraints", {})
                        }
                        
                # Add basic validations
                for rule, confidence in type_rules.items():
                    if self._check_rule(rule, content):
                        validations.append({
                            "rule": rule,
                            "passed": True,
                            "confidence": confidence
                        })
                    else:
                        issues.append({
                            "type": f"missing_{rule}",
                            "severity": "medium",
                            "description": f"Schema is missing {rule}"
                        })
                        
            else:
                issues.append({
                    "type": "invalid_format",
                    "severity": "high",
                    "description": "Content must be a dictionary"
                })
                
            # Add similar schemas as reference
            if similar_schemas:
                schema["similar_schemas"] = [
                    {
                        "content": s.get("content", {}).get("content", ""),
                        "similarity": s.get("similarity", 0.0),
                        "timestamp": s.get("timestamp", "")
                    }
                    for s in similar_schemas
                ]
                
        return {
            "schema": schema,
            "validations": validations,
            "issues": issues
        }
        
    def _check_rule(self, rule: str, content: Dict[str, Any]) -> bool:
        """Check if content satisfies a schema rule."""
        if rule == "has_fields":
            return bool(content.get("fields", {}))
        elif rule == "has_types":
            return all("type" in f for f in content.get("fields", {}).values())
        elif rule == "has_constraints":
            return any("constraints" in f for f in content.get("fields", {}).values())
        elif rule == "has_endpoints":
            return bool(content.get("endpoints", {}))
        elif rule == "has_methods":
            return any("methods" in e for e in content.get("endpoints", {}).values())
        elif rule == "has_responses":
            return any("responses" in e for e in content.get("endpoints", {}).values())
        elif rule == "has_attributes":
            return bool(content.get("attributes", {}))
        elif rule == "has_relations":
            return bool(content.get("relations", {}))
        elif rule == "has_validations":
            return bool(content.get("validations", {}))
        return False
        
    def _extract_schema(self, analysis: Dict) -> Dict:
        """Extract and validate schema."""
        schema = analysis.get("schema", {})
        valid_schema = {}
        
        if isinstance(schema, dict):
            # Extract core schema fields
            valid_schema["type"] = str(schema.get("type", "unknown"))
            valid_schema["fields"] = {}
            
            # Extract and validate fields
            fields = schema.get("fields", {})
            if isinstance(fields, dict):
                for name, field in fields.items():
                    if isinstance(field, dict):
                        valid_field = {
                            "type": str(field.get("type", "string")),
                            "required": bool(field.get("required", False))
                        }
                        
                        # Add optional field attributes
                        if "description" in field:
                            valid_field["description"] = str(field["description"])
                        if "default" in field:
                            valid_field["default"] = field["default"]
                        if "constraints" in field:
                            valid_field["constraints"] = field["constraints"]
                            
                        valid_schema["fields"][str(name)] = valid_field
                        
            # Add optional schema sections
            if "constraints" in schema:
                valid_schema["constraints"] = schema["constraints"]
            if "metadata" in schema:
                valid_schema["metadata"] = schema["metadata"]
            if "similar_schemas" in schema:
                valid_schema["similar_schemas"] = schema["similar_schemas"]
                
        return valid_schema
        
    def _extract_validations(self, analysis: Dict) -> List[Dict]:
        """Extract and validate schema validations."""
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
                    
                valid_validations.append(valid_validation)
                
        return valid_validations
        
    def _extract_issues(self, analysis: Dict) -> List[Dict]:
        """Extract and validate schema issues."""
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
        schema: Dict,
        validations: List[Dict],
        issues: List[Dict]
    ) -> float:
        """Calculate overall schema confidence."""
        if not schema or not validations:
            return 0.0
            
        # Schema completeness confidence
        schema_conf = 0.0
        if schema.get("fields"):
            field_count = len(schema["fields"])
            field_conf = min(1.0, field_count * 0.1)  # Cap at 1.0
            schema_conf += field_conf
            
        if schema.get("constraints"):
            constraint_count = len(schema["constraints"])
            constraint_conf = min(1.0, constraint_count * 0.1)
            schema_conf += constraint_conf
            
        schema_conf = schema_conf / 2 if schema_conf > 0 else 0.0
        
        # Validation confidence
        validation_conf = sum(v.get("confidence", 0.5) for v in validations) / len(validations)
        
        # Issue impact
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
        base_conf = (schema_conf + validation_conf) / 2
        return max(0.0, base_conf - issue_impact)
        
    def _determine_validity(
        self,
        schema: Dict,
        validations: List[Dict],
        issues: List[Dict],
        confidence: float
    ) -> bool:
        """Determine overall schema validity."""
        if not schema or not validations:
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
        
        # Check schema completeness
        has_required_fields = bool(schema.get("fields"))
        has_valid_types = all(
            "type" in f for f in schema.get("fields", {}).values()
        )
        
        # Consider all factors
        return (
            validation_ratio >= 0.7 and
            confidence >= 0.6 and
            has_required_fields and
            has_valid_types
        )
        
    async def generate_pydantic_model(
        self,
        schema: Dict[str, Any],
        model_name: str = "DynamicModel"
    ) -> type[BaseModel]:
        """Generate a Pydantic model from schema definition."""
        try:
            # Extract field definitions
            fields = {}
            for name, field in schema.get("fields", {}).items():
                field_type = self._get_python_type(field.get("type", "string"))
                field_default = field.get("default", ...)
                
                # Add field with type and default
                fields[name] = (field_type, field_default)
                
            # Create dynamic model
            model = create_model(
                model_name,
                **fields
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error generating Pydantic model: {str(e)}")
            raise
            
    def _get_python_type(self, schema_type: str) -> type:
        """Convert schema type to Python type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping.get(schema_type.lower(), str)
