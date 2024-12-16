"""
Interactive CLI for the enhanced memory management system.
"""

import os
import sys
import asyncio
import logging
import json
import aiohttp
from typing import Dict, Optional
from datetime import datetime
import difflib

from nia.memory import MemorySystem
from nia.memory.logging_config import setup_logging

# Configure logging
logger = logging.getLogger(__name__)
agent_logger = setup_logging()

class Colors:
    """ANSI color codes."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

class InteractiveSystem:
    """Interactive CLI system."""
    
    def __init__(self):
        """Initialize system."""
        self.memory_system = MemorySystem()
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_context_length = 2048  # Maximum tokens for LLM context
        self.commands = {
            'exit': 'End session',
            'status': 'Show system state',
            'logs': 'Show memory state and agent responses',
            'reset': 'Reset memory system',
            'clean': 'Clean memory system'
        }
    
    def _get_closest_command(self, input_str: str) -> tuple[Optional[str], float]:
        """Get closest matching command using fuzzy matching."""
        matches = difflib.get_close_matches(input_str.lower(), self.commands.keys(), n=1, cutoff=0.0)
        if matches:
            ratio = difflib.SequenceMatcher(None, input_str.lower(), matches[0]).ratio()
            return matches[0], ratio
        return None, 0.0
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to approximate token limit."""
        # Rough approximation: average English word is 4 characters
        # and typically corresponds to one token
        char_limit = self.max_context_length * 4  # Leave room for system prompt
        if len(text) > char_limit:
            logger.warning(f"Truncating text from {len(text)} to {char_limit} characters")
            # Try to truncate at a word boundary
            truncated = text[:char_limit]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            return truncated
        return text
    
    async def check_llm_server(self) -> bool:
        """Check if LLM server is available."""
        try:
            url = "http://localhost:1234/v1/chat/completions"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json={
                    "model": "local",
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": "test"}
                    ]
                }) as response:
                    return response.status == 200
        except:
            return False
    
    async def get_llm_completion(self, prompt: str) -> str:
        """Get completion from LLM."""
        try:
            if not await self.check_llm_server():
                raise Exception("LLM server is not available")
            
            # Truncate prompt if needed
            prompt = self._truncate_text(prompt)
            
            url = "http://localhost:1234/v1/chat/completions"
            payload = {
                "model": "local",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"LLM server returned status {response.status}")
                    
                    result = await response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        return content if content else "Empty response from LLM"
                    else:
                        raise Exception("Invalid response format from LLM")
                    
        except Exception as e:
            logger.error(f"Error getting LLM completion: {str(e)}")
            return f"Error: {str(e)}"
    
    async def process_interaction(self, content: str) -> str:
        """Process user interaction."""
        try:
            if not await self.check_llm_server():
                return "Error: LLM server is not available"
            
            print(f"\n{Colors.CYAN}Processing interaction...{Colors.ENDC}")
            
            # Process with each agent in sequence
            print(f"{Colors.YELLOW}BeliefAgent: Processing...{Colors.ENDC}")
            belief_output = await self.memory_system.belief_agent.process_interaction(content)
            
            print(f"{Colors.YELLOW}DesireAgent: Processing...{Colors.ENDC}")
            desire_output = await self.memory_system.desire_agent.process_interaction(content)
            
            print(f"{Colors.YELLOW}EmotionAgent: Processing...{Colors.ENDC}")
            emotion_output = await self.memory_system.emotion_agent.process_interaction(content)
            
            print(f"{Colors.YELLOW}ReflectionAgent: Processing...{Colors.ENDC}")
            reflection_output = await self.memory_system.reflection_agent.process_interaction(content)
            
            print(f"{Colors.YELLOW}ResearchAgent: Processing...{Colors.ENDC}")
            research_output = await self.memory_system.research_agent.process_interaction(content)
            
            # Gather agent outputs
            agent_outputs = {
                "BeliefAgent": belief_output,
                "DesireAgent": desire_output,
                "EmotionAgent": emotion_output,
                "ReflectionAgent": reflection_output,
                "ResearchAgent": research_output
            }
            
            print(f"{Colors.YELLOW}MetaAgent: Synthesizing responses...{Colors.ENDC}")
            
            # Process with meta agent
            response = await self.memory_system.meta_agent.process_interaction(content, agent_outputs)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing interaction: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def show_agent_logs(self) -> None:
        """Show detailed agent responses from recent memory."""
        try:
            # Get system state first
            state = await self.memory_system.get_system_state()
            memory_stats = state.get('memory_stats', {})
            
            print(f"\n{Colors.CYAN}=== Memory System State ==={Colors.ENDC}")
            print(f"Short-term memories: {memory_stats.get('short_term_memories', 0)}")
            
            recent = memory_stats.get('recent_interactions', [])
            if recent:
                print("\nRecent interactions:")
                for interaction in recent:
                    print(f"- {interaction.get('input', '')} ({interaction.get('timestamp', '')})")
            else:
                print("\nNo recent interactions found")
            
            # Get detailed logs if available
            memories = await self.memory_system.memory_store.get_recent_memories(limit=1)
            if not memories:
                print(f"\n{Colors.YELLOW}No previous interactions to show detailed logs for.{Colors.ENDC}\n")
                return

            latest_memory = memories[0]
            if not isinstance(latest_memory.get('content'), dict):
                print(f"\n{Colors.YELLOW}No detailed logs available for the last interaction.{Colors.ENDC}\n")
                return

            print(f"\n{Colors.CYAN}=== Detailed Agent Responses ==={Colors.ENDC}")
            
            responses = latest_memory['content'].get('responses', {})
            if not responses:
                print(f"\n{Colors.YELLOW}No agent responses available for the last interaction.{Colors.ENDC}\n")
                return

            for agent_name, response in responses.items():
                if response and isinstance(response, str) and not response.startswith("Error"):
                    print(f"\n{Colors.YELLOW}{agent_name}:{Colors.ENDC}")
                    print(response)
                elif response and isinstance(response, dict):
                    print(f"\n{Colors.YELLOW}{agent_name}:{Colors.ENDC}")
                    print(json.dumps(response, indent=2))

            synthesis = latest_memory['content'].get('synthesis')
            if synthesis and isinstance(synthesis, str) and not synthesis.startswith("Error"):
                print(f"\n{Colors.CYAN}=== Final Synthesis ==={Colors.ENDC}")
                print(f"{Colors.GREEN}{synthesis}{Colors.ENDC}")

            print(f"\n{Colors.CYAN}=== End of Logs ==={Colors.ENDC}\n")

        except Exception as e:
            print(f"\n{Colors.RED}Error showing logs: {str(e)}{Colors.ENDC}\n")
    
    def inject_llm_completion(self):
        """Inject LLM completion method into agents."""
        self.memory_system.meta_agent.get_completion = self.get_llm_completion
        self.memory_system.belief_agent.get_completion = self.get_llm_completion
        self.memory_system.desire_agent.get_completion = self.get_llm_completion
        self.memory_system.emotion_agent.get_completion = self.get_llm_completion
        self.memory_system.reflection_agent.get_completion = self.get_llm_completion
        self.memory_system.research_agent.get_completion = self.get_llm_completion
    
    async def run(self):
        """Run interactive system."""
        try:
            print(f"\n{Colors.HEADER}=== Memory System ==={Colors.ENDC}\n")
            
            # Initialize vector store with recreation to ensure correct dimensions
            print(f"{Colors.CYAN}Initializing vector store...{Colors.ENDC}")
            await self.memory_system.initialize(reset=False, recreate_vectors=True)
            print(f"{Colors.GREEN}Vector store initialized{Colors.ENDC}")
            
            # Inject LLM completion method
            self.inject_llm_completion()
            
            # Check LLM server
            if not await self.check_llm_server():
                print(f"{Colors.RED}Warning: LLM server is not available{Colors.ENDC}\n")
            else:
                print(f"{Colors.GREEN}LLM server is available{Colors.ENDC}\n")
            
            # Print welcome
            print(f"{Colors.GREEN}System: Ready for interaction")
            print(f"\nCommands:")
            for cmd, desc in self.commands.items():
                print(f"'{cmd}' - {desc}")
            print(f"{Colors.ENDC}\n")
            
            # Main loop
            while True:
                try:
                    user_input = input(f"{Colors.BLUE}You: {Colors.ENDC}").strip()
                    
                    # Check for command match
                    cmd, ratio = self._get_closest_command(user_input)
                    if cmd and ratio > 0.6:  # Only use command if good match
                        if cmd == 'exit':
                            print(f"\n{Colors.GREEN}System: Ending session...{Colors.ENDC}")
                            break
                            
                        elif cmd == 'status':
                            state = await self.memory_system.get_system_state()
                            print(f"\n{Colors.CYAN}System State:")
                            print(json.dumps(state, indent=2))
                            print(f"{Colors.ENDC}")
                            continue
                            
                        elif cmd == 'logs':
                            await self.show_agent_logs()
                            continue
                            
                        elif cmd == 'reset':
                            print(f"\n{Colors.YELLOW}Resetting memory system...{Colors.ENDC}")
                            await self.memory_system.initialize(reset=True, recreate_vectors=True)
                            print(f"{Colors.GREEN}Memory system reset complete{Colors.ENDC}\n")
                            continue
                            
                        elif cmd == 'clean':
                            print(f"\n{Colors.YELLOW}Cleaning memory system...{Colors.ENDC}")
                            await self.memory_system.cleanup()
                            print(f"{Colors.GREEN}Memory system cleanup complete{Colors.ENDC}\n")
                            continue
                    
                    if not user_input:
                        continue
                    
                    if not await self.check_llm_server():
                        print(f"\n{Colors.RED}Error: LLM server not available{Colors.ENDC}\n")
                        continue
                    
                    response = await self.process_interaction(user_input)
                    if isinstance(response, str) and not response.startswith("Error"):
                        print(f"\n{Colors.GREEN}Nova: {response}{Colors.ENDC}\n")
                    else:
                        print(f"\n{Colors.RED}Error: {response}{Colors.ENDC}\n")
                    
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}Interrupted{Colors.ENDC}\n")
                    continue
                except Exception as e:
                    print(f"\n{Colors.RED}Error: {str(e)}{Colors.ENDC}\n")
                    continue
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            raise

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    print(f"{Colors.YELLOW}Note: Please ensure LM Studio is running{Colors.ENDC}\n")
    
    try:
        system = InteractiveSystem()
        asyncio.run(system.run())
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}System shutdown complete{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {str(e)}{Colors.ENDC}")

if __name__ == "__main__":
    main()
