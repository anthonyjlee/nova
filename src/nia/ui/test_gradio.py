"""Test Gradio functionality."""

import gradio as gr
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting test Gradio app...")
        logger.info(f"Gradio version: {gr.__version__}")
        
        with gr.Blocks(analytics_enabled=False) as app:
            gr.Markdown("# Test App")
            gr.Textbox(label="Test Input")
        
        logger.info("Launching app...")
        app.launch(
            server_name="127.0.0.1",  # Use localhost
            server_port=8080,  # Try different port
            quiet=False  # Show all Gradio logs
        )
    except Exception as e:
        logger.error(f"Error running Gradio app: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
