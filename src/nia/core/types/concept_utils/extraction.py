"""Concept extraction utilities."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .validation import validate_concept_structure

logger = logging.getLogger(__name__)

def extract_concepts_from_response(data: Dict) -> List[Dict]:
    """Extract concepts from response data structure."""
    concepts = []
    start_time = datetime.now()
    extraction_log = []

    def log_extraction(source: str, success: bool, error: Optional[str] = None, concept: Optional[Dict] = None):
        """Log concept extraction attempt."""
        duration = (datetime.now() - start_time).total_seconds()
        entry = {
            "source": source,
            "success": success,
            "duration": duration
        }
        if error:
            entry["error"] = error
        if concept:
            entry["concept_name"] = concept.get("name", "unknown")
        extraction_log.append(entry)

    def extract_from_tasks(tasks: List[Dict]) -> List[Dict]:
        """Extract concepts from task data."""
        task_concepts = []
        for i, task in enumerate(tasks):
            try:
                concept = {
                    "name": task.get("name", ""),
                    "type": "task",
                    "description": task.get("description", ""),
                    "validation": {
                        "confidence": 1.0 if task.get("status") == "completed" else 0.5
                    }
                }
                if "dependencies" in task:
                    concept["related"] = task["dependencies"]
                validated = validate_concept_structure(concept)
                task_concepts.append(validated)
                log_extraction(f"task[{i}]", True, concept=validated)
            except ValueError as e:
                log_extraction(f"task[{i}]", False, str(e))
        return task_concepts

    if "concepts" in data:
        if isinstance(data["concepts"], list):
            for i, concept in enumerate(data["concepts"]):
                if isinstance(concept, dict):
                    try:
                        validated = validate_concept_structure(concept)
                        concepts.append(validated)
                        log_extraction(f"concepts_array[{i}]", True, concept=validated)
                    except ValueError as e:
                        log_extraction(f"concepts_array[{i}]", False, str(e))
                        logger.warning(f"Invalid concept in array at index {i}: {str(e)}")
                else:
                    log_extraction(f"concepts_array[{i}]", False, "Not a dictionary")
        else:
            log_extraction("concepts_array", False, "Not a list")
            logger.warning("'concepts' field is not a list")

    if "tasks" in data and isinstance(data["tasks"], list):
        try:
            task_concepts = extract_from_tasks(data["tasks"])
            concepts.extend(task_concepts)
            log_extraction("tasks_array", True, concept={"name": f"{len(task_concepts)} tasks"})
        except Exception as e:
            log_extraction("tasks_array", False, str(e))
            logger.warning(f"Failed to extract concepts from tasks: {str(e)}")

    for field in ["response", "key_points", "implications", "reasoning"]:
        if field in data:
            try:
                if isinstance(data[field], dict):
                    validated = validate_concept_structure(data[field])
                    concepts.append(validated)
                    log_extraction(f"{field}_field", True, concept=validated)
                elif isinstance(data[field], list):
                    for i, item in enumerate(data[field]):
                        if isinstance(item, str):
                            concept = {
                                "name": f"{field}_{i}",
                                "type": field,
                                "description": item
                            }
                            validated = validate_concept_structure(concept)
                            concepts.append(validated)
                            log_extraction(f"{field}_list[{i}]", True, concept=validated)
            except ValueError as e:
                log_extraction(field, False, str(e))

    if all(key in data for key in ["name", "type", "description"]):
        try:
            validated = validate_concept_structure(data)
            concepts.append(validated)
            log_extraction("root_level", True, concept=validated)
        except ValueError as e:
            log_extraction("root_level", False, str(e))

    if "metadata" in data and isinstance(data["metadata"], dict):
        try:
            metadata = data["metadata"]
            concept = {
                "name": "metadata",
                "type": "metadata",
                "description": f"Total tasks: {metadata.get('total_tasks', 0)}, "
                             f"Estimated time: {metadata.get('estimated_total_time', 0)} minutes"
            }
            validated = validate_concept_structure(concept)
            concepts.append(validated)
            log_extraction("metadata", True, concept=validated)
        except ValueError as e:
            log_extraction("metadata", False, str(e))

    if not concepts:
        logger.error("No valid concepts extracted. Extraction attempts:")
        for entry in extraction_log:
            logger.error(f"  Source: {entry['source']}")
            logger.error(f"  Success: {entry['success']}")
            logger.error(f"  Duration: {entry['duration']:.3f}s")
            if "error" in entry:
                logger.error(f"  Error: {entry['error']}")
            if "concept_name" in entry:
                logger.error(f"  Concept: {entry['concept_name']}")
            logger.error("---")
    else:
        logger.info(f"Successfully extracted {len(concepts)} concepts")
        for concept in concepts:
            logger.info(f"  - {concept['name']} ({concept['type']})")

    return concepts
