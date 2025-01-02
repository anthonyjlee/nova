"""LM Studio integration for Nova."""

import aiohttp
import json
from typing import Dict, Any, Optional

class LMStudioLLM:
    """LM Studio integration for language model capabilities."""
    
    def __init__(
        self,
        chat_model: str,
        embedding_model: str,
        api_base: str = "http://localhost:1234/v1"
    ):
        """Initialize LM Studio integration."""
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.api_base = api_base
        
    async def get_structured_completion(
        self,
        prompt: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
        max_tokens: int = 1000
    ) -> Dict:
        """Get structured completion from LM Studio."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    json={
                        "model": self.chat_model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant that analyzes text and extracts structured information."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"LM Studio API error: {response.status}")
                        
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    try:
                        parsed = json.loads(content)
                        # Add confidence if not present
                        if isinstance(parsed, dict):
                            if "confidence" not in parsed:
                                parsed["confidence"] = 0.8
                            if "concepts" in parsed:
                                for concept in parsed["concepts"]:
                                    if "confidence" not in concept:
                                        concept["confidence"] = 0.8
                        return parsed
                    except json.JSONDecodeError:
                        # Return structured format even for non-JSON responses
                        return {
                            "response": content,
                            "confidence": 0.8,
                            "concepts": [{
                                "name": "LLM Analysis",
                                "type": agent_type or "analysis",
                                "description": content,
                                "confidence": 0.8
                            }],
                            "key_points": [content],
                            "implications": ["Analysis complete"],
                            "uncertainties": [],
                            "insights": [{"type": "analysis", "description": content, "confidence": 0.8}],
                            "metadata": metadata or {}
                        }
        except Exception as e:
            raise Exception(f"LM Studio error: {str(e)}")

    async def analyze(
        self,
        content: Dict[str, Any],
        template: str = "parsing_analysis",
        max_tokens: int = 1000
    ) -> Dict:
        """Analyze content using LM Studio."""
        try:
            # Prepare prompt based on template
            prompt = self._prepare_prompt(content, template)
            
            # Call LM Studio API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    json={
                        "model": self.chat_model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant that analyzes text and extracts structured information."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"LM Studio API error: {response.status}")
                        
                    result = await response.json()
                    
                    # Extract and parse response
                    response_text = result["choices"][0]["message"]["content"]
                    try:
                        parsed = json.loads(response_text)
                        
                        # Handle analytics response
                        if template == "analytics_processing":
                            if not isinstance(parsed.get("analytics"), dict):
                                parsed["analytics"] = {}
                            if not isinstance(parsed.get("insights"), list):
                                parsed["insights"] = []
                            return parsed
                        # Handle parsing response
                        else:
                            if not isinstance(parsed.get("concepts"), list):
                                parsed["concepts"] = []
                            if not isinstance(parsed.get("key_points"), list):
                                parsed["key_points"] = []
                            if not isinstance(parsed.get("structure"), dict):
                                parsed["structure"] = {}
                            return parsed
                    except json.JSONDecodeError:
                        # Attempt to extract structured data from unstructured response
                        concepts = []
                        key_points = []
                        
                        # Look for concept-like statements
                        lines = response_text.split("\n")
                        for line in lines:
                            line = line.strip()
                            if line.startswith("- "):
                                if "concept:" in line.lower():
                                    concepts.append({
                                        "statement": line.split(":", 1)[1].strip(),
                                        "type": "extracted_concept",
                                        "confidence": 0.5
                                    })
                                elif "key point:" in line.lower():
                                    key_points.append({
                                        "statement": line.split(":", 1)[1].strip(),
                                        "type": "extracted_key_point",
                                        "confidence": 0.5
                                    })
                                    
                        return {
                            "concepts": concepts,
                            "key_points": key_points,
                            "structure": {
                                "extraction_method": "fallback_parsing",
                                "original_text": response_text
                            }
                        }
                        
        except Exception as e:
            raise Exception(f"Analysis error: {str(e)}")
            
    def _prepare_prompt(self, content: Dict[str, Any], template: str) -> str:
        """Prepare prompt based on template."""
        if template == "analytics_processing":
            return f"""Analyze the following content and generate analytics insights. Return the result as a JSON object with the following structure:
{{
    "analytics": {{
        "key_metrics": [
            {{
                "name": "metric name",
                "value": metric_value,
                "confidence": confidence_score
            }}
        ],
        "trends": [
            {{
                "name": "trend name",
                "description": "trend description",
                "confidence": confidence_score
            }}
        ]
    }},
    "insights": [
        {{
            "type": "insight type",
            "description": "insight description",
            "confidence": confidence_score,
            "recommendations": ["list of recommendations"]
        }}
    ]
}}

Content to analyze:
{content.get("text", str(content))}

Domain: {content["metadata"].get("domain", "general")}
"""
        elif template == "parsing_analysis":
            return f"""Analyze the following text and extract structured information. Return the result as a JSON object with the following structure:
{{
    "concepts": [
        {{
            "statement": "concept statement",
            "type": "concept type",
            "confidence": confidence_score,
            "description": "optional description"
        }}
    ],
    "key_points": [
        {{
            "statement": "key point statement",
            "type": "key point type",
            "confidence": confidence_score,
            "importance": importance_score
        }}
    ],
    "structure": {{
        "sections": ["list of sections"],
        "relationships": ["list of relationships"],
        "domain_factors": {{"factor": "value"}},
        "complexity_factors": [
            {{
                "factor": "factor name",
                "weight": weight_score
            }}
        ]
    }}
}}

Text to analyze:
{content["text"]}

Domain: {content["metadata"].get("domain", "general")}
"""
        else:
            raise ValueError(f"Unknown template: {template}")
