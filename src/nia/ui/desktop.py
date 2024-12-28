"""Desktop UI interface for NIA chat system."""

import gradio as gr
from typing import Dict, List, Tuple, Any
from datetime import datetime

from .handlers import System2Handler, MemoryHandler

class DesktopUI:
    """Desktop UI with chat interface."""
    
    def __init__(self):
        """Initialize the desktop UI."""
        self.title = "NIA Chat"
        self.description = """
        Chat interface for NIA system.
        """
        # Initialize handlers
        self.system2 = System2Handler()
        self.memory = MemoryHandler()
        
        # Initialize chat state
        self.active_chat = "Nova (Main)"
        self.chat_histories = {
            "Nova (Main)": [{"role": "assistant", "content": "Hello! How can I help you today?"}]
        }
    
    def create_chat_interface(self) -> gr.Blocks:
        """Create the chat interface."""
        with gr.Blocks(title=self.title) as interface:
            gr.Markdown(self.description)
            # Chat interface
            with gr.Row():
                with gr.Column():
                    # Chat display
                    chatbot = gr.Chatbot(
                        value=[{"role": "assistant", "content": "Hello! How can I help you today?"}],
                        height=400,
                        show_label=False
                    )
                    
                    # Message input
                    with gr.Row():
                        msg = gr.Textbox(
                            show_label=False,
                            placeholder="Type a message...",
                            container=False
                        )
                        send = gr.Button("Send")
            
            # Add message handlers
            msg.submit(
                self.handle_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            send.click(
                self.handle_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            
            return interface
    
    async def handle_message(
        self,
        message: str,
        history: List[Dict[str, str]]
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Handle incoming messages."""
        try:
            # Add user message
            history.append({"role": "user", "content": message})
            
            # Get response from handler
            if self.system2:
                updated_history, _, _ = await self.system2.send_message(
                    message=message,
                    chat_history=history,
                    agent=self.active_chat
                )
                return "", updated_history
            else:
                # Fallback response if handler not available
                history.append({
                    "role": "assistant",
                    "content": "I'm sorry, but I'm currently unable to process messages. Please try again later."
                })
                return "", history
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            history.append({
                "role": "assistant",
                "content": f"Error: {str(e)}"
            })
            return "", history
    
    def launch(self, share: bool = False):
        """Launch the desktop UI."""
        try:
            interface = self.create_chat_interface()
            interface.launch(
                server_name="127.0.0.1",
                server_port=7860,
                share=share
            )
        except Exception as e:
            logger.error(f"Error launching UI: {str(e)}")
            raise

if __name__ == "__main__":
    ui = DesktopUI()
    ui.launch()
