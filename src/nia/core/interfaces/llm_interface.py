"""Interface for LLM interactions."""

import json
import logging
import re
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from ..types.memory_types import AgentResponse

if TYPE_CHECKING:
    from ..nova.core.parsing import NovaParser
    from .neo4j.neo4j_store import Neo4jMemoryStore
    from .vector.vector_store import VectorStore

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
        self.base_url = "http://localhost:1234/v1"
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
    async def check_lmstudio(self) -> bool:
        """Check if LMStudio is running and get available models."""
        from openai import AsyncOpenAI
        try:
            # Initialize OpenAI client for LMStudio
            client = AsyncOpenAI(
                base_url=self.base_url,
                api_key="lm-studio"  # LMStudio accepts any non-empty string
            )
            
            # Check models endpoint
            models = await client.models.list()
            if not models.data:
                return False
            
            # Test chat completions endpoint
            test_completion = await client.chat.completions.create(
                model=models.data[0].id,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                temperature=0.7
            )
            
            return bool(test_completion.choices)
            
        except Exception as e:
            self.logger.error(f"Error checking LMStudio: {str(e)}")
            return False
        
    def initialize_parser(
        self,
        store: 'Neo4jMemoryStore',
        vector_store: 'VectorStore'
    ) -> None:
        """Initialize parsing agent."""
        from ..nova.core.parsing import NovaParser
        self.parser = NovaParser(self, store, vector_store)
        
    def set_parser(self, parser: 'NovaParser'):
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
        """Make request to LMStudio API."""
        from openai import AsyncOpenAI
        import outlines
        from .schema import response_schema
        
        try:
            # Initialize OpenAI client for LMStudio
            client = AsyncOpenAI(
                base_url=self.base_url,
                api_key="lm-studio"  # LMStudio accepts any non-empty string
            )
            
            # First verify LMStudio is running
            if not await self.check_lmstudio():
                logger.warning("LMStudio is not running or not accessible")
                return json.dumps({
                    "response": "I apologize, but I'm currently unable to process messages. Please ensure LMStudio is running and try again.",
                    "dialogue": "LMStudio connection required",
                    "concepts": [{
                        "name": "Connection Error",
                        "type": "error",
                        "description": "LMStudio is not running or not accessible",
                        "related": [],
                        "validation": {
                            "confidence": 0.0,
                            "supported_by": [],
                            "contradicted_by": [],
                            "needs_verification": []
                        }
                    }],
                    "key_points": ["LMStudio connection required"],
                    "implications": ["Cannot process messages"],
                    "uncertainties": ["LMStudio status"],
                    "reasoning": ["Connection check failed"]
                })
            
            # Get available models
            models = await client.models.list()
            if not models.data:
                raise Exception("No models available in LMStudio")
            
            # Use first available model for chat completions
            model_id = models.data[0].id
            
            # Create outlines guide with our schema
            guide = outlines.Guide(response_schema)
            
            # Make completion request using outlines
            async def get_completion():
                completion = await client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=10000,  # Increased token limit
                    timeout=30.0  # Added timeout for longer responses
                )
                return completion.choices[0].message.content
                
            # Use outlines to get structured output
            try:
                result = guide.run(get_completion)
                self.logger.debug(f"Structured Output: {result}")
                return json.dumps(result)
            except Exception as e:
                self.logger.error(f"Error using outlines: {str(e)}")
                # Fallback to basic parsing if outlines fails
                completion = await get_completion()
                content = completion.strip()
            
            # Handle empty or invalid content
            if not content or content == "null":
                return json.dumps({
                    "response": "Empty or invalid response",
                    "concepts": [],
                    "key_points": [],
                    "implications": [],
                    "uncertainties": [],
                    "reasoning": []
                })
            
            # Parse and validate response
            try:
                # Parse JSON content
                parsed = json.loads(content) if content.startswith('{') else {"response": content}
                if not isinstance(parsed, dict):
                    parsed = {"response": str(parsed)}
                if "response" not in parsed:
                    parsed["response"] = content
                    
                # Log parsed structure
                logger.debug(f"Parsed response structure: {json.dumps(parsed, indent=2)}")
                
                # Extract and validate tasks if present
                if "tasks" in parsed:
                    logger.info(f"Found {len(parsed['tasks'])} tasks in response")
                    for task in parsed["tasks"]:
                        logger.debug(f"Task: {json.dumps(task, indent=2)}")
                    
                # Ensure required fields
                base_structure = {
                    "response": str(parsed.get("response", "")),
                    "dialogue": str(parsed.get("dialogue", parsed.get("response", ""))),
                    "concepts": [],
                    "key_points": [],
                    "implications": [],
                    "uncertainties": [],
                    "reasoning": [],
                    "tasks": [],  # Include tasks array
                    "metadata": {
                        "model": model_id,
                        "timestamp": datetime.now().isoformat(),
                        "total_tasks": 0,
                        "estimated_total_time": 0
                    }
                }
                
                # Copy valid fields from parsed response
                for field in ["concepts", "key_points", "implications", "uncertainties", "reasoning", "tasks"]:
                    if field in parsed and isinstance(parsed[field], list):
                        base_structure[field] = parsed[field]
                        
                # Update metadata if tasks present
                if "tasks" in parsed:
                    base_structure["metadata"]["total_tasks"] = len(parsed["tasks"])
                    base_structure["metadata"]["estimated_total_time"] = sum(
                        task.get("estimated_time", 0) for task in parsed["tasks"]
                    )
                        
                return json.dumps(base_structure)
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Error parsing response: {str(e)}")
                return json.dumps({
                    "response": content,
                    "dialogue": content,
                    "concepts": [{
                        "name": "Parse Error",
                        "type": "error",
                        "description": str(e),
                        "related": []
                    }],
                    "key_points": ["Error parsing response"],
                    "implications": ["Response needs reformatting"],
                    "uncertainties": ["Response structure"],
                    "reasoning": ["Parse error occurred"]
                })
                    
        except Exception as e:
            self.logger.error(f"Error making LLM request: {str(e)}")
            return json.dumps({
                "response": f"Error: {str(e)}",
                "dialogue": "I apologize, but I encountered an error while processing your request.",
                "concepts": [{
                    "name": "Processing Error",
                    "type": "error",
                    "description": str(e),
                    "related": []
                }],
                "key_points": ["Error occurred"],
                "implications": ["Request failed"],
                "uncertainties": ["Error cause"],
                "reasoning": ["Error handling"]
            })
    
    async def get_completion(self, prompt: str, agent_type: str = "default") -> str:
        """Get LLM completion."""
        try:
            if self.use_mock:
                # Use mock response for testing
                concept = self._get_mock_concept(agent_type)
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
                # Import system prompt
                from .prompts import SYSTEM_PROMPT, AGENT_PROMPTS
                
                # Get agent-specific prompt
                agent_prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["default"])
                
                messages = [
                    {
                        "role": "system",
                        "content": f"{agent_prompt}\n\n{SYSTEM_PROMPT.format(agent_type=agent_type)}"
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
        """Get structured LLM completion."""
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
