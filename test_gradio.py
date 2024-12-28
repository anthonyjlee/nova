"""Test Gradio version and basic functionality."""

import gradio as gr
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Test Gradio setup."""
    try:
        # Print Gradio version
        logger.info(f"Gradio version: {gr.__version__}")
        
        # Create minimal interface
        with gr.Blocks() as demo:
            gr.Markdown("# Test Interface")
            input_text = gr.Textbox(label="Input")
            output_text = gr.Textbox(label="Output")
            
            def echo(text):
                return text
            
            input_text.submit(fn=echo, inputs=input_text, outputs=output_text)
        
        # Launch with debug mode
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            debug=True
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
