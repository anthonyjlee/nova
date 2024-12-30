"""UI component definitions for NIA chat interface."""

import gradio as gr
from typing import Dict, Any, List, Optional

class UIComponents:
    """UI component definitions and factory methods."""
    
    @staticmethod
    def create_chat(
        value: Optional[List] = None,
        height: int = 400,
        avatar_images: Optional[List[str]] = None
    ) -> gr.Chatbot:
        """Create a chat component."""
        return gr.Chatbot(
            value=value if value is not None else [],
            height=height,
            type="messages",  # Use messages format
            avatar_images=avatar_images,
            show_label=False,
            layout="bubble",  # Use bubble layout for better distinction
            render=True  # Enable markdown rendering
        )
    
    @staticmethod
    def create_input(
        placeholder: str = "Enter message...",
        container: bool = False
    ) -> gr.Textbox:
        """Create an input component."""
        return gr.Textbox(
            show_label=False,
            placeholder=placeholder,
            container=container
        )
    
    @staticmethod
    def create_button(
        text: str = "Send"
    ) -> gr.Button:
        """Create a button component."""
        return gr.Button(text)
    
    @staticmethod
    def create_highlighted_text(
        value: Optional[List] = None,
        label: str = "",
        show_label: bool = False
    ) -> gr.HighlightedText:
        """Create a highlighted text component."""
        return gr.HighlightedText(
            value=value if value is not None else [],
            label=label,
            show_label=show_label
        )
    
    @staticmethod
    def create_plot(
        label: str = ""
    ) -> gr.Plot:
        """Create a plot component."""
        return gr.Plot(label=label)
    
    @staticmethod
    def create_gallery(
        label: str = "",
        columns: int = 2,
        height: int = 200
    ) -> gr.Gallery:
        """Create a gallery component."""
        return gr.Gallery(
            label=label,
            columns=columns,
            height=height
        )
    
    @staticmethod
    def create_markdown(
        value: str = "",
        elem_id: Optional[str] = None
    ) -> gr.Markdown:
        """Create a markdown component."""
        return gr.Markdown(
            value=value,
            elem_id=elem_id
        )
    
    @staticmethod
    def create_json(
        value: Optional[Dict] = None,
        label: str = ""
    ) -> gr.JSON:
        """Create a JSON component."""
        return gr.JSON(
            value=value if value is not None else {},
            label=label
        )
    
    @staticmethod
    def create_dropdown(
        choices: List[str],
        value: Optional[str] = None,
        label: str = ""
    ) -> gr.Dropdown:
        """Create a dropdown component."""
        return gr.Dropdown(
            choices=choices,
            value=value,
            label=label
        )
    
    @staticmethod
    def create_checkbox(
        label: str = "",
        value: bool = True
    ) -> gr.Checkbox:
        """Create a checkbox component."""
        return gr.Checkbox(
            label=label,
            value=value
        )
    
    @staticmethod
    def create_state(value: Any = None) -> gr.State:
        """Create a state component.
        
        Args:
            value: Initial state value
            
        Returns:
            State component
        """
        return gr.State(value=value)
    
    @staticmethod
    def create_html(
        value: str = "",
        elem_id: Optional[str] = None
    ) -> gr.HTML:
        """Create an HTML component."""
        return gr.HTML(
            value=value,
            elem_id=elem_id
        )

