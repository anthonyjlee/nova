"""Memory system integration with enhanced parsing capabilities."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from .memory_types import AgentResponse, Memory
from .llm_interface import LLMInterface
from .neo4j_store import Neo4jMemoryStore
from .vector_store import VectorStore
from .agents.belief_agent import BeliefAgent
from .agents.desire_agent import DesireAgent
from .agents.emotion_agent import EmotionAgent
from .agents.reflection_agent import ReflectionAgent
from .research_agent import ResearchAgent
from .agents.meta_agent import MetaAgent
from .agents.structure_agent import StructureAgent
from .agents.task_agent import TaskAgent
from .agents.dialogue_agent import DialogueAgent
from .agents.context_agent import ContextAgent

logger = logging.getLogger(__name__)

def truncate_content(content: str, max_length: int = 8192) -> str:
    """Truncate content to max length."""
    if len(content) > max_length:
        return content[:max_length] + "..."
    return content

def serialize_datetime(obj: Any) -> Any:
    """Serialize datetime objects to ISO format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

class MemorySystem:
    """Memory system integration with enhanced parsing capabilities.
    
    The system uses a multi-agent architecture for processing and understanding:
    
    Core Processing:
    - ParsingAgent: Basic text and JSON parsing
    - StructureAgent: Complex data structure analysis
    
    Understanding:
    - BeliefAgent: Epistemological analysis
    - DesireAgent: Goal and motivation analysis
    - EmotionAgent: Emotional intelligence
    - ReflectionAgent: Meta-learning and patterns
    - ResearchAgent: Knowledge integration
    
    Task Management:
    - TaskAgent: Planning and execution
    - DialogueAgent: Conversation flow
    - ContextAgent: Environmental understanding
    
    Integration:
    - MetaAgent: Response synthesis and dialogue
    """
    
    def __init__(
        self,
        llm: LLMInterface,
        store: Neo4jMemoryStore,
        vector_store: VectorStore
    ):
        """Initialize memory system."""
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        
        # Initialize core processing agents
        self.structure_agent = StructureAgent(llm, store, vector_store)
        
        # Initialize parser and connect structure agent
        self.llm.initialize_parser(store, vector_store)
        parser = self.llm.parser
        if parser:
            parser.set_structure_agent(self.structure_agent)
        
        # Initialize understanding agents
        self.belief_agent = BeliefAgent(llm, store, vector_store)
        self.desire_agent = DesireAgent(llm, store, vector_store)
        self.emotion_agent = EmotionAgent(llm, store, vector_store)
        self.reflection_agent = ReflectionAgent(llm, store, vector_store)
        self.research_agent = ResearchAgent(llm, store, vector_store)
        
        # Initialize task management agents
        self.task_agent = TaskAgent(llm, store, vector_store)
        self.dialogue_agent = DialogueAgent(llm, store, vector_store)
        self.context_agent = ContextAgent(llm, store, vector_store)
        
        # Initialize integration agent
        self.meta_agent = MetaAgent(llm, store, vector_store)
        
        # Track consolidation
        self.last_consolidation = datetime.now()
        self.consolidation_interval = 60 * 60  # 1 hour
    
    async def _check_consolidation(self) -> None:
        """Check if consolidation is needed."""
        now = datetime.now()
        if (now - self.last_consolidation).total_seconds() > self.consolidation_interval:
            await self._consolidate_memories()
            self.last_consolidation = now
    
    async def _consolidate_memories(self) -> None:
        """Consolidate memories into semantic layer."""
        try:
            # Get recent episodic memories
            recent = await self.vector_store.search_vectors(
                content="",
                limit=100,
                layer="episodic"
            )
            
            # Group by topic/theme
            groups = {}
            for memory in recent:
                key = memory.get("type", "general")
                if key not in groups:
                    groups[key] = []
                groups[key].append(memory)
            
            # Consolidate each group
            for group_type, memories in groups.items():
                # Extract content
                content = "\n".join([
                    m.get("content", {}).get("content", "") if isinstance(m.get("content"), dict)
                    else str(m.get("content", ""))
                    for m in memories
                ])
                
                # Process through agents
                responses = {}
                content_dict = {'content': content, 'memories': memories}
                
                # Process through understanding agents
                for agent_type, agent in [
                    ('belief', self.belief_agent),
                    ('desire', self.desire_agent),
                    ('emotion', self.emotion_agent),
                    ('reflection', self.reflection_agent),
                    ('research', self.research_agent)
                ]:
                    responses[agent_type] = await agent.process(content_dict)
                
                # Process through task management agents
                for agent_type, agent in [
                    ('task', self.task_agent),
                    ('dialogue', self.dialogue_agent),
                    ('context', self.context_agent)
                ]:
                    responses[agent_type] = await agent.process(content_dict)
                
                # Analyze structure
                structure_response = await self.structure_agent.analyze_structure(content)
                responses['structure'] = structure_response
                
                # Synthesize responses
                synthesis = await self.meta_agent.synthesize_dialogue({
                    'content': {'content': content},
                    'agent_responses': responses
                })
                
                # Store consolidated memory
                memory_id = str(uuid.uuid4())
                timestamp = datetime.now()
                
                # Create memory content with consolidation type
                memory_content = {
                    'content': truncate_content(content),
                    'synthesis': synthesis.dict(),
                    'original_memories': [m.get('id') for m in memories],
                    'timestamp': timestamp,
                    'type': 'consolidation',  # Explicitly set type
                    'id': memory_id,
                    'group_type': group_type
                }
                
                # Create metadata with consolidation type
                memory_metadata = {
                    'id': memory_id,
                    'type': 'consolidation',  # Explicitly set type
                    'group_type': group_type,
                    'original_count': len(memories),
                    'layer': 'semantic',
                    'timestamp': timestamp
                }
                
                # Store in vector store
                await self.vector_store.store_vector(
                    content=serialize_datetime(memory_content),
                    metadata=serialize_datetime(memory_metadata),
                    layer="semantic"
                )
                
                # Store extracted concepts
                for concept in synthesis.concepts:
                    await self.store.store_concept(
                        name=concept["name"],
                        type=concept["type"],
                        description=concept["description"]
                    )
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {str(e)}")
    
    async def _find_relevant_memories(
        self,
        content: str,
        limit: int = 5
    ) -> List[Dict]:
        """Find relevant memories from both layers."""
        try:
            # Search both layers
            episodic = await self.vector_store.search_vectors(
                content=content,
                limit=limit,
                layer="episodic"
            )
            semantic = await self.vector_store.search_vectors(
                content=content,
                limit=limit,
                layer="semantic"
            )
            
            # Combine and sort by relevance
            all_memories = episodic + semantic
            all_memories.sort(
                key=lambda x: x.get("score", 0),
                reverse=True
            )
            
            return all_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error finding relevant memories: {str(e)}")
            return []
    
    async def process_interaction(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> AgentResponse:
        """Process an interaction through the memory system."""
        try:
            # Check for memory consolidation
            await self._check_consolidation()
            
            # Generate UUID for memory ID
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Store in episodic memory (raw interaction)
            await self.vector_store.store_vector(
                content=serialize_datetime({
                    'content': truncate_content(content),
                    'timestamp': timestamp,
                    'type': 'interaction',
                    'layer': 'episodic'  # Explicitly set layer in content
                }),
                metadata=serialize_datetime({
                    'id': memory_id,
                    'type': 'interaction',
                    'layer': 'episodic',  # Explicitly set layer in metadata
                    **(metadata or {})
                }),
                layer="episodic"
            )
            
            # Find relevant memories from both layers
            similar_memories = await self._find_relevant_memories(content)
            
            # Process through agent system
            content_dict = {
                'content': truncate_content(content),
                'similar_memories': similar_memories,
                **(metadata or {})
            }
            
            # Get agent responses
            responses = {}
            
            # Process through understanding agents
            for agent_type, agent in [
                ('belief', self.belief_agent),
                ('desire', self.desire_agent),
                ('emotion', self.emotion_agent),
                ('reflection', self.reflection_agent),
                ('research', self.research_agent)
            ]:
                responses[agent_type] = await agent.process(content_dict)
                logger.info(f"{agent_type.capitalize()}Agent processed interaction")
            
            # Process through task management agents
            for agent_type, agent in [
                ('task', self.task_agent),
                ('dialogue', self.dialogue_agent),
                ('context', self.context_agent)
            ]:
                responses[agent_type] = await agent.process(content_dict)
                logger.info(f"{agent_type.capitalize()}Agent processed interaction")
            
            # Analyze structure
            structure_response = await self.structure_agent.analyze_structure(content)
            responses['structure'] = structure_response
            logger.info("StructureAgent processed interaction")
            
            # Synthesize responses using dialogue format
            response = await self.meta_agent.synthesize_dialogue({
                'content': {'content': content},
                'dialogue_context': None,
                'agent_responses': responses
            })
            
            # Store processed memory in semantic layer
            await self.vector_store.store_vector(
                content=serialize_datetime({
                    'content': truncate_content(content),
                    'memory_id': memory_id,
                    'similar_memories': similar_memories,
                    'response': response.dict(),
                    'timestamp': datetime.now(),
                    'type': 'processed_memory',
                    'layer': 'semantic'  # Explicitly set layer in content
                }),
                metadata=serialize_datetime({
                    'id': str(uuid.uuid4()),
                    'type': 'processed_memory',
                    'original_memory_id': memory_id,
                    'layer': 'semantic',  # Explicitly set layer in metadata
                    **(metadata or {})
                }),
                layer="semantic"
            )
            
            # Store extracted concepts in knowledge graph
            for concept in response.concepts:
                # Store concept
                await self.store.store_concept(
                    name=concept["name"],
                    type=concept["type"],
                    description=concept["description"]
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}")
            return AgentResponse(
                response="Error processing interaction",
                concepts=[],
                key_points=[],
                implications=[],
                uncertainties=[],
                reasoning=[],
                perspective="error",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def search_memories(
        self,
        query: str,
        include_episodic: bool = True,
        include_semantic: bool = True,
        limit: int = 10
    ) -> List[Dict]:
        """Search memories across layers."""
        try:
            results = []
            
            # Search episodic layer
            if include_episodic:
                episodic = await self.vector_store.search_vectors(
                    content=query,
                    limit=limit,
                    layer="episodic"
                )
                results.extend(episodic)
            
            # Search semantic layer
            if include_semantic:
                semantic = await self.vector_store.search_vectors(
                    content=query,
                    limit=limit,
                    layer="semantic",
                    include_metadata=True  # Ensure metadata is included
                )
                # Filter out non-semantic memories
                semantic = [m for m in semantic if m.get("layer") == "semantic"]
                results.extend(semantic)
            
            # Sort by relevance
            results.sort(
                key=lambda x: x.get("score", 0),
                reverse=True
            )
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
