"""Mobile UI interface optimized for remote control."""

import json
import gradio as gr
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from nia.ui.handlers import System1Handler, System2Handler, MemoryHandler

class MobileUI:
    """Mobile UI optimized for remote control."""
    
    def __init__(self):
        """Initialize the mobile UI."""
        self.title = "NIA Remote Control"
        self.description = """
        Remote control interface for NIA system.
        Use this interface to control your computer and interact with agents.
        """
        # Initialize handlers
        self.system1 = System1Handler()
        self.system2 = System2Handler()
        self.memory = MemoryHandler()
    
    def create_system1_tab(self) -> gr.Tab:
        """Create the System-1 remote control tab."""
        with gr.Tab("System-1") as tab:
            # API key (collapsible)
            with gr.Accordion("Settings", open=False):
                api_key = gr.Textbox(
                    label="Anthropic API Key",
                    placeholder="Enter your API key",
                    type="password",
                    value=os.getenv("ANTHROPIC_API_KEY", "")
                )
            
                # Screen selection
                screen = gr.Dropdown(
                    choices=["All Displays", "Main Display", "Secondary Display"],
                    label="Control Screen",
                    value="Main Display"
                )
            
            # Quick actions
            with gr.Row():
                type_btn = gr.Button("Type")
                click_btn = gr.Button("Click")
                keys_btn = gr.Button("Keys")
                shot_btn = gr.Button("Screenshot")
            
            # Command input
            command = gr.Textbox(
                label="Command",
                placeholder="Enter command (e.g. {'action': 'type', 'text': 'Hello'})",
                lines=2
            )
            
            # Execute button
            execute_btn = gr.Button("Execute", variant="primary", size="lg")
            
            # Status
            status = gr.Textbox(
                label="Status",
                interactive=False
            )
            
            # Screenshot display
            screenshot = gr.Image(
                label="Screen",
                interactive=False,
                height=300
            )
            
            # Quick action handlers
            def create_type_command():
                return json.dumps({"action": "type", "text": ""})
            
            def create_click_command():
                return json.dumps({"action": "left_click"})
            
            def create_keys_command():
                return json.dumps({"action": "key", "text": ""})
            
            def create_screenshot_command():
                return json.dumps({"action": "screenshot"})
            
            type_btn.click(fn=create_type_command, outputs=command)
            click_btn.click(fn=create_click_command, outputs=command)
            keys_btn.click(fn=create_keys_command, outputs=command)
            shot_btn.click(fn=create_screenshot_command, outputs=command)
            
            # Execute handler
            execute_btn.click(
                fn=self.handle_command,
                inputs=[command, api_key],
                outputs=[status, screenshot]
            )
            
            return tab
    
    def create_agents_tab(self) -> gr.Tab:
        """Create the multi-agent chat tab."""
        with gr.Tab("Agents") as tab:
            # Agent selection
            with gr.Row():
                agent = gr.Dropdown(
                    choices=[
                        "Nova (Group)",
                        "Meta Agent",
                        "Belief Agent", 
                        "Desire Agent",
                        "Emotion Agent",
                        "Reflection Agent"
                    ],
                    label="Chat With",
                    value="Nova (Group)"
                )
            
            # Chat history
            chat_history = gr.Chatbot(
                label="Chat History",
                height=400,
                show_label=False
            )
            
            # Message input
            with gr.Row():
                message = gr.Textbox(
                    placeholder="Type a message...",
                    show_label=False,
                    container=False
                )
                send_btn = gr.Button("Send")
            
            # Add handlers
            send_btn.click(
                fn=self.handle_message,
                inputs=[message, chat_history, agent],
                outputs=[chat_history]
            )
            
            return tab
    
    async def handle_command(
        self,
        command: str,
        api_key: str
    ) -> Tuple[str, Optional[str]]:
        """Handle command execution."""
        try:
            output, status, screenshot = await self.system1.execute_command(command)
            return status, screenshot
        except Exception as e:
            return f"Error: {str(e)}", None
    
    async def handle_message(
        self,
        message: str,
        chat_history: List[Tuple[str, str]],
        agent: str
    ) -> List[Tuple[str, str]]:
        """Handle agent messages."""
        try:
            # Add user message
            chat_history.append((message, None))
            
            # Get agent response
            response = f"[{agent}] Received: {message}"
            chat_history.append((None, response))
            
            return chat_history
        except Exception as e:
            chat_history.append((None, f"Error: {str(e)}"))
            return chat_history
    
    def launch(self, share: bool = True):
        """Launch the mobile UI."""
        with gr.Blocks(
            title=self.title,
            theme=gr.themes.Soft(),
            css="""
                .container { max-width: 600px; margin: auto; }
                .gr-button { min-width: 0; }
                footer { display: none !important; }
            """
        ) as app:
            gr.Markdown(self.description)
            
            with gr.Tabs():
                system1_tab = self.create_system1_tab()
                agents_tab = self.create_agents_tab()
            
        app.launch(share=share)

if __name__ == "__main__":
    ui = MobileUI()
    ui.launch()
