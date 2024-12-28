"""Mobile UI interface for NIA chat system with WhatsApp-style interface."""

import gradio as gr
import logging
import os
import platform
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from nia.ui.handlers import System2Handler, MemoryHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MobileUI:
    def __init__(self):
        """Initialize the mobile UI."""
        logger.info("Initializing mobile UI...")
        
        self.title = "NIA Chat"
        self.description = """
        # NIA Chat Interface
        
        **Nova (Main)**: Synthesized responses and key insights
        **Nova Orchestration**: View agent interactions and task coordination
        """
        
        # Initialize handlers
        logger.info("Initializing handlers...")
        try:
            self.memory = MemoryHandler()
            self.system2 = System2Handler()
        except Exception as e:
            logger.warning(f"Failed to initialize handlers: {e}")
            self.memory = None
            self.system2 = None
        
        # Initialize chat histories
        self.nova_history = []  # Main Nova thread
        self.orchestration_history = []  # Agent dialogue thread
        self.debug_output = []  # Terminal-style debug output
        
        logger.info("Mobile UI initialization complete")

    def create_chat_interface(self) -> gr.Blocks:
        """Create the WhatsApp-style chat interface."""
        # SVG data URLs
        user_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOSIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzI1NjNlYiIgc3Ryb2tlLXdpZHRoPSIyIi8+PGNpcmNsZSBjeD0iMjAiIGN5PSIxNSIgcj0iNiIgZmlsbD0iIzI1NjNlYiIvPjxwYXRoIGQ9Ik04IDM1YzAtOCA2LTEzIDEyLTEzczEyIDUgMTIgMTMiIGZpbGw9IiMyNTYzZWIiLz48L3N2Zz4="
        nova_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOSIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzEwYjk4MSIgc3Ryb2tlLXdpZHRoPSIyIi8+PGNpcmNsZSBjeD0iMjAiIGN5PSIxNSIgcj0iNiIgZmlsbD0iIzEwYjk4MSIvPjxwYXRoIGQ9Ik04IDM1YzAtOCA2LTEzIDEyLTEzczEyIDUgMTIgMTMiIGZpbGw9IiMxMGI5ODEiLz48Y2lyY2xlIGN4PSIxNyIgY3k9IjE0IiByPSIxLjUiIGZpbGw9IndoaXRlIi8+PGNpcmNsZSBjeD0iMjMiIGN5PSIxNCIgcj0iMS41IiBmaWxsPSJ3aGl0ZSIvPjwvc3ZnPg=="
        agents_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOSIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzYzNjZmMSIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0iTTEyIDI4TDIwIDEyTDI4IDI4WiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNjM2NmYxIiBzdHJva2Utd2lkdGg9IjMiLz48L3N2Zz4="
        
        with gr.Blocks(
            title=self.title,
            theme=gr.themes.Default()
        ) as interface:
            gr.Markdown(self.description)
            
            with gr.Tabs() as tabs:
                # Nova's main thread
                with gr.Tab("Nova (Main)", id="nova_main"):
                    nova_chat = gr.Chatbot(
                        value=[],
                        height=400,
                        show_label=False,
                        type="messages",  # Use OpenAI message format
                        elem_id="nova_chat",
                        avatar_images=[
                            user_svg,
                            nova_svg
                        ]
                    )
                    
                    with gr.Row():
                        nova_input = gr.Textbox(
                            show_label=False,
                            placeholder="Message Nova...",
                            container=False
                        )
                        nova_send = gr.Button("Send")
                
                # Nova's orchestration thread
                with gr.Tab("Nova Orchestration", id="nova_orchestration"):
                    orchestration_chat = gr.Chatbot(
                        value=[],
                        height=400,
                        show_label=False,
                        type="messages",
                        elem_id="orchestration_chat",
                        avatar_images=[
                            user_svg,
                            agents_svg
                        ]
                    )
                    
                    # Read-only - no input needed as this shows agent interactions
                    gr.Markdown("*Agent interactions are displayed here*")
                
                # Settings and CLI access
                with gr.Tab("Settings", id="settings"):
                    gr.Markdown("## System Commands")
                    
                    # Command input
                    with gr.Row():
                        cli_input = gr.Textbox(
                            show_label=False,
                            placeholder="Enter command (e.g., status, search <query>, reset, help)",
                            container=False
                        )
                        cli_send = gr.Button("Execute")
                    
                    # Command output
                    cli_output = gr.Markdown(
                        value="*Command output will appear here*\n\n" + 
                              "Available commands:\n" +
                              "- status: Check system status\n" +
                              "- search <query>: Search memories\n" +
                              "- reset: Reset system state\n" +
                              "- help: Show this help message\n" +
                              "- consolidate: Force memory consolidation",
                        elem_id="cli_output"
                    )
            
            # Debug output area
            with gr.Accordion("Debug Output", open=True):
                debug_output = gr.Markdown(
                    value="*Debug information will appear here*",
                    elem_id="debug_output"
                )
                
                # Auto-refresh toggle for debug output
                debug_refresh = gr.Checkbox(
                    label="Auto-refresh debug output",
                    value=True
                )
            
            # Add handlers
            nova_input.submit(
                self.handle_nova_message,
                inputs=[nova_input, nova_chat],
                outputs=[
                    nova_input,  # Clear input
                    nova_chat,   # Update Nova chat
                    orchestration_chat,  # Update orchestration view
                    debug_output  # Update debug output
                ]
            )
            
            nova_send.click(
                self.handle_nova_message,
                inputs=[nova_input, nova_chat],
                outputs=[
                    nova_input,
                    nova_chat,
                    orchestration_chat,
                    debug_output
                ]
            )
            
            # CLI handlers
            cli_input.submit(
                self.handle_cli_command,
                inputs=[cli_input],
                outputs=[cli_input, cli_output]
            )
            
            cli_send.click(
                self.handle_cli_command,
                inputs=[cli_input],
                outputs=[cli_input, cli_output]
            )
            
        return interface

    async def handle_cli_command(
        self,
        command: str
    ) -> Tuple[str, str]:
        """Handle CLI commands."""
        try:
            if not command:
                return "", cli_output.value
            
            command = command.lower().strip()
            output_lines = []
            
            if command == "status":
                if self.system2:
                    status = await self.system2.nova.get_status()
                    output_lines.extend([
                        "## System Status",
                        "",
                        "### Vector Store:",
                        f"- Episodic Layer: {status['vector_store'].get('episodic_count', 0)} memories",
                        f"- Semantic Layer: {status['vector_store'].get('semantic_count', 0)} memories",
                        f"- Last Consolidation: {status['vector_store'].get('last_consolidation', 'Never')}",
                        "",
                        "### Neo4j:",
                        f"- Total Concepts: {status['neo4j'].get('concept_count', 0)}",
                        f"- Relationships: {status['neo4j'].get('relationship_count', 0)}",
                        "",
                        "### Active Agents:",
                        *[f"- {agent}" for agent in status.get('active_agents', [])],
                        "",
                        "### Memory Consolidation:",
                        f"- Next scheduled: {status['vector_store'].get('next_consolidation', 'Unknown')}"
                    ])
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command.startswith("search "):
                query = command[7:].strip()
                if self.system2:
                    memories = await self.system2.nova.search_memories(query)
                    output_lines.extend([
                        f"## Found {len(memories)} related memories:",
                        ""
                    ])
                    for i, memory in enumerate(memories, 1):
                        output_lines.extend([
                            f"{i}. Layer: {memory.get('layer', 'unknown')}",
                            f"   Score: {memory.get('score', 0):.3f}",
                            f"   Type: {memory.get('type', 'unknown')}",
                            f"   Content: {memory.get('content', '')}",
                            ""
                        ])
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command == "reset":
                if self.system2:
                    output_lines.extend([
                        "Resetting system...",
                        "- Clearing episodic memories...",
                        "- Clearing semantic memories...",
                        "- Resetting concept storage...",
                        "- Resetting consolidation timer...",
                        "- Clearing agent states...",
                        "",
                        "Reset complete"
                    ])
                    await self.system2.nova.cleanup()
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command == "consolidate":
                if self.system2:
                    await self.system2.nova._consolidate_memories()
                    status = await self.system2.nova.get_status()
                    output_lines.extend([
                        "Consolidation complete:",
                        f"- Semantic memories: {status['vector_store'].get('semantic_count', 0)}",
                        f"- Concepts stored: {status['neo4j'].get('concept_count', 0)}",
                        f"- Next consolidation: {status['vector_store'].get('next_consolidation', 'Unknown')}"
                    ])
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command == "help":
                output_lines.extend([
                    "## Available commands:",
                    "- exit: Quit the system",
                    "- status: Check detailed system status (memory layers, concepts, agents)",
                    "- search <query>: Search memories across layers with relevance scores",
                    "- reset: Reset all memory stores and system state",
                    "- consolidate: Force memory consolidation",
                    "- help: Show this help message"
                ])
            
            else:
                output_lines.append(f"Unknown command: {command}")
            
            return "", "\n".join(output_lines)
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return "", f"Error: {str(e)}"

    async def handle_nova_message(
        self,
        message: str,
        history: List[Dict[str, str]]
    ) -> Tuple[str, List[Dict[str, str]], List[Dict[str, str]], str]:
        """Handle messages in Nova's main thread."""
        try:
            # Format debug output
            debug_lines = []
            debug_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processing message: {message}")
            
            # Add user message to Nova chat
            history.append({
                "role": "user",
                "content": message
            })
            
            if self.system2:
                # Process through Nova
                response = await self.system2.send_message(
                    message=message,
                    chat_history=history,
                    agent="Nova (Main)"
                )
                
                # Update Nova chat with response
                updated_history = response[0]
                
                # Extract agent whispers and interactions for orchestration view
                agent_interactions = []
                
                # First add thinking message
                agent_interactions.append({
                    "role": "assistant",
                    "content": "Let me think about this...",
                    "metadata": {"title": "🧠 Thinking"}
                })
                
                # Add whispers if available
                if response[1] and response[1].get("whispers"):
                    for whisper in response[1]["whispers"]:
                        # Extract agent type from whisper (e.g., "*Emotion agent whispers: ..." -> "emotion")
                        agent_type = "assistant"
                        if "*" in whisper and "whispers:" in whisper.lower():
                            agent_name = whisper.split("whispers:")[0].strip("*").lower()
                            if "agent" in agent_name:
                                agent_type = agent_name.replace("agent", "").strip()
                        
                        agent_interactions.append({
                            "role": agent_type,
                            "content": whisper,
                            "metadata": {"title": "🤫 Whisper"}
                        })
                
                # Add agent interactions
                if response[1] and response[1].get("agent_interactions"):
                    for interaction in response[1]["agent_interactions"]:
                        # Extract agent type from content
                        agent_type = "assistant"
                        content = interaction['content']
                        
                        if content.startswith('['):
                            agent_name = content.split(']')[0][1:].lower()
                            if "agent" in agent_name:
                                agent_type = agent_name.replace("agent", "").strip()
                                content = content.split(']', 1)[1].strip()
                        
                        agent_interactions.append({
                            "role": agent_type,
                            "content": content,
                            "metadata": {"title": f"💭 {agent_type.capitalize()}"}
                        })
                    
                    # Add interactions to debug output
                    debug_lines.append("\nAgent Interactions:")
                    for interaction in agent_interactions:
                        debug_lines.append(f"{interaction['content']}")
                
                # Update debug output
                debug_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Nova processed message")
                if response[1] and response[1].get("concepts"):
                    debug_lines.append("\nValidated Concepts:")
                    for concept in response[1]["concepts"]:
                        debug_lines.append(f"- {concept['name']} ({concept['type']})")
                        debug_lines.append(f"  Description: {concept['description']}")
                
                # Update orchestration history
                self.orchestration_history.extend(agent_interactions)
                
                return (
                    "",  # Clear input
                    updated_history,  # Update Nova chat
                    self.orchestration_history,  # Update orchestration view with full history
                    "\n".join(debug_lines)  # Update debug output
                )
            else:
                # Fallback if handler not available
                history.append({
                    "role": "assistant",
                    "content": "I'm sorry, but I'm currently unable to process messages. Please try again later."
                })
                debug_lines.append("[ERROR] System2Handler not available")
                
                return (
                    "",
                    history,
                    [],
                    "\n".join(debug_lines)
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            history.append({
                "role": "assistant",
                "content": f"Error: {str(e)}"
            })
            debug_lines.append(f"[ERROR] {str(e)}")
            
            return (
                "",
                history,
                [],
                "\n".join(debug_lines)
            )


    def launch(self, share: bool = True):
        """Launch the mobile UI."""
        try:
            interface = self.create_chat_interface()
            import time
            time.sleep(1)  # Wait for any previous connections to close
            interface.launch(
                server_name="127.0.0.1",
                server_port=7861,  # Use a different port
                share=False,
                inbrowser=True  # Open in browser automatically
            )
        except Exception as e:
            logger.error(f"Error launching UI: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        # Log system information
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
        
        # Initialize and launch UI
        ui = MobileUI()
        ui.launch()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
