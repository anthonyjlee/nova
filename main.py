"""
Main entry point for NIA system.
"""

import asyncio
import logging
from datetime import datetime
from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.memory.embeddings import EmbeddingService
from nia.memory.logging_config import configure_logging

# Import agents
from nia.memory.agents.meta_agent import MetaAgent
from nia.memory.agents.belief_agent import BeliefAgent
from nia.memory.agents.desire_agent import DesireAgent
from nia.memory.agents.emotion_agent import EmotionAgent
from nia.memory.agents.reflection_agent import ReflectionAgent
from nia.memory.agents.research_agent import ResearchAgent
from nia.memory.agents.task_planner_agent import TaskPlannerAgent

async def main():
    """Main entry point."""
    # Setup logging
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting NIA system")
    
    try:
        # Initialize core components
        llm = LLMInterface()
        store = Neo4jMemoryStore()
        embedding_service = EmbeddingService()
        vector_store = VectorStore(embedding_service=embedding_service)
        
        # Initialize specialized agents
        task_planner = TaskPlannerAgent(llm, store, vector_store)
        belief_agent = BeliefAgent(llm, store, vector_store)
        desire_agent = DesireAgent(llm, store, vector_store)
        emotion_agent = EmotionAgent(llm, store, vector_store)
        reflection_agent = ReflectionAgent(llm, store, vector_store)
        research_agent = ResearchAgent(llm, store, vector_store)
        
        # Initialize MetaAgent (Nova) with other agents
        nova = MetaAgent(
            llm=llm,
            store=store,
            vector_store=vector_store,
            task_planner=task_planner,
            other_agents={
                'belief': belief_agent,
                'desire': desire_agent,
                'emotion': emotion_agent,
                'reflection': reflection_agent,
                'research': research_agent
            }
        )
        
        logger.info("Initialized all agents")
        
        # Get initial system status
        status = await nova.get_status()
        logger.info(f"System status: {status}")
        
        print("\nNIA System")
        print("==========")
        print("Nova is ready to engage in conversation.")
        print("Type 'exit' to quit")
        print("Type 'status' to check system status")
        print("Type 'search <query>' to search memories")
        print("Type 'reset' to reset memory stores")
        print("Type 'help' to see all commands")
        print("Otherwise, engage in conversation with Nova\n")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'exit':
                    break
                    
                if user_input.lower() == 'status':
                    status = await nova.get_status()
                    print(f"\nSystem Status:")
                    print("Vector Store:")
                    print(f"  - Episodic Layer: {status['vector_store'].get('episodic_count', 0)} memories")
                    print(f"  - Semantic Layer: {status['vector_store'].get('semantic_count', 0)} memories")
                    print(f"  - Last Consolidation: {status['vector_store'].get('last_consolidation', 'Never')}")
                    print("\nNeo4j:")
                    print(f"  - Concepts: {status['neo4j'].get('concept_count', 0)} stored")
                    print(f"  - Relationships: {status['neo4j'].get('relationship_count', 0)} mapped")
                    print("\nActive Agents:")
                    for agent in status.get('active_agents', []):
                        print(f"  - {agent}")
                    print("\nMemory Consolidation:")
                    next_consolidation = status['vector_store'].get('next_consolidation', 'Unknown')
                    print(f"  - Next scheduled: {next_consolidation}")
                    continue
                    
                if user_input.lower() == 'reset':
                    print("\nResetting system...")
                    print("- Clearing episodic memories...")
                    print("- Clearing semantic memories...")
                    print("- Resetting concept storage...")
                    print("- Resetting consolidation timer...")
                    print("- Clearing agent states...")
                    await nova.cleanup()
                    print("Reset complete")
                    continue
                    
                if user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("- exit: Quit the system")
                    print("- status: Check detailed system status (memory layers, concepts, agents)")
                    print("- search <query>: Search memories across layers with relevance scores")
                    print("- reset: Reset all memory stores and system state")
                    print("- consolidate: Force memory consolidation")
                    print("- help: Show this help message")
                    continue
                    
                if user_input.lower().startswith('search '):
                    query = user_input[7:].strip()
                    memories = await nova.search_memories(query)
                    print(f"\nFound {len(memories)} related memories:")
                    for i, memory in enumerate(memories, 1):
                        print(f"\n{i}. Layer: {memory.get('layer', 'unknown')}")
                        print(f"   Score: {memory.get('score', 0):.3f}")
                        print(f"   Type: {memory.get('type', 'unknown')}")
                        print(f"   Content: {memory.get('content', '')}")
                        if memory.get('layer') == 'semantic':
                            print(f"   Related Concepts: {', '.join(c['name'] for c in memory.get('concepts', []))}")
                        print(f"   Metadata: {memory.get('metadata', {})}")
                    continue

                if user_input.lower() == 'consolidate':
                    print("\nForcing memory consolidation...")
                    await nova._consolidate_memories()
                    status = await nova.get_status()
                    print("\nConsolidation complete:")
                    print(f"- Semantic memories: {status['vector_store'].get('semantic_count', 0)}")
                    print(f"- Concepts stored: {status['neo4j'].get('concept_count', 0)}")
                    print(f"- Next consolidation: {status['vector_store'].get('next_consolidation', 'Unknown')}")
                    continue
                
                # Process through Nova
                response = await nova.process_interaction(
                    text=user_input,
                    metadata={
                        "type": "user_input",
                        "timestamp": datetime.now()
                    }
                )
                
                # Display response
                print("\nNova:", response.response)
                
                # Show validated concepts if any
                if response.concepts:
                    print("\nValidated Concepts:")
                    for concept in response.concepts:
                        validation = concept.get('validation', {})
                        supporters = len(validation.get('supported_by', []))
                        contradictors = len(validation.get('contradicted_by', []))
                        print(f"\n- {concept['name']} ({concept['type']}, confidence: {validation.get('confidence', 0):.2f})")
                        print(f"  Description: {concept['description']}")
                        print(f"  Support: {supporters} for, {contradictors} against")
                        if concept.get('related'):
                            print(f"  Related: {', '.join(concept['related'])}")
                
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                break
                
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}")
                print(f"\nError: {str(e)}")
        
        # Cleanup
        await nova.cleanup()
        logger.info("Shut down NIA system")
        
    except Exception as e:
        logger.error(f"System error: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
