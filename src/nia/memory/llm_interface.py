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
                "description": "Pattern of emotional reaction",
                "related": ["Affect", "Behavior"]
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
                    async with session.post(
                        "http://localhost:1234/v1/chat/completions",
                        json=request_data,
                        timeout=10.0,  # Increased timeout for real responses
                        headers={"Content-Type": "application/json"}
                    ) as response:
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
                            parsed = json.loads(content)
                            # Validate required fields
                            required_fields = ["response", "concepts", "key_points", 
                                            "implications", "uncertainties", "reasoning"]
                            missing_fields = [f for f in required_fields if f not in parsed]
                            if missing_fields:
                                raise ValueError(f"Missing required fields: {missing_fields}")
                                
                            # Validate concept structure
                            for concept in parsed["concepts"]:
                                required_concept_fields = ["name", "type", "description", 
                                                        "related", "validation"]
                                missing_concept_fields = [f for f in required_concept_fields 
                                                        if f not in concept]
                                if missing_concept_fields:
                                    raise ValueError(f"Concept missing fields: {missing_concept_fields}")
                                    
                                # Validate validation structure
                                validation = concept["validation"]
                                required_validation_fields = ["confidence", "supported_by",
                                                           "contradicted_by", "needs_verification"]
                                missing_validation_fields = [f for f in required_validation_fields 
                                                          if f not in validation]
                                if missing_validation_fields:
                                    raise ValueError(f"Validation missing fields: {missing_validation_fields}")
                            
                            return json.dumps(parsed)
                            
                        except (json.JSONDecodeError, ValueError) as e:
                            self.logger.warning(f"Error parsing LLM response: {str(e)}")
                            self.logger.warning("Attempting to fix response format")
                            
                            # Extract any JSON-like content
                            import re
                            json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', content)
                            if json_match:
                                content = json_match.group(0)
                            
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
                mock_concept = {
                    "name": concept["name"],
                    "type": concept["type"],
                    "description": concept["description"],
                    "related": concept["related"],
                    "validation": {
                        "confidence": 0.8,
                        "supported_by": ["Evidence 1"],
                        "contradicted_by": [],
                        "needs_verification": []
                    }
                }
                
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
                        "content": f"""You are an AI agent specialized in {agent_type} analysis. You must respond with ONLY a JSON object, no other text.

The JSON must follow this EXACT format (do not add any fields or change the structure):
{{
    "response": "Your main response analyzing the input from a {agent_type} perspective",
    "concepts": [
        {{
            "name": "Name of an important concept identified",
            "type": "{agent_type}",
            "description": "Clear description of the concept",
            "related": ["Related", "Concept", "Terms"],
            "validation": {{
                "confidence": 0.8,
                "supported_by": ["Supporting evidence"],
                "contradicted_by": [],
                "needs_verification": []
            }}
        }}
    ],
    "key_points": ["Key insight 1", "Key insight 2"],
    "implications": ["Implication 1", "Implication 2"],
    "uncertainties": ["Uncertainty 1", "Uncertainty 2"],
    "reasoning": ["Reasoning step 1", "Reasoning step 2"]
}}

Remember:
1. Respond with ONLY the JSON object
2. No explanation text before or after
3. Ensure it's valid JSON (use double quotes, no trailing commas)
4. Keep the exact field names and structure"""
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
