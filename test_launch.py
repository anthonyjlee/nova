"""Test minimal Gradio interface launch."""

import gradio as gr
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_interface():
    """Create minimal test interface."""
    with gr.Blocks() as interface:
        gr.Markdown("# Test Interface")
        input_text = gr.Textbox(label="Input")
        output_text = gr.Textbox(label="Output")
        
        def echo(text):
            return text
        
        input_text.submit(fn=echo, inputs=input_text, outputs=output_text)
    return interface

def main():
    """Launch test interface."""
    try:
        interface = create_interface()
        logger.info("Interface created")
        
        interface.queue()
        logger.info("Interface queued")
        
        result = interface.launch(
            server_name="127.0.0.1",
            server_port=7860,  # Try specific port
            share=False,
            prevent_thread_lock=True
        )
        logger.info(f"Launch result: {result}")
        
        if not result:
            raise RuntimeError("Interface launch returned None")
        
        logger.info("Interface launched successfully")
        return result
    except Exception as e:
        logger.error(f"Launch error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
