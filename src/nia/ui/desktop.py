"""Desktop UI interface with advanced features."""

import gradio as gr
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .handlers import System1Handler, System2Handler, MemoryHandler

class DesktopUI:
    """Desktop UI with advanced features."""
    
    def __init__(self):
        """Initialize the desktop UI."""
        self.title = "NIA Desktop Dashboard"
        self.description = """
        Advanced dashboard for NIA system with full feature set.
        """
        # Initialize handlers
        self.system1 = System1Handler()
        self.system2 = System2Handler()
        self.memory = MemoryHandler()
        
        # Initialize state
        self.command_history = []
        self.query_templates = {
            "Recent Concepts": "MATCH (c:Concept) WHERE c.created > datetime() - duration('P7D') RETURN c",
            "Active Agents": "MATCH (a:Agent) WHERE a.status = 'active' RETURN a",
            "Memory Stats": "MATCH (n) RETURN labels(n) as type, count(*) as count"
        }
    
    def create_system1_tab(self) -> gr.Tab:
        """Create the real-time system tab."""
        with gr.Tab("System-1 (Real-time)") as tab:
            with gr.Row():
                # Left sidebar
                with gr.Column(scale=1):
                    # API key management
                    with gr.Accordion("API Settings", open=False):
                        api_key = gr.Textbox(
                            label="Anthropic API Key",
                            placeholder="Enter your API key",
                            type="password",
                            value=os.getenv("ANTHROPIC_API_KEY", "")
                        )
                    
                    # Command templates
                    with gr.Accordion("Command Templates", open=True):
                        templates = gr.Dropdown(
                            choices=[
                                "Open Application",
                                "Browse Web",
                                "File Operation",
                                "System Command"
                            ],
                            label="Templates"
                        )
                    
                    # Command history
                    with gr.Accordion("Command History", open=True):
                        history = gr.Dataframe(
                            headers=["Time", "Command", "Status"],
                            datatype=["str", "str", "str"],
                            label="History"
                        )
                
                # Main content
                with gr.Column(scale=2):
                    # Command interface
                    command = gr.Textbox(
                        label="Command",
                        placeholder="Enter command here...",
                        lines=3
                    )
                    
                    with gr.Row():
                        # Action buttons
                        execute_btn = gr.Button("Execute")
                        clear_btn = gr.Button("Clear")
                        save_btn = gr.Button("Save to Templates")
                    
                    # Output display
                    output = gr.Textbox(
                        label="Output",
                        lines=10,
                        interactive=False
                    )
                    status = gr.Textbox(
                        label="Status",
                        interactive=False
                    )
                
                # Right sidebar
                with gr.Column(scale=1):
                    # Screenshot display
                    screenshot = gr.Image(
                        label="Screen",
                        interactive=False
                    )
                    
                    # Display settings
                    with gr.Accordion("Display Settings", open=False):
                        display = gr.Dropdown(
                            choices=["All Displays", "Main Display", "Secondary Display"],
                            label="Display Selection",
                            value="All Displays"
                        )
                        resolution = gr.Dropdown(
                            choices=["Original", "720p", "1080p", "4K"],
                            label="Resolution",
                            value="1080p"
                        )
            
            # Add handlers
            execute_btn.click(
                fn=self.handle_command,
                inputs=[command, api_key, display, resolution],
                outputs=[output, status, screenshot, history]
            )
            
            return tab
    
    def create_system2_tab(self) -> gr.Tab:
        """Create the Nova/Agents chat tab."""
        with gr.Tab("System-2 (Nova)") as tab:
            with gr.Row():
                # Left sidebar - Chat list
                with gr.Column(scale=1):
                    # Search chats
                    chat_search = gr.Textbox(
                        label="Search Chats",
                        placeholder="Search..."
                    )
                    
                    # Chat list
                    chats = gr.Dataframe(
                        headers=["Chat", "Type", "Last Active"],
                        datatype=["str", "str", "str"],
                        label="Chats",
                        interactive=False,
                        value=[
                            ["Nova", "Group", datetime.now().strftime("%Y-%m-%d %H:%M")],
                            ["Meta Agent", "Agent", "-"],
                            ["Belief Agent", "Agent", "-"],
                            ["Desire Agent", "Agent", "-"],
                            ["Emotion Agent", "Agent", "-"],
                            ["Reflection Agent", "Agent", "-"],
                            ["Research Agent", "Agent", "-"]
                        ]
                    )
                    
                    # Add chat button
                    add_chat_btn = gr.Button("New Chat")
                
                # Main content - Chat interface
                with gr.Column(scale=2):
                    # Chat header
                    with gr.Row():
                        chat_title = gr.Textbox(
                            label="Chat",
                            value="Nova",
                            interactive=False
                        )
                        chat_menu = gr.Dropdown(
                            choices=["Pin Chat", "Mute", "Clear History", "Leave"],
                            label=""
                        )
                    
                    # Chat display
                    chat_history = gr.Chatbot(
                        label="Chat History",
                        height=400
                    )
                    
                    # Message input
                    with gr.Row():
                        message = gr.Textbox(
                            label="Message",
                            placeholder="Type your message here...",
                            lines=2
                        )
                        send_btn = gr.Button("Send")
                        attach_btn = gr.Button("📎")
                
                # Right sidebar - Info panel
                with gr.Column(scale=1):
                    # Session info
                    with gr.Accordion("Session Info", open=True):
                        session_info = gr.JSON(
                            label="Info",
                            value={
                                "Active Agents": ["Meta", "Belief", "Desire"],
                                "Memory Status": "Connected",
                                "Last Update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        )
                    
                    # Debug panel
                    with gr.Accordion("Debug", open=True):
                        debug_info = gr.Textbox(
                            label="Debug Info",
                            interactive=False,
                            lines=10
                        )
                    
                    # Agent states
                    with gr.Accordion("Agent States", open=True):
                        agent_states = gr.JSON(
                            label="States",
                            value={
                                "Meta": "Active",
                                "Belief": "Processing",
                                "Desire": "Idle"
                            }
                        )
            
            # Add handlers
            send_btn.click(
                fn=self.handle_message,
                inputs=[message, chat_history],
                outputs=[chat_history, session_info, debug_info, agent_states]
            )
            
            chats.select(
                fn=self.handle_chat_selection,
                outputs=[chat_history, session_info, debug_info, chat_title]
            )
            
            return tab
    
    def create_memory_tab(self) -> gr.Tab:
        """Create the memory system tab."""
        with gr.Tab("Memory System") as tab:
            with gr.Row():
                # Left sidebar - Query tools
                with gr.Column(scale=1):
                    # Query input
                    query = gr.Textbox(
                        label="Neo4j Query",
                        placeholder="Enter Cypher query...",
                        lines=3
                    )
                    
                    # Query templates
                    templates = gr.Dropdown(
                        label="Query Templates",
                        choices=list(self.query_templates.keys())
                    )
                    
                    # Quick filters
                    filters = gr.Dropdown(
                        label="Quick Filters",
                        choices=[
                            "Recent Concepts",
                            "Consolidated Memories",
                            "Active Relationships",
                            "System State"
                        ]
                    )
                    
                    # Execute button
                    query_btn = gr.Button("Execute Query")
                
                # Main content - Visualization
                with gr.Column(scale=2):
                    # Visualization controls
                    with gr.Row():
                        viz_type = gr.Dropdown(
                            choices=["Graph", "Tree", "Force", "Circle"],
                            label="Visualization Type",
                            value="Graph"
                        )
                        viz_settings = gr.Button("⚙️")
                    
                    # Graph display
                    graph = gr.Plot(label="Memory Graph")
                    
                    # Legend
                    with gr.Accordion("Legend", open=False):
                        legend = gr.Markdown("""
                        - 🔵 Concept
                        - 🟢 Memory
                        - 🔴 Agent
                        - 🟡 State
                        """)
                
                # Right sidebar - Details
                with gr.Column(scale=1):
                    # Query results
                    results = gr.JSON(
                        label="Query Results"
                    )
                    
                    # Memory stats
                    stats = gr.JSON(
                        label="Memory Statistics",
                        value={
                            "Total Concepts": 0,
                            "Total Relationships": 0,
                            "Consolidated Memories": 0,
                            "Last Consolidation": "-"
                        }
                    )
            
            # Add handlers
            query_btn.click(
                fn=self.handle_query,
                inputs=[query, viz_type],
                outputs=[graph, results, stats]
            )
            
            templates.select(
                fn=self.handle_template,
                outputs=[query]
            )
            
            filters.select(
                fn=self.handle_filter,
                outputs=[graph, results, stats]
            )
            
            return tab
    
    def create_settings_tab(self) -> gr.Tab:
        """Create the settings tab."""
        with gr.Tab("Settings") as tab:
            with gr.Row():
                # Left column - UI Settings
                with gr.Column():
                    with gr.Accordion("UI Settings", open=True):
                        # Theme
                        theme = gr.Dropdown(
                            choices=["Light", "Dark", "System"],
                            label="Theme",
                            value="System"
                        )
                        
                        # Layout
                        layout = gr.Dropdown(
                            choices=["Default", "Compact", "Comfortable"],
                            label="Layout",
                            value="Default"
                        )
                        
                        # Font settings
                        font_size = gr.Slider(
                            minimum=12,
                            maximum=24,
                            value=16,
                            label="Font Size"
                        )
                
                # Middle column - System Settings
                with gr.Column():
                    with gr.Accordion("System Settings", open=True):
                        # Neo4j connection
                        neo4j_uri = gr.Textbox(
                            label="Neo4j URI",
                            value="bolt://localhost:7687"
                        )
                        neo4j_user = gr.Textbox(
                            label="Neo4j User",
                            value="neo4j"
                        )
                        neo4j_password = gr.Textbox(
                            label="Neo4j Password",
                            type="password"
                        )
                        
                        # API settings
                        anthropic_key = gr.Textbox(
                            label="Anthropic API Key",
                            type="password",
                            value=os.getenv("ANTHROPIC_API_KEY", "")
                        )
                
                # Right column - Advanced Settings
                with gr.Column():
                    with gr.Accordion("Advanced Settings", open=True):
                        # Logging
                        log_level = gr.Dropdown(
                            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                            label="Log Level",
                            value="INFO"
                        )
                        
                        # Performance
                        cache_size = gr.Slider(
                            minimum=100,
                            maximum=1000,
                            value=500,
                            label="Cache Size (MB)"
                        )
                        
                        # Debug mode
                        debug_mode = gr.Checkbox(
                            label="Debug Mode",
                            value=False
                        )
            
            # Add save button
            save_btn = gr.Button("Save Settings")
            
            return tab
    
    async def handle_command(
        self,
        command: str,
        api_key: str,
        display: str,
        resolution: str,
        screenshot: Optional[str] = None
    ) -> Tuple[str, str, Optional[str], List]:
        """Handle command execution in System-1."""
        try:
            # Update API key if changed
            if api_key != self.system1.api_key:
                self.system1.update_api_key(api_key)
            
            # Execute command
            output, status, new_screenshot = await self.system1.execute_command(
                command,
                screenshot
            )
            
            # Update command history
            self.command_history.append([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                command,
                status
            ])
            
            return output, status, new_screenshot, self.command_history
        except Exception as e:
            return str(e), "Error", None, self.command_history
    
    async def handle_message(
        self,
        message: str,
        chat_history: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], Dict, str, Dict]:
        """Handle message sending in System-2."""
        try:
            # Send message
            history, info, debug = await self.system2.send_message(message, chat_history)
            
            # Update agent states
            states = {
                "Meta": "Active",
                "Belief": "Processing",
                "Desire": "Idle"
            }
            
            return history, info, debug, states
        except Exception as e:
            return chat_history, {}, str(e), {}
    
    def handle_template(self, template: str) -> str:
        """Handle query template selection."""
        return self.query_templates.get(template, "")
    
    async def handle_query(
        self,
        query: str,
        viz_type: str
    ) -> Tuple[Any, Dict, Dict]:
        """Handle memory query execution."""
        try:
            # Execute query
            graph, results, stats = await self.memory.execute_query(query)
            
            # Update visualization based on type
            if viz_type != "Graph":
                # TODO: Implement different visualization types
                pass
            
            return graph, results, stats
        except Exception as e:
            return None, {"error": str(e)}, {}
    
    def launch(self):
        """Launch the desktop UI."""
        with gr.Blocks(
            title=self.title,
            theme=gr.themes.Default()
        ) as app:
            gr.Markdown(self.description)
            
            with gr.Tabs():
                system1_tab = self.create_system1_tab()
                system2_tab = self.create_system2_tab()
                memory_tab = self.create_memory_tab()
                settings_tab = self.create_settings_tab()
            
        app.launch()

if __name__ == "__main__":
    ui = DesktopUI()
    ui.launch()
