"""Interface for LLM interactions."""

import json
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from .memory_types import AgentResponse

if TYPE_CHECKING:
    from .agents.parsing_agent import ParsingAgent
    from .neo4j_store import Neo4jMemoryStore
    from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(self, use_mock: bool = False):
        """Initialize LLM interface.
        
        Args:
            use_mock: Whether to use mock responses (for testing)
        """
        self.parser = None  # Will be set after initialization
        self.use_mock = use_mock
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
    def initialize_parser(
        self,
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ) -> None:
        """Initialize parsing agent.
        
        This method creates a new ParsingAgent instance and sets it as the parser
        for this LLM interface. The parser is used to extract structured content
        from LLM responses.
        
        Args:
            store: Neo4j store for concept storage
            vector_store: Vector store for embeddings
        """
        from .agents.parsing_agent import ParsingAgent
        self.parser = ParsingAgent(self, store, vector_store)
        
    def set_parser(self, parser: 'ParsingAgent'):
        """Set parsing agent."""
        self.parser = parser
        
    def _get_mock_concept(self, agent_type: str) -> Dict[str, Any]:
        """Get mock concept based on agent type."""
        concepts = {
            "belief": {
                "name": "Knowledge Structure",
                "type": "belief",
                "description": "Understanding of knowledge organization",
                "related": ["Learning", "Memory"]
            },
            "emotion": {
                "name": "Emotional Response",
                "type": "emotion",
                "description": "Pattern of emotional reaction with high intensity and positive valence",
                "related": ["Affect", "Behavior", "Emotional Regulation", "Mood"]
            },
            "desire": {
                "name": "Achievement Drive",
                "type": "goal",
                "description": "Motivation to accomplish objectives",
                "related": ["Motivation", "Success"]
            },
            "reflection": {
                "name": "Learning Pattern",
                "type": "pattern",
                "description": "Recurring learning behavior",
                "related": ["Growth", "Development"]
            },
            "research": {
                "name": "Information Source",
                "type": "source",
                "description": "Origin of knowledge",
                "related": ["Data", "Evidence"]
            },
            "task": {
                "name": "Task Structure",
                "type": "task",
                "description": "Organization of task steps",
                "related": ["Planning", "Execution"]
            },
            "dialogue": {
                "name": "Dialogue Flow",
                "type": "interaction",
                "description": "Pattern of conversation",
                "related": ["Communication", "Exchange"]
            },
            "context": {
                "name": "Context Frame",
                "type": "context",
                "description": "Environmental understanding",
                "related": ["Situation", "Environment"]
            },
            "parsing": {
                "name": "Parse Structure",
                "type": "pattern",
                "description": "Information organization",
                "related": ["Analysis", "Structure"]
            },
            "meta": {
                "name": "Meta Pattern",
                "type": "synthesis",
                "description": "High-level integration",
                "related": ["Coordination", "Integration"]
            }
        }
        return concepts.get(agent_type, {
            "name": "Generic Concept",
            "type": "pattern",
            "description": "Basic pattern or concept",
            "related": []
        })
        
    async def _make_llm_request(self, messages: List[Dict[str, str]]) -> str:
        """Make request to LMStudio API.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Response text from LLM
        """
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "model": "llama-3.2-3b-instruct"
                }
                self.logger.debug(f"LLM Request: {json.dumps(request_data, indent=2)}")
                
                try:
                    # Increased timeout and added retry logic for LMStudio
                    for retry in range(3):
                        try:
                            async with session.post(
                                "http://localhost:1234/v1/chat/completions",
                                json=request_data,
                                timeout=30.0,  # Increased timeout for LMStudio
                                headers={"Content-Type": "application/json"}
                            ) as response:
                                # Check response status
                                if response.status != 200:
                                    error_text = await response.text()
                                    self.logger.error(f"LMStudio error (status {response.status}): {error_text}")
                                    if retry < 2:  # Try again if not last attempt
                                        self.logger.info(f"Retrying LMStudio request (attempt {retry + 2}/3)")
                                        continue
                                    raise Exception(f"LMStudio API error (status {response.status}): {error_text}")

                                result = await response.json()
                                self.logger.debug(f"LLM API Response: {json.dumps(result, indent=2)}")
                                
                                if "error" in result:
                                    raise Exception(f"LMStudio API error: {result['error']}")
                                    
                                if "choices" not in result or not result["choices"]:
                                    raise Exception("No choices in LMStudio response")
                                
                                content = result["choices"][0]["message"]["content"]
                                self.logger.debug(f"Raw LLM Content: {content}")
                                
                                # Try to parse as JSON first
                                try:
                                    # Clean up common formatting issues
                                    content = content.strip()
                                    if content.startswith("```json"):
                                        content = content[7:]
                                    if content.endswith("```"):
                                        content = content[:-3]
                                    content = content.strip()
                                    
                                    parsed = json.loads(content)
                                    
                                    # Ensure base structure
                                    if not isinstance(parsed, dict):
                                        raise ValueError("Response must be a JSON object")
                                        
                                    # Validate and fix required fields
                                    required_fields = {
                                        "response": str,
                                        "concepts": list,
                                        "key_points": list,
                                        "implications": list,
                                        "uncertainties": list,
                                        "reasoning": list
                                    }
                                    
                                    # Add missing fields with defaults
                                    for field, field_type in required_fields.items():
                                        if field not in parsed:
                                            if field_type == str:
                                                parsed[field] = ""
                                            else:
                                                parsed[field] = []
                                                
                                    # Validate concepts
                                    if parsed["concepts"]:
                                        validated_concepts = []
                                        for concept in parsed["concepts"]:
                                            if not isinstance(concept, dict):
                                                continue
                                                
                                            # Ensure required concept fields
                                            concept_template = {
                                                "name": str(concept.get("name", "Unnamed Concept")),
                                                "type": str(concept.get("type", "concept")),
                                                "description": str(concept.get("description", "")),
                                                "related": list(concept.get("related", [])),
                                                "validation": {
                                                    "confidence": float(concept.get("validation", {}).get("confidence", 0.5)),
                                                    "supported_by": list(concept.get("validation", {}).get("supported_by", [])),
                                                    "contradicted_by": list(concept.get("validation", {}).get("contradicted_by", [])),
                                                    "needs_verification": list(concept.get("validation", {}).get("needs_verification", []))
                                                }
                                            }
                                            validated_concepts.append(concept_template)
                                            
                                        parsed["concepts"] = validated_concepts
                                    
                                    return json.dumps(parsed)
                                    
                                except (json.JSONDecodeError, ValueError) as e:
                                    self.logger.warning(f"Error parsing LLM response: {str(e)}")
                                    self.logger.warning("Attempting to fix response format")
                                    
                                    # More robust JSON extraction
                                    import re
                                    
                                    # Clean up common JSON formatting issues
                                    content = content.replace('\n', ' ').strip()
                                    
                                    # Fix JSON structure
                                    content = re.sub(r'}\s*{', '},{', content)  # Fix adjacent objects
                                    content = re.sub(r']\s*{', '],{', content)  # Fix array followed by object
                                    content = re.sub(r'}\s*\[', '},[', content)  # Fix object followed by array
                                    content = re.sub(r',\s*}', '}', content)  # Remove trailing commas
                                    content = re.sub(r',\s*]', ']', content)  # Remove trailing commas in arrays
                                    
                                    # Fix property names and values
                                    content = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)  # Quote property names
                                    content = re.sub(r':\s*"([^"]*)"(?=\s*[},])', r':"\1"', content)  # Fix string values
                                    content = re.sub(r':\s*([^",\s\]}]+)(?=\s*[},])', r':"\1"', content)  # Quote unquoted values
                                    content = re.sub(r':\s*(\d+\.?\d*)\s*(?=[,}])', r':\1', content)  # Preserve numeric values
                                    content = re.sub(r':\s*(true|false)\s*(?=[,}])', r':\1', content)  # Preserve boolean values
                                    
                                    # Normalize whitespace and structure
                                    content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
                                    content = re.sub(r'"\s*,\s*"', '","', content)  # Fix array string spacing
                                    content = re.sub(r'\[\s*"', '["', content)  # Fix array start spacing
                                    content = re.sub(r'"\s*\]', '"]', content)  # Fix array end spacing
                                    content = re.sub(r',\s*([}\]])', r'\1', content)  # Remove trailing commas
                                    
                                    # Ensure proper JSON structure
                                    if not content.startswith('{'):
                                        content = '{' + content
                                    if not content.endswith('}'):
                                        content = content + '}'
                                    
                                    try:
                                        parsed = json.loads(content)
                                        if isinstance(parsed, dict) and any(key in parsed for key in ["response", "concepts"]):
                                            return json.dumps(parsed)
                                    except json.JSONDecodeError:
                                        self.logger.warning("Could not parse JSON directly, attempting extraction")
                                        
                                        # Try to find JSON-like content
                                        json_pattern = r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\})'
                                        matches = list(re.finditer(json_pattern, content))
                                        
                                        for match in matches:
                                            try:
                                                potential_json = match.group(0)
                                                parsed = json.loads(potential_json)
                                                if isinstance(parsed, dict) and any(key in parsed for key in ["response", "concepts"]):
                                                    return json.dumps(parsed)
                                            except json.JSONDecodeError:
                                                continue
                                    
                                    self.logger.warning("Could not extract valid JSON, using fallback")
                                    
                                    # Wrap in proper JSON structure
                                    return json.dumps({
                                        "response": content,
                                        "concepts": [{
                                            "name": "LLM Response",
                                            "type": "belief",
                                            "description": content,
                                            "related": [],
                                            "validation": {
                                                "confidence": 0.5,
                                                "supported_by": [],
                                                "contradicted_by": [],
                                                "needs_verification": ["Response format needs validation"]
                                            }
                                        }],
                                        "key_points": ["LLM provided response"],
                                        "implications": ["Response needs proper structuring"],
                                        "uncertainties": ["Response format", "Content structure"],
                                        "reasoning": ["Attempted to parse LLM output", 
                                                    "Applied fallback formatting"]
                                    })
                                
                        except aiohttp.ClientError as e:
                            if retry < 2:  # Try again if not last attempt
                                self.logger.warning(f"LMStudio connection error (attempt {retry + 1}/3): {str(e)}")
                                continue
                            raise  # Re-raise if all retries failed
                            
                except aiohttp.ClientError as e:
                    self.logger.error(f"LMStudio connection error: {str(e)}. Is LMStudio running?")
                    return json.dumps({
                        "response": "LMStudio is not running or not accessible",
                        "concepts": [{
                            "name": "LMStudio Error",
                            "type": "error",
                            "description": "Could not connect to LMStudio API",
                            "related": [],
                            "validation": {
                                "confidence": 0.0,
                                "supported_by": [],
                                "contradicted_by": [],
                                "needs_verification": []
                            }
                        }],
                        "key_points": ["LMStudio connection failed"],
                        "implications": ["System cannot process requests"],
                        "uncertainties": ["LMStudio availability"],
                        "reasoning": ["Connection attempt failed"]
                    })
                    
        except Exception as e:
            self.logger.error(f"Error making LLM request: {str(e)}")
            return json.dumps({
                "response": f"Error: {str(e)}",
                "concepts": [],
                "key_points": [],
                "implications": [],
                "uncertainties": [],
                "reasoning": []
            })
    
    async def get_completion(self, prompt: str, agent_type: str = "default") -> str:
        """Get LLM completion.
        
        Args:
            prompt: Prompt for LLM
            agent_type: Type of agent making request
            
        Returns:
            LLM completion text
        """
        try:
            if self.use_mock:
                # Use mock response for testing
                concept = self._get_mock_concept(agent_type)
                # Get mock concept and ensure it has required fields
                mock_concept = {
                    "name": concept["name"],
                    "type": concept["type"],
                    "description": concept["description"],
                    "related": concept["related"] if concept["related"] else ["Default Related"],
                    "validation": {
                        "confidence": 0.8,
                        "supported_by": ["Evidence 1"],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                }

                # For emotion concepts, ensure related terms exist
                if mock_concept["type"] == "emotion" and not mock_concept["related"]:
                    mock_concept["related"] = ["Affect", "Behavior", "Emotional Regulation", "Mood"]
                
                if "consolidation" in str(prompt).lower():
                    mock_concept["type"] = "consolidation"
                    mock_concept["name"] = "Memory Pattern"
                    mock_concept["description"] = "Consolidated memory pattern"
                
                response = {
                    "response": "Mock LLM response for " + agent_type,
                    "concepts": [mock_concept],
                    "key_points": ["Mock key point"],
                    "implications": ["Mock implication"],
                    "uncertainties": ["Mock uncertainty"],
                    "reasoning": ["Mock reasoning step"]
                }
                
                return json.dumps(response, ensure_ascii=False)
            else:
                # Make real LLM request
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are an AI agent specialized in {agent_type} analysis. Your response MUST be a single valid JSON object with NO additional text or formatting.

REQUIRED FORMAT:
{{
    "response": "Your detailed analysis from a {agent_type} perspective",
    "concepts": [
        {{
            "name": "Concept name (required)",
            "type": "{agent_type}",
            "description": "Clear description (required)",
            "related": ["Term1", "Term2"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["Evidence1"],
                "contradicted_by": [],
                "needs_verification": []
            }}
        }}
    ],
    "key_points": ["Key insight 1"],
    "implications": ["Implication 1"],
    "uncertainties": ["Uncertainty 1"],
    "reasoning": ["Reasoning step 1"]
}}

