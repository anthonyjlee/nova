"""
Research agent for analyzing and retrieving information.
"""

import logging
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from ..llm_interface import LLMInterface
from ..neo4j_store import Neo4jMemoryStore
from ..prompts import RESEARCH_PROMPT
from ..memory_types import AgentResponse

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """Agent for researching and retrieving information."""
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore
    ):
        """Initialize research agent."""
        super().__init__(llm, store, "research")
    
    def _format_prompt(self, content: Dict[str, Any]) -> str:
        """Format prompt for research analysis."""
        # Format content for prompt
        formatted_content = []
        
        # Add original content
        if isinstance(content.get('content'), str):
            formatted_content.append(f"Content: {content['content']}")
        
        # Add any command results
        if content.get('command_result'):
            result = content['command_result']
            formatted_content.append("Command Result:")
            formatted_content.append(f"Success: {result.get('success', False)}")
            if result.get('output'):
                formatted_content.append(f"Output: {result['output']}")
            if result.get('error'):
                formatted_content.append(f"Error: {result['error']}")
        
        # Add any system info
        if content.get('systems_info'):
            formatted_content.append("Systems Information:")
            for info in content['systems_info']:
                system = info['system']
                formatted_content.append(f"- {system['name']} ({system['type']})")
                formatted_content.append(f"  Created: {system['created_at']}")
                if system.get('capabilities'):
                    formatted_content.append("  Capabilities:")
                    for cap in system['capabilities']:
                        formatted_content.append(f"  - {cap['description']} ({cap['type']})")
                if info.get('relationships'):
                    formatted_content.append("  Relationships:")
                    for rel in info['relationships']:
                        formatted_content.append(f"  - {rel['relationship_type']} -> {rel['target_name']}")
        
        # Add any capabilities info
        if content.get('capabilities_info'):
            formatted_content.append("Capabilities Information:")
            for cap in content['capabilities_info']:
                formatted_content.append(f"- {cap['description']} ({cap['type']})")
                if cap.get('systems'):
                    formatted_content.append("  Used by: " + ", ".join(s['name'] for s in cap['systems']))
        
        # Add any related memories
        if content.get('related_memories'):
            formatted_content.append("Related Memories:")
            for memory in content['related_memories']:
                formatted_content.append(f"- {memory['type']} ({memory['created_at']})")
                if isinstance(memory.get('content'), str):
                    formatted_content.append(f"  Content: {memory['content'][:100]}...")
                if memory.get('relationships'):
                    formatted_content.append("  Relationships:")
                    for rel in memory['relationships']:
                        formatted_content.append(f"  - {rel['type']} -> {rel['target_type']}")
        
        # Format final prompt with focus on pragmatic capabilities
        formatted_content.append("\nFocus on identifying:")
        formatted_content.append("1. Concrete, implementable capabilities")
        formatted_content.append("2. Technical requirements and dependencies")
        formatted_content.append("3. Development timeline and complexity")
        formatted_content.append("4. Integration with existing capabilities")
        
        # Format final prompt
        return RESEARCH_PROMPT.format(
            content="\n".join(formatted_content)
        )
    
    async def process(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process content through research lens."""
        try:
            # Get system info if mentioned
            systems_info = []
            for system in ["Nova", "Nia", "Echo"]:
                if system.lower() in str(content).lower():
                    system_info = await self.get_system_info(system)
                    if system_info:
                        relationships = await self.get_system_relationships(system)
                        systems_info.append({
                            "system": system_info,
                            "relationships": relationships
                        })
            
            if systems_info:
                content["systems_info"] = systems_info
            
            # Get capabilities if mentioned
            if "capability" in str(content).lower():
                capabilities = await self.get_capabilities()
                if capabilities:
                    content["capabilities_info"] = capabilities
            
            # Get related memories
            memories = await self.search_memories(
                content_pattern=str(content),
                limit=5
            )
            if memories:
                content["related_memories"] = memories
            
            # Get LLM response
            response = await self.llm.get_structured_completion(
                self._format_prompt(content)
            )
            
            # Store research findings
            try:
                await self.store.store_memory(
                    memory_type="research",
                    content={
                        'original_content': content,
                        'research_findings': response.dict(),
                        'systems_analyzed': [s["system"]["name"] for s in systems_info],
                        'memories_found': len(memories) if memories else 0
                    },
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to store research memory: {str(e)}")
                # Continue even if memory storage fails
            
            return response
            
        except Exception as e:
            logger.error(f"Error in research agent: {str(e)}")
            raise
