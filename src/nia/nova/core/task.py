"""Nova's core task analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskResult:
    """Container for task analysis results."""
    
    def __init__(
        self,
        tasks: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        dependencies: Optional[Dict] = None
    ):
        self.tasks = tasks
        self.confidence = confidence
        self.metadata = metadata or {}
        self.dependencies = dependencies or {}
        self.timestamp = datetime.now().isoformat()

class TaskAgent:
    """Core task analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_tasks(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> TaskResult:
        """Analyze tasks with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata
                    },
                    template="task_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content)
                
            # Extract and validate components
            tasks = self._extract_tasks(analysis)
            dependencies = self._extract_dependencies(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(tasks, dependencies)
            
            return TaskResult(
                tasks=tasks,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                dependencies=dependencies
            )
            
        except Exception as e:
            logger.error(f"Task analysis error: {str(e)}")
            return TaskResult(
                tasks=[],
                confidence=0.0,
                metadata={"error": str(e)},
                dependencies={"error": str(e)}
            )
            
    def _basic_analysis(self, content: Dict[str, Any]) -> Dict:
        """Basic task analysis without LLM."""
        tasks = []
        dependencies = {}
        
        # Basic task extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic task indicators and their confidences
        task_indicators = {
            "need to": 0.8,
            "must": 0.9,
            "should": 0.7,
            "will": 0.6,
            "going to": 0.6,
            "plan to": 0.7,
            "required to": 0.8,
            "have to": 0.8
        }
        
        # Check for task indicators
        for indicator, base_confidence in task_indicators.items():
            if indicator in text:
                # Extract the task statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                task_statement = text[start_idx:end_idx].strip()
                if task_statement:
                    tasks.append({
                        "statement": task_statement,
                        "type": "inferred_task",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Basic dependency extraction
        if "after" in text:
            start_idx = text.find("after") + len("after")
            end_idx = text.find(".", start_idx)
            if end_idx == -1:
                end_idx = len(text)
                
            dependency = text[start_idx:end_idx].strip()
            if dependency:
                dependencies["sequential"] = [dependency]
                
        return {
            "tasks": tasks,
            "dependencies": dependencies
        }
        
    def _extract_tasks(self, analysis: Dict) -> List[Dict]:
        """Extract and validate tasks."""
        tasks = analysis.get("tasks", [])
        valid_tasks = []
        
        for task in tasks:
            if isinstance(task, dict) and "statement" in task:
                valid_task = {
                    "statement": str(task["statement"]),
                    "type": str(task.get("type", "task")),
                    "confidence": float(task.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in task:
                    valid_task["description"] = str(task["description"])
                if "source" in task:
                    valid_task["source"] = str(task["source"])
                if "domain_relevance" in task:
                    valid_task["domain_relevance"] = float(task["domain_relevance"])
                if "priority" in task:
                    valid_task["priority"] = float(task["priority"])
                if "complexity" in task:
                    valid_task["complexity"] = float(task["complexity"])
                if "status" in task:
                    valid_task["status"] = str(task["status"])
                    
                valid_tasks.append(valid_task)
                
        return valid_tasks
        
    def _extract_dependencies(self, analysis: Dict) -> Dict:
        """Extract and validate dependencies."""
        dependencies = analysis.get("dependencies", {})
        valid_dependencies = {}
        
        if isinstance(dependencies, dict):
            # Extract relevant dependency fields
            if "sequential" in dependencies:
                valid_dependencies["sequential"] = [
                    str(d) for d in dependencies["sequential"]
                    if isinstance(d, str)
                ]
                
            if "parallel" in dependencies:
                valid_dependencies["parallel"] = [
                    str(d) for d in dependencies["parallel"]
                    if isinstance(d, str)
                ]
                
            if "blockers" in dependencies:
                valid_dependencies["blockers"] = [
                    str(b) for b in dependencies["blockers"]
                    if isinstance(b, str)
                ]
                
            if "domain_factors" in dependencies:
                valid_dependencies["domain_factors"] = {
                    str(k): str(v)
                    for k, v in dependencies["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "priority_factors" in dependencies:
                valid_dependencies["priority_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in dependencies.get("priority_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_dependencies
        
    def _calculate_confidence(
        self,
        tasks: List[Dict],
        dependencies: Dict
    ) -> float:
        """Calculate overall task analysis confidence."""
        if not tasks:
            return 0.0
            
        # Base confidence from task confidences
        task_conf = sum(t.get("confidence", 0.5) for t in tasks) / len(tasks)
        
        # Dependency confidence factors
        dependency_conf = 0.0
        dependency_weight = 0.0
        
        # Sequential dependencies boost confidence
        if "sequential" in dependencies:
            seq_count = len(dependencies["sequential"])
            seq_conf = min(1.0, seq_count * 0.2)  # Cap at 1.0
            dependency_conf += seq_conf
            dependency_weight += 1
            
        # Parallel tasks provide context
        if "parallel" in dependencies:
            para_count = len(dependencies["parallel"])
            para_conf = min(1.0, para_count * 0.15)  # Cap at 1.0
            dependency_conf += para_conf
            dependency_weight += 1
            
        # Blockers indicate understanding
        if "blockers" in dependencies:
            block_count = len(dependencies["blockers"])
            block_conf = min(1.0, block_count * 0.1)  # Cap at 1.0
            dependency_conf += block_conf
            dependency_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in dependencies:
            domain_conf = min(1.0, len(dependencies["domain_factors"]) * 0.1)
            dependency_conf += domain_conf
            dependency_weight += 1
            
        # Priority factors boost confidence
        if "priority_factors" in dependencies:
            priority_conf = min(1.0, len(dependencies["priority_factors"]) * 0.15)
            dependency_conf += priority_conf
            dependency_weight += 1
            
        # Calculate final dependency confidence
        if dependency_weight > 0:
            dependency_conf = dependency_conf / dependency_weight
            
            # Weighted combination of task and dependency confidence
            return (0.6 * task_conf) + (0.4 * dependency_conf)
        else:
            return task_conf
