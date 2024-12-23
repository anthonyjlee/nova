"""
Main entry point for NIA system.
"""

import asyncio
import logging
from datetime import datetime
import difflib
from colorama import init, Fore, Style
from nia.memory.llm_interface import LLMInterface
from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.memory.vector_store import VectorStore
from nia.memory.embeddings import EmbeddingService
from nia.memory.logging_config import configure_logging

# Import agents
from nia.memory.agents.meta_agent import MetaAgent
from nia.memory.agents.structure_agent import StructureAgent
from nia.memory.agents.parsing_agent import ParsingAgent
from nia.memory.agents.belief_agent import BeliefAgent
from nia.memory.agents.desire_agent import DesireAgent
from nia.memory.agents.emotion_agent import EmotionAgent
from nia.memory.agents.reflection_agent import ReflectionAgent
from nia.memory.agents.research_agent import ResearchAgent
from nia.memory.agents.task_planner_agent import TaskPlannerAgent

# Initialize colorama
init()

# Available commands for typo checking
COMMANDS = ['exit', 'status', 'search', 'reset', 'help', 'consolidate']

def get_command_suggestion(input_cmd: str) -> str:
    """Get closest matching command for typo correction."""
    matches = difflib.get_close_matches(input_cmd.lower(), COMMANDS, n=1, cutoff=0.6)
    return matches[0] if matches else ""

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
        
        # Initialize parsing and structure agents
        structure_agent = StructureAgent(llm, store, vector_store)
        parsing_agent = ParsingAgent(llm, store, vector_store)
        parsing_agent.set_structure_agent(structure_agent)
        llm.set_parser(parsing_agent)
        
        # Initialize specialized agents
        task_planner = TaskPlannerAgent(llm, store, vector_store)
        belief_agent = BeliefAgent(llm, store, vector_store)
        desire_agent = DesireAgent(llm, store, vector_store)
        emotion_agent = EmotionAgent(llm, store, vector_store)
        reflection_agent = ReflectionAgent(llm, store, vector_store)
        research_agent = ResearchAgent(llm, store, vector_store)
        
        # Initialize MetaAgent (Nova) with agents
        nova = MetaAgent(
            llm=llm,
            store=store,
            vector_store=vector_store,
            agents={
                'belief': belief_agent,
                'desire': desire_agent,
                'emotion': emotion_agent,
                'reflection': reflection_agent,
                'research': research_agent,
                'task_planner': task_planner
            }
        )
        
        logger.info("Initialized all agents")
        
        # Get initial system status
        status = await nova.get_status()
        logger.info(f"System status: {status}")
        
        print(f"\n{Fore.CYAN}NIA System{Style.RESET_ALL}")
        print(f"{Fore.CYAN}=========={Style.RESET_ALL}")
        print(f"{Fore.GREEN}Nova is ready to engage in conversation.{Style.RESET_ALL}")
        print(f"Type '{Fore.YELLOW}exit{Style.RESET_ALL}' to quit")
        print(f"Type '{Fore.YELLOW}status{Style.RESET_ALL}' to check system status")
        print(f"Type '{Fore.YELLOW}search <query>{Style.RESET_ALL}' to search memories")
        print(f"Type '{Fore.YELLOW}reset{Style.RESET_ALL}' to reset memory stores")
        print(f"Type '{Fore.YELLOW}help{Style.RESET_ALL}' to see all commands")
        print("Otherwise, engage in conversation with Nova\n")
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n{Fore.CYAN}You:{Style.RESET_ALL} ").strip()
                
                if not user_input:
                    continue
                
                # Check for typos in commands
                if user_input.lower() not in ['exit', 'status', 'reset', 'help', 'consolidate'] and \
                   not user_input.lower().startswith('search '):
                    suggestion = get_command_suggestion(user_input.lower())
                    if suggestion:
                        print(f"{Fore.YELLOW}Did you mean '{suggestion}'?{Style.RESET_ALL}")
                    
                if user_input.lower() == 'exit':
                    break
                    
                if user_input.lower() == 'status':
                    status = await nova.get_status()
                    print(f"\n{Fore.CYAN}System Status:{Style.RESET_ALL}")
                    print(f"{Fore.MAGENTA}Vector Store:{Style.RESET_ALL}")
                    print(f"  - Episodic Layer: {Fore.YELLOW}{status['vector_store'].get('episodic_count', 0)}{Style.RESET_ALL} memories")
                    print(f"  - Semantic Layer: {Fore.YELLOW}{status['vector_store'].get('semantic_count', 0)}{Style.RESET_ALL} memories")
                    print(f"  - Last Consolidation: {Fore.YELLOW}{status['vector_store'].get('last_consolidation', 'Never')}{Style.RESET_ALL}")
                    print(f"\n{Fore.MAGENTA}Neo4j:{Style.RESET_ALL}")
                    print(f"  - Concepts: {Fore.YELLOW}{status['neo4j'].get('concept_count', 0)}{Style.RESET_ALL} stored")
                    print(f"  - Relationships: {Fore.YELLOW}{status['neo4j'].get('relationship_count', 0)}{Style.RESET_ALL} mapped")
                    print(f"\n{Fore.MAGENTA}Active Agents:{Style.RESET_ALL}")
                    for agent in status.get('active_agents', []):
                        print(f"  - {Fore.YELLOW}{agent}{Style.RESET_ALL}")
                    print(f"\n{Fore.MAGENTA}Memory Consolidation:{Style.RESET_ALL}")
                    next_consolidation = status['vector_store'].get('next_consolidation', 'Unknown')
                    print(f"  - Next scheduled: {Fore.YELLOW}{next_consolidation}{Style.RESET_ALL}")
                    continue
                    
                if user_input.lower() == 'reset':
                    print(f"\n{Fore.YELLOW}Resetting system...{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}- Clearing episodic memories...{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}- Clearing semantic memories...{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}- Resetting concept storage...{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}- Resetting consolidation timer...{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}- Clearing agent states...{Style.RESET_ALL}")
                    await nova.cleanup()
                    print(f"{Fore.GREEN}Reset complete{Style.RESET_ALL}")
                    continue
                    
                if user_input.lower() == 'help':
                    print(f"\n{Fore.CYAN}Available commands:{Style.RESET_ALL}")
                    print(f"- {Fore.YELLOW}exit{Style.RESET_ALL}: Quit the system")
                    print(f"- {Fore.YELLOW}status{Style.RESET_ALL}: Check detailed system status (memory layers, concepts, agents)")
                    print(f"- {Fore.YELLOW}search <query>{Style.RESET_ALL}: Search memories across layers with relevance scores")
                    print(f"- {Fore.YELLOW}reset{Style.RESET_ALL}: Reset all memory stores and system state")
                    print(f"- {Fore.YELLOW}consolidate{Style.RESET_ALL}: Force memory consolidation")
                    print(f"- {Fore.YELLOW}help{Style.RESET_ALL}: Show this help message")
                    continue
                    
                if user_input.lower().startswith('search '):
                    query = user_input[7:].strip()
                    memories = await nova.search_memories(query)
                    print(f"\n{Fore.GREEN}Found {len(memories)} related memories:{Style.RESET_ALL}")
                    for i, memory in enumerate(memories, 1):
                        print(f"\n{Fore.CYAN}{i}. Layer:{Style.RESET_ALL} {Fore.YELLOW}{memory.get('layer', 'unknown')}{Style.RESET_ALL}")
                        print(f"   {Fore.CYAN}Score:{Style.RESET_ALL} {Fore.YELLOW}{memory.get('score', 0):.3f}{Style.RESET_ALL}")
                        print(f"   {Fore.CYAN}Type:{Style.RESET_ALL} {Fore.YELLOW}{memory.get('type', 'unknown')}{Style.RESET_ALL}")
                        print(f"   {Fore.CYAN}Content:{Style.RESET_ALL} {memory.get('content', '')}")
                        if memory.get('layer') == 'semantic':
                            concepts = ', '.join(c['name'] for c in memory.get('concepts', []))
                            print(f"   {Fore.CYAN}Related Concepts:{Style.RESET_ALL} {Fore.YELLOW}{concepts}{Style.RESET_ALL}")
                        print(f"   {Fore.CYAN}Metadata:{Style.RESET_ALL} {memory.get('metadata', {})}")
                    continue

                if user_input.lower() == 'consolidate':
                    print(f"\n{Fore.YELLOW}Forcing memory consolidation...{Style.RESET_ALL}")
                    await nova._consolidate_memories()
                    status = await nova.get_status()
                    print(f"\n{Fore.GREEN}Consolidation complete:{Style.RESET_ALL}")
                    print(f"- Semantic memories: {Fore.YELLOW}{status['vector_store'].get('semantic_count', 0)}{Style.RESET_ALL}")
                    print(f"- Concepts stored: {Fore.YELLOW}{status['neo4j'].get('concept_count', 0)}{Style.RESET_ALL}")
                    print(f"- Next consolidation: {Fore.YELLOW}{status['vector_store'].get('next_consolidation', 'Unknown')}{Style.RESET_ALL}")
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
                print(f"\n{Fore.GREEN}Nova:{Style.RESET_ALL}", response.response)
                
                # Show validated concepts if any
                if response.concepts:
                    print(f"\n{Fore.CYAN}Validated Concepts:{Style.RESET_ALL}")
                    for concept in response.concepts:
                        validation = concept.get('validation', {})
                        supporters = len(validation.get('supported_by', []))
                        contradictors = len(validation.get('contradicted_by', []))
                        print(f"\n- {Fore.YELLOW}{concept['name']}{Style.RESET_ALL} ({concept['type']}, confidence: {validation.get('confidence', 0):.2f})")
                        print(f"  {Fore.CYAN}Description:{Style.RESET_ALL} {concept['description']}")
                        print(f"  {Fore.CYAN}Support:{Style.RESET_ALL} {Fore.GREEN}{supporters}{Style.RESET_ALL} for, {Fore.RED}{contradictors}{Style.RESET_ALL} against")
                        if concept.get('related'):
                            print(f"  {Fore.CYAN}Related:{Style.RESET_ALL} {Fore.YELLOW}{', '.join(concept['related'])}{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
                break
                
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}")
                print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        
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
        print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