CRITICAL RULES:
1. Response MUST be ONLY the JSON object - no markdown, no code blocks
2. Use DOUBLE QUOTES for ALL strings and property names
3. NO trailing commas after last item in arrays/objects
4. ALL property names must match exactly as shown
5. ALL arrays and objects must be properly closed
6. Concepts array MUST contain at least one concept
7. ALL fields shown are required - do not omit any
8. ALL arrays must contain at least one item
9. Validation object is required for each concept with exact structure shown
10. Numbers must be raw numeric values without quotes (e.g. confidence: 0.8 not "0.8")
11. Boolean values must be raw true/false without quotes
12. Arrays must use square brackets even for single items
13. Validation confidence must be between 0.0 and 1.0"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                return await self._make_llm_request(messages)
            
        except Exception as e:
            self.logger.error(f"Error getting LLM completion: {str(e)}")
            return "{}"
    
    async def get_structured_completion(
        self,
        prompt: str,
        agent_type: str = "default",
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Get structured LLM completion.
        
        Args:
            prompt: Prompt for LLM
            agent_type: Type of agent making request
            metadata: Optional metadata
            
        Returns:
            Structured agent response
        """
        try:
            # Get raw completion
            completion = await self.get_completion(prompt, agent_type)
            
            # Parse through parsing agent
            if self.parser:
                response = await self.parser.parse_text(completion)
            else:
                # Fallback if parser not set
                self.logger.warning("Parser not set, returning minimal response")
                response = AgentResponse(
                    response=completion,
                    concepts=[],
                    key_points=[],
                    implications=[],
                    uncertainties=[],
                    reasoning=[],
                    perspective=agent_type,
                    confidence=0.5,
                    timestamp=datetime.now()
                )
            
            # Add metadata if provided
            if metadata:
                if not response.metadata:
                    response.metadata = {}
                response.metadata.update(metadata)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting structured completion: {str(e)}")
            return AgentResponse(
                response=f"Error getting structured completion: {str(e)}",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective=agent_type,
                confidence=0.0,
                timestamp=datetime.now()
            )
