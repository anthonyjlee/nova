"""Handlers for the NIA chat system."""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j.neo4j_store import Neo4jMemoryStore
from nia.memory.vector.vector_store import VectorStore
from nia.memory.embeddings import EmbeddingService

# Import agents
from nia.nova.core.meta import MetaAgent
from nia.nova.core.structure import StructureAgent
from nia.nova.core.parsing import NovaParser
from nia.memory.agents.belief_agent import BeliefAgent
from nia.memory.agents.desire_agent import DesireAgent
from nia.memory.agents.emotion_agent import EmotionAgent
from nia.memory.agents.reflection_agent import ReflectionAgent
from nia.memory.agents.research_agent import ResearchAgent
from nia.nova.tasks.planner import TaskPlannerAgent

logger = logging.getLogger(__name__)

class System2Handler:
    """Chat system handler with full agent integration."""
    def __init__(self, state=None):
        """Initialize System2Handler with optional state."""
        logger.info("Initializing System2Handler")
        self.state = state
        
        # Initialize core components
        self.llm = LLMInterface(use_mock=False)
        self.store = Neo4jMemoryStore()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(embedding_service=self.embedding_service)
        
        # Initialize parsing and structure agents
        self.structure_agent = StructureAgent(self.llm, self.store, self.vector_store)
        self.parsing_agent = NovaParser(self.llm, self.store, self.vector_store)
        self.llm.set_parser(self.parsing_agent)
        
        # Initialize specialized agents
        self.task_planner = TaskPlannerAgent(self.llm, self.store, self.vector_store)
        self.belief_agent = BeliefAgent(self.llm, self.store, self.vector_store)
        self.desire_agent = DesireAgent(self.llm, self.store, self.vector_store)
        self.emotion_agent = EmotionAgent(self.llm, self.store, self.vector_store)
        self.reflection_agent = ReflectionAgent(self.llm, self.store, self.vector_store)
        self.research_agent = ResearchAgent(self.llm, self.store, self.vector_store)
        
        # Initialize MetaAgent (Nova) with agents
        self.nova = MetaAgent(
            llm=self.llm,
            store=self.store,
            vector_store=self.vector_store,
            agents={
                'belief': self.belief_agent,
                'desire': self.desire_agent,
                'emotion': self.emotion_agent,
                'reflection': self.reflection_agent,
                'research': self.research_agent,
                'task_planner': self.task_planner
            }
        )
        
        # Initialize or restore chat histories from state
        self.chat_histories = self.state.get('chat_histories', {}) if self.state else {}
        self.agents = {
            "Nova (Main)": "Main chat interface",
            "Meta Agent": "Coordinates and synthesizes agent interactions",
            "Belief Agent": "Handles belief and knowledge validation",
            "Desire Agent": "Manages goals and aspirations",
            "Emotion Agent": "Processes emotional context",
            "Reflection Agent": "Analyzes patterns and provides insights"
        }

    async def send_message(
        self,
        message: str,
        chat_history: List[Dict[str, str]],
        agent: str
    ) -> Tuple[List[Dict[str, str]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Handle chat message with full agent integration and interaction tracking."""
        try:
            logger.info(f"Processing message for {agent}")
            
            # Update chat history in state
            if agent not in self.chat_histories:
                self.chat_histories[agent] = []
            self.chat_histories[agent].extend(chat_history)
            if self.state:
                self.state.set('chat_histories', self.chat_histories)
            
            # Track agent interactions
            agent_interactions = []
            
            # Process through Nova with interaction tracking
            response = await self.nova.process_interaction(
                text=message,
                metadata={
                    "type": "user_input",
                    "timestamp": datetime.now(),
                    "agent": agent
                }
            )
            
            # Record agent interactions from metadata
            if response.metadata.get('agent_interactions'):
                agent_interactions.extend(response.metadata['agent_interactions'])
            
            # Record belief validation
            if response.concepts:
                agent_interactions.append({
                    "role": "assistant",
                    "content": f"[BeliefAgent] Validating concepts: {', '.join(c['name'] for c in response.concepts)}"
                })
            
            # Record emotion assessment if present
            if hasattr(response, 'emotional_state'):
                agent_interactions.append({
                    "role": "assistant",
                    "content": f"[EmotionAgent] Emotional assessment: {response.emotional_state}"
                })
            
            # Record reflection insights if present
            if hasattr(response, 'reflections'):
                agent_interactions.append({
                    "role": "assistant",
                    "content": f"[ReflectionAgent] Reflection: {response.reflections}"
                })
            
            # Update chat history with Nova's synthesized response
            chat_history.append({
                "role": "assistant",
                "content": response.response
            })
            
            # Return chat history and additional data
            return chat_history, {
                "concepts": response.concepts,
                "agent_interactions": agent_interactions
            }, None
            
        except Exception as e:
            logger.error(f"Error in message handling: {str(e)}")
            chat_history.append({
                "role": "assistant",
                "content": f"Error processing message: {str(e)}"
            })
            return chat_history, None, None

    async def cleanup(self):
        """Cleanup resources."""
        try:
            await self.nova.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

class MemoryHandler:
    """Memory system integration handler."""
    def __init__(self, state=None):
        """Initialize MemoryHandler with optional state."""
        logger.info("Initializing MemoryHandler")
        self.state = state
        self.store = Neo4jMemoryStore()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(embedding_service=self.embedding_service)
        
    async def store_memory(self, content: Dict[str, Any]) -> str:
        """Store memory in both vector and graph stores."""
        try:
            # Store in vector store
            vector_id = await self.vector_store.store_vector(content)
            
            # Store in graph store
            memory_id = await self.store.store_memory(content)
            
            # Store in state if available
            if self.state:
                memories = self.state.get('stored_memories', [])
                memories.append({
                    'id': memory_id,
                    'vector_id': vector_id,
                    'timestamp': datetime.now().isoformat()
                })
                self.state.set('stored_memories', memories)
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
            
    async def retrieve_memory(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from both stores."""
        try:
            # Search vector store
            vector_results = await self.vector_store.search_vectors(
                content={"text": query},
                limit=5
            )
            
            # Search graph store
            graph_results = await self.store.search_memories(
                content_pattern=query,
                include_concepts=True
            )
            
            # Combine and deduplicate results
            all_results = []
            seen_ids = set()
            
            for result in vector_results + graph_results:
                result_id = result.get("id")
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    all_results.append(result)
            
            # Update state with retrieval info if available
            if self.state:
                retrievals = self.state.get('memory_retrievals', [])
                retrievals.append({
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'result_count': len(all_results)
                })
                self.state.set('memory_retrievals', retrievals)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            raise
