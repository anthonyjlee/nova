"""Core validation functionality."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import ValidationError, BaseModel

logger = logging.getLogger(__name__)

class ValidationPattern(BaseModel):
    """Pattern detected during validation."""
    type: str
    description: str
    severity: str = "low"
    frequency: int = 1
    first_seen: str
    last_seen: str
    metadata: Dict[str, Any] = {}

class ValidationResult(BaseModel):
    """Result of validation operation."""
    is_valid: bool
    issues: List[Dict[str, Any]] = []
    patterns: List[ValidationPattern] = []
    metadata: Dict[str, Any] = {}
    timestamp: str = datetime.now().isoformat()

class Message(BaseModel):
    """Base message class for validation."""
    content: str
    thread_id: str
    sender_type: str = "user"
    sender_id: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = {}
    validation: Optional[Dict[str, Any]] = None

class ValidationTracker:
    """Track validation patterns and issues."""
    
    def __init__(self):
        self.patterns = {}  # pattern_key -> ValidationPattern
        
    def add_issue(self, issue: Dict[str, Any]):
        """Add validation issue and update patterns."""
        pattern_key = f"{issue['type']}:{issue['description']}"
        
        if pattern_key in self.patterns:
            pattern = self.patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_seen = datetime.now().isoformat()
            pattern.metadata["last_issue"] = issue
        else:
            now = datetime.now().isoformat()
            self.patterns[pattern_key] = ValidationPattern(
                type=issue["type"],
                description=issue["description"],
                severity=issue.get("severity", "low"),
                first_seen=now,
                last_seen=now,
                metadata={"first_issue": issue}
            )
            
    def get_patterns(self) -> List[ValidationPattern]:
        """Get all tracked validation patterns."""
        return list(self.patterns.values())
        
    def get_critical_patterns(self) -> List[ValidationPattern]:
        """Get patterns with high severity or frequency."""
        return [
            p for p in self.patterns.values()
            if p.severity == "high" or p.frequency > 2
        ]

# Global validation tracker
validation_tracker = ValidationTracker()

async def validate_message(
    data: dict
) -> Optional[Message]:
    """Validate message with debug logging and pattern tracking."""
    try:
        logger.debug(f"Validating message data: {data}")
            
        # Basic schema validation
        message = Message(**data)
        
        # Additional validation rules
        validation_issues = []
        
        # Content validation
        if len(message.content) < 1:
            issue = {
                "type": "content_validation",
                "severity": "high",
                "description": "Message content cannot be empty"
            }
            validation_issues.append(issue)
            validation_tracker.add_issue(issue)
            
        if len(message.content) > 10000:
            issue = {
                "type": "content_validation",
                "severity": "medium", 
                "description": "Message content exceeds maximum length"
            }
            validation_issues.append(issue)
            validation_tracker.add_issue(issue)
            
        # Thread validation
        if not message.thread_id.strip():
            issue = {
                "type": "thread_validation",
                "severity": "high",
                "description": "Thread ID cannot be empty"
            }
            validation_issues.append(issue)
            validation_tracker.add_issue(issue)
            
        # Sender validation
        if not message.sender_id.strip():
            issue = {
                "type": "sender_validation",
                "severity": "high",
                "description": "Sender ID cannot be empty"
            }
            validation_issues.append(issue)
            validation_tracker.add_issue(issue)
            
        # Create validation result
        validation_result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            issues=validation_issues,
            patterns=validation_tracker.get_patterns(),
            metadata={
                "message_type": message.sender_type,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Add validation result to message
        message.validation = validation_result.dict()
        
        logger.debug(f"Validation result: {validation_result.dict()}")
            
        # Log critical patterns
        critical_patterns = validation_tracker.get_critical_patterns()
        if critical_patterns:
            logger.warning(f"Critical validation patterns detected: {critical_patterns}")
                
        # Always raise on validation issues
        if validation_issues:
            raise ValidationError(f"Validation failed: {validation_issues}")
            
        return message
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

async def validate_thread_access(
    thread_id: str,
    user_id: str
) -> ValidationResult:
    """Validate thread access with debug logging and pattern tracking."""
    try:
        logger.debug(f"Validating thread access - thread: {thread_id}, user: {user_id}")
            
        validation_issues = []
        
        # Thread ID validation
        if not thread_id.strip():
            issue = {
                "type": "thread_access",
                "severity": "high",
                "description": "Thread ID cannot be empty"
            }
            validation_issues.append(issue)
            validation_tracker.add_issue(issue)
            
        # User ID validation
        if not user_id.strip():
            issue = {
                "type": "thread_access",
                "severity": "high",
                "description": "User ID cannot be empty"
            }
            validation_issues.append(issue)
            validation_tracker.add_issue(issue)
            
        # TODO: Implement actual access validation
        # For now, create validation result
        validation_result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            issues=validation_issues,
            patterns=validation_tracker.get_patterns(),
            metadata={
                "thread_id": thread_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.debug(f"Thread access validation result: {validation_result.dict()}")
            
        # Log critical patterns
        critical_patterns = validation_tracker.get_critical_patterns()
        if critical_patterns:
            logger.warning(f"Critical validation patterns detected: {critical_patterns}")
                
        return validation_result
        
    except Exception as e:
        logger.error(f"Thread access validation failed: {str(e)}")
        raise
            
        return ValidationResult(
            is_valid=False,
            issues=[{
                "type": "validation_error",
                "severity": "high",
                "description": str(e)
            }],
            metadata={
                "error": str(e),
                "thread_id": thread_id,
                "user_id": user_id
            }
        )

async def validate_schema(
    data: Dict[str, Any],
    schema_type: str
) -> ValidationResult:
    """Validate data against a schema with debug logging and pattern tracking."""
    try:
        logger.debug(f"Validating schema - type: {schema_type}, data: {data}")
            
        validation_issues = []
        
        # TODO: Implement schema validation
        # For now, create validation result
        validation_result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            issues=validation_issues,
            patterns=validation_tracker.get_patterns(),
            metadata={
                "schema_type": schema_type,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.debug(f"Schema validation result: {validation_result.dict()}")
            
        # Log critical patterns
        critical_patterns = validation_tracker.get_critical_patterns()
        if critical_patterns:
            logger.warning(f"Critical validation patterns detected: {critical_patterns}")
                
        return validation_result
        
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        raise
            
        return ValidationResult(
            is_valid=False,
            issues=[{
                "type": "validation_error",
                "severity": "high",
                "description": str(e)
            }],
            metadata={
                "error": str(e),
                "schema_type": schema_type
            }
        )
