"""Minimal mobile UI test following the original architecture."""

import gradio as gr
import logging
import platform
from typing import List, Tuple

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MinimalHandler:
    """Basic message handler."""
    def __init__(self):
        logger.info("Initializing MinimalHandler")

    async def send_message(self, message: str, chat_history: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Handle chat message."""
        logger.info(f"Handling message: {message}")
        chat_history.append((message, f"You said: {message}"))
        return chat_history

class MinimalUI:
    def __init__(self):
        """Initialize the minimal UI."""
        logger.info("Initializing minimal UI...")
        self.title = "Test Interface"
        self.description = "Basic chat interface test"
        self.handler = MinimalHandler()
        logger.info("Initialization complete")

    def create_chat_interface(self) -> gr.Blocks:
        """Create the chat interface."""
        with gr.Blocks(title=self.title) as interface:
            gr.Markdown(self.description)
            
            chatbot = gr.Chatbot(
                value=[(None, "Hello! How can I help you today?")],
                height=400
            )
            
            with gr.Row():
                with gr.Column(scale=8):
                    msg = gr.Textbox(
                        show_label=False,
                        placeholder="Type a message...",
                        container=False
                    )
                with gr.Column(scale=1, min_width=50):
                    send = gr.Button("Send")

            async def handle_message(message: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
                """Handle incoming messages."""
                if not message:
                    return "", history
                    
                try:
                    # Get response from handler
                    updated_history = await self.handler.send_message(
                        message=message,
                        chat_history=history
                    )
                    return "", updated_history
                    
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    history.append((message, f"Error: {str(e)}"))
                    return "", history

            # Add message handlers
            msg.submit(
                handle_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            send.click(
                handle_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            
        return interface

    def launch(self, share: bool = False):
        """Launch the minimal UI."""
        try:
            interface = self.create_chat_interface()
            interface.queue()
            interface.launch(
                server_name="127.0.0.1",
                server_port=7860,
                share=share
            )
        except Exception as e:
            logger.error(f"Error launching UI: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        # Log system information
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        
        # Initialize and launch UI
        ui = MinimalUI()
        ui.launch()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
