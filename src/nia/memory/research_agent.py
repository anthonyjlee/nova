"""
Research agent for analyzing and retrieving information.
"""

import logging
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for researching and retrieving information."""
    
    async def process(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through research lens."""
        try:
            # First check if content mentions any systems
            systems_info = []
            for system in ["Nova", "Nia", "Echo"]:
                if system.lower() in str(content).lower():
                    system_info = await self.store.get_system_info(system)
                    if system_info:
                        relationships = await self.store.get_system_relationships(system)
                        systems_info.append({
                            "system": system_info,
                            "relationships": relationships
                        })
            
            # Add system info to content if found
            if systems_info:
                content["systems_info"] = systems_info
            
            # Check for capabilities
            if "capability" in str(content).lower():
                capabilities = await self.store.get_capabilities()
                if capabilities:
                    content["capabilities_info"] = capabilities
            
            # Search related memories
            memories = await self.store.search_memories(
                content_pattern=str(content),
                limit=5
            )
            if memories:
                content["related_memories"] = memories
            
            # Get LLM response with enhanced context
            response = await self.llm.get_structured_completion(
                self._format_prompt(content)
            )
            
            # Store research findings
            await self.store.store_memory(
                memory_type="research",
                content={
                    "original_content": content,
                    "research_findings": response.dict(),
                    "systems_analyzed": [s["system"]["name"] for s in systems_info],
                    "memories_found": len(memories) if memories else 0
                },
                metadata=metadata
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in ResearchAgent: {str(e)}")
            raise
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for research analysis."""
        prompt = "Analyze the following content through a research lens:\n\n"
        
        # Add original content
        if isinstance(content.get("content"), str):
            prompt += f"Content: {content['content']}\n\n"
        
        # Add systems info if available
        if content.get("systems_info"):
            prompt += "Systems Information:\n"
            for info in content["systems_info"]:
                system = info["system"]
                prompt += f"- {system['name']} ({system['type']})\n"
                prompt += f"  Created: {system['created_at']}\n"
                prompt += f"  Capabilities: {len(system['capabilities'])}\n"
                if info["relationships"]:
                    prompt += "  Relationships:\n"
                    for rel in info["relationships"]:
                        prompt += f"  - {rel['relationship_type']} -> {rel['target_name']}\n"
                prompt += "\n"
        
        # Add capabilities info if available
        if content.get("capabilities_info"):
            prompt += "Capabilities Information:\n"
            for cap in content["capabilities_info"]:
                prompt += f"- {cap['description']} ({cap['type']})\n"
                if cap["systems"]:
                    prompt += "  Used by: " + ", ".join(s["name"] for s in cap["systems"]) + "\n"
            prompt += "\n"
        
        # Add related memories if available
        if content.get("related_memories"):
            prompt += "Related Memories:\n"
            for memory in content["related_memories"]:
                prompt += f"- {memory['type']} ({memory['created_at']})\n"
                if isinstance(memory["content"], str):
                    prompt += f"  Content: {memory['content'][:100]}...\n"
            prompt += "\n"
        
        prompt += """
Based on the above information, provide a research analysis. Format your response as a JSON object with:
{
    "response": "Your research findings",
    "analysis": {
        "key_points": ["Important point 1", "Important point 2"],
        "confidence": 0.8,
        "state_update": "Brief state description"
    }
}
"""
        
        return prompt