class TabComponents:
    """Tab-specific component collections."""
    
    @staticmethod
    def create_main_tab(
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create components for main Nova tab."""
        nova_chat = UIComponents.create_chat(
            value=state.get('nova_history', [])
        )
        
        with gr.Row():
            nova_input = UIComponents.create_input(
                placeholder="Message Nova..."
            )
            nova_send = UIComponents.create_button("Send")
        
        return {
            'chat': nova_chat,
            'input': nova_input,
            'send': nova_send
        }
    
    @staticmethod
    def create_orchestration_tab(
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create components for orchestration tab."""
        with gr.Row():
            # Main chat area
            with gr.Column(scale=2):
                # Create chat with custom styling for agent messages
                orchestration_chat = UIComponents.create_chat(
                    value=state.get('orchestration_history', []),
                    height=600,  # Increased height for better visibility
                    avatar_images={  # Add agent avatars
                        "Meta Agent": "src/nia/ui/assets/nova.svg",
                        "Belief Agent": "src/nia/ui/assets/agents.svg",
                        "Desire Agent": "src/nia/ui/assets/agents.svg",
                        "Emotion Agent": "src/nia/ui/assets/agents.svg",
                        "Reflection Agent": "src/nia/ui/assets/agents.svg",
                        "Research Agent": "src/nia/ui/assets/agents.svg",
                        "Task Agent": "src/nia/ui/assets/agents.svg"
                    }
                )
            
            # Side panel
            with gr.Column(scale=1):
                with gr.Accordion("Active Agents", open=True):
                    active_agents = UIComponents.create_highlighted_text(
                        label="Currently Active"
                    )
                
                with gr.Accordion("Key Concepts", open=True):
                    key_concepts = UIComponents.create_highlighted_text(
                        label="Identified Concepts"
                    )
                
                with gr.Accordion("Concept Gallery", open=True):
                    concept_gallery = UIComponents.create_gallery(
                        label="Visual Concepts"
                    )
        
        return {
            'chat': orchestration_chat,
            'agents': active_agents,
            'concepts': key_concepts,
            'gallery': concept_gallery
        }
    
    @staticmethod
    def create_graph_tab() -> Dict[str, Any]:
        """Create components for graph tab."""
        with gr.Row():
            # Graph visualization
            with gr.Column(scale=3):
                graph_view = UIComponents.create_html(
                    elem_id="cy"
                )
            
            # Controls
            with gr.Column(scale=1):
                with gr.Accordion("Cypher Query", open=True):
                    cypher_input = UIComponents.create_input(
                        placeholder="MATCH (n) RETURN n LIMIT 10"
                    )
                    run_query = UIComponents.create_button("Run Query")
                
                with gr.Accordion("Graph Controls", open=True):
                    layout_select = UIComponents.create_dropdown(
                        choices=["cose", "circle", "grid", "random"],
                        value="cose",
                        label="Layout"
                    )
                    refresh_graph = UIComponents.create_button("Refresh Graph")
                
                with gr.Accordion("Node Info", open=True):
                    node_info = UIComponents.create_json(
                        label="Selected Node Details"
                    )
        
        return {
            'view': graph_view,
            'input': cypher_input,
            'run': run_query,
            'layout': layout_select,
            'refresh': refresh_graph,
            'info': node_info
        }
    
    @staticmethod
    def create_settings_tab() -> Dict[str, Any]:
        """Create components for settings tab."""
        gr.Markdown("## System Commands")
        
        with gr.Row():
            cli_input = UIComponents.create_input(
                placeholder="Enter command (e.g., status, search <query>, reset, help)"
            )
            cli_send = UIComponents.create_button("Execute")
        
        cli_output = UIComponents.create_markdown(
            value="*Command output will appear here*\n\n" + 
                  "Available commands:\n" +
                  "- status: Check system status\n" +
                  "- search <query>: Search memories\n" +
                  "- reset: Reset system state\n" +
                  "- help: Show this help message\n" +
                  "- consolidate: Force memory consolidation",
            elem_id="cli_output"
        )
        
        return {
            'input': cli_input,
            'send': cli_send,
            'output': cli_output
        }
    
    @staticmethod
    def create_debug_section() -> Dict[str, Any]:
        """Create debug output section."""
        with gr.Accordion("Debug Output", open=True):
            debug_output = UIComponents.create_markdown(
                value="*Debug information will appear here*",
                elem_id="debug_output"
            )
            
            debug_refresh = UIComponents.create_checkbox(
                label="Auto-refresh debug output",
                value=True
            )
        
        return {
            'output': debug_output,
            'refresh': debug_refresh
        }
