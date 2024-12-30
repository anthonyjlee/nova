"""Test minimal Gradio interface."""

import gradio as gr

def greet(name):
    return f"Hello {name}!"

with gr.Blocks() as demo:
    name = gr.Textbox(label="Name")
    output = gr.Textbox(label="Output")
    greet_btn = gr.Button("Greet")
    greet_btn.click(fn=greet, inputs=name, outputs=output)

if __name__ == "__main__":
    demo.launch(server_port=8080, prevent_thread_lock=True)
